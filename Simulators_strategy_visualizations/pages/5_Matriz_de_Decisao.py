import streamlit as st

st.set_page_config(layout="wide", page_title="Matriz de Decisão")

st.title("Matriz de Decisão: Qual Banco Escolher?")

st.markdown("""
Esta matriz resume as visualizações e cenários que exploramos. A escolha da tecnologia de banco de dados não é sobre "qual é a melhor", mas sim "qual é a mais adequada para o problema específico e os trade-offs que estamos dispostos a aceitar".
""")

st.table(
    [
        {
            "Tecnologia": "Aurora PostgreSQL",
            "Estrutura Visual (Metáfora)": "Fila Única (Lock Pessimista)",
            "Quando Usar (Motivação)": "Bancos tradicionais, baixo/médio TPS por conta. Migração 'as-is' de legado.",
            "Garantias e 'Custo'": "**Garantia:** ACID completo, SQL padrão. **Custo:** Sofre com Hot Partitions (a fila trava o sistema)."
        },
        {
            "Tecnologia": "DynamoDB (Padrão)",
            "Estrutura Visual (Metáfora)": "Corrida com Versão (Lock Otimista)",
            "Quando Usar (Motivação)": "Alta escala, varejo, Pix, microsserviços na AWS. Custo x Benefício excelente.",
            "Garantias e 'Custo'": "**Garantia:** Alta disponibilidade. **Custo:** Exige controle de retry na aplicação para evitar Race Conditions."
        },
        {
            "Tecnologia": "DynamoDB + Sharding",
            "Estrutura Visual (Metáfora)": "Múltiplos Cofres (Scatter-Gather)",
            "Quando Usar (Motivação)": "Contas 'Baleia' (Ex: Conta concentradora do iFood ou Mercado Livre).",
            "Garantias e 'Custo'": "**Garantia:** Escalabilidade de escrita 'infinita'. **Custo:** Leitura mais complexa/cara (tem que somar os cofres)."
        },
        {
            "Tecnologia": "CockroachDB",
            "Estrutura Visual (Metáfora)": "Votação (Raft Consensus)",
            "Quando Usar (Motivação)": "Banco Global, Multi-Região, necessidade de Strong Consistency sem perder o SQL.",
            "Garantias e 'Custo'": "**Garantia:** Sobrevive à queda de um Data Center. Garante que o saldo nunca fure. **Custo:** Latência de escrita maior devido à comunicação entre nós."
        },
        {
            "Tecnologia": "ScyllaDB / Cassandra",
            "Estrutura Visual (Metáfora)": "Pista Expressa (LSM-Tree) + Particionamento",
            "Quando Usar (Motivação)": "Latência ultrabaixa e throughput massivo. Ótimo para Ledger de alta frequência.",
            "Garantias e 'Custo'": "**Garantia:** Performance bruta por nó. **Custo:** Consistência eventual por padrão, modelo de dados rígido e complexidade operacional."
        }
    ]
)

st.header("Resumo da 'Solução Intuitiva' para Saldos e Bloqueios")
st.markdown("""
A intuição final para modelar sistemas de saldo robustos é pensar em **"Pockets" (Bolsos)** e **operações atômicas**.

#### Visualizar os "Pockets" (Bolsos)
Em vez de um único número `Saldo: 100`, a visualização correta (e a implementação no banco) é uma estrutura com múltiplos bolsos:
- `saldo_disponivel: 80`
- `saldo_bloqueado_judicial: 10`
- `saldo_provisionado_cartao: 10`

**Visualização:** Uma barra empilhada ou um JSON.
```json
{
  "disponivel": 80,
  "bloqueado_judicial": 10,
  "provisionado_cartao": 10
}
```

#### A Lógica do Bloqueio Atômico
Quando uma ordem judicial chega, a operação não é "bloquear a conta". A operação é uma **transação atômica** que move dinheiro do bolso "Disponível" para o "Bloqueio Judicial".

- **Operação:** `UPDATE saldos SET disponivel = disponivel - 10, bloqueado_judicial = bloqueado_judicial + 10 WHERE ...`

Se um Pix chegar no mesmo milissegundo, ele tentará debitar do bolso `disponivel`. Como o valor lá já diminuiu (graças à transação atômica do bloqueio), o Pix pode falhar por "Saldo Insuficiente", mas **o sistema nunca fica inconsistente**.

**A visualização da atomicidade é a corrida que vimos nos cenários:** A operação que ganhar a "Votação" (CockroachDB) ou chegar primeiro no "Quadro Negro" (DynamoDB com CAS) vence. A outra falha matematicamente, não por sorte.
""")

