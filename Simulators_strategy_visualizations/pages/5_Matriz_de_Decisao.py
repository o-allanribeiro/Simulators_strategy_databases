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