st.header("Estratégias de Arquitetura para um Sistema de Pagamentos")

st.subheader("Estratégia 1: Convivência Híbrida (Mainframe + Cloud)")
st.markdown("""
**O Cenário:** O sistema de core banking (o "livro-razão" oficial) reside em um Mainframe que é lento, caro e suporta no máximo **40 transações por segundo (TPS)**. No entanto, o novo sistema de PIX precisa ser elástico, moderno e aguentar milhares de TPS.

**A Solução (Offloading):** Usamos a nuvem como uma camada de alta performance para "amortecer" a carga sobre o Mainframe.

- **Para PIX Crédito (Ingestão Massiva):**
    - **DynamoDB ou ScyllaDB** são perfeitos aqui. Eles atuam como um "buffer de alta velocidade". Milhares de PIX de crédito chegam e são registrados instantaneamente nestes bancos NoSQL na nuvem.
    - Um processo assíncrono (rodando a cada minuto, por exemplo) lê os lotes de transações do banco NoSQL, os consolida, e envia uma **única transação agregada** para o Mainframe. Ex: `+ R$ 50.000,00`.
    - **Benefício:** O Mainframe recebe apenas 1 transação em vez de 50.000, respeitando seu limite de 40 TPS. A experiência do cliente que enviou o PIX é instantânea.

- **Para PIX Débito (Validação de Saldo):**
    - Este é o maior desafio. O saldo "oficial" está no Mainframe. Fazer uma consulta síncrona ao Mainframe para cada PIX Débito é inviável (lento e derrubaria o Mainframe).
    - **Solução (Cache e Réplica):** O saldo das contas é replicado do Mainframe para um banco rápido na nuvem (como **Redis** ou **DynamoDB**) a cada poucos segundos.
    - Quando um PIX Débito chega, a aplicação primeiro verifica o saldo no cache/réplica na nuvem. Se houver saldo, a transação é aprovada e registrada em um "livro diário" no **CockroachDB ou Aurora**, e só depois enviada para uma fila de processamento que irá consolidá-la no Mainframe.
    - **Risco:** Existe um pequeno risco de o saldo no cache estar defasado. A arquitetura precisa ter mecanismos de reconciliação e lidar com possíveis "saldos a descoberto" que são corrigidos posteriormente.
""")

st.subheader("Estratégia 2: Autorizado Cloud (Nuvem Pura)")
st.markdown("""
**O Cenário:** Não há mais Mainframe. O novo sistema de pagamentos, incluindo seu core (o livro-razão), será construído do zero na nuvem, buscando consistência forte e escalabilidade.

**A Solução:** A escolha do banco de dados para o "core" é a decisão mais crítica.

- **Para o Livro-Razão (Ledger - Onde fica o Saldo):**
    - **CockroachDB** é um candidato ideal. Ele foi projetado para este exato cenário: um banco de dados SQL distribuído que oferece consistência serializável (como um Mainframe ou um PostgreSQL) mas que escala horizontalmente (como um banco NoSQL). Ele pode processar **PIX Débitos** e **Créditos** de forma transacional e segura, em múltiplos servidores, eliminando o gargalo do nó único.
    - **Aurora PostgreSQL** pode ser uma opção se a carga de escrita concorrente na mesma conta não for extrema, aproveitando o conhecimento SQL existente. No entanto, ele ainda pode sofrer com o problema de *Hot Partition* (Cenário A) se uma conta for muito ativa.

- **Para Serviços Auxiliares (Auditoria, Logs, Análise):**
    - **DynamoDB ou ScyllaDB** continuam sendo excelentes escolhas para registrar o "rastro" de cada transação (o *ledger de eventos*). Eles podem ingerir trilhões de eventos de auditoria com baixo custo e altíssima velocidade, sem sobrecarregar o banco de dados principal onde o saldo é mantido.
    - Essa separação de responsabilidades (um banco para o **estado atual do saldo** e outro para o **histórico imutável de eventos**) é um padrão de arquitetura muito robusto e escalável.
""")

