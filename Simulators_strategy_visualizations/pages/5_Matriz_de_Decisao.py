import streamlit as st

st.set_page_config(layout="wide", page_title="Matriz de Decisão")

# --- Dados dos Bancos ---
db_data = {
    "Aurora PostgreSQL": {
        "metaphora": "Fila Única (Lock Pessimista)",
        "motivacao": "Bancos tradicionais, baixo/médio TPS por conta, migração 'as-is' de legado.",
        "garantia": "ACID completo, SQL padrão.",
        "custo": "Sofre com Hot Partitions (a fila trava o sistema).",
        "cenario": "Cenário A"
    },
    "DynamoDB (Padrão)": {
        "metaphora": "Corrida com Versão (Lock Otimista)",
        "motivacao": "Alta escala, varejo, Pix, microsserviços na AWS. Custo x Benefício excelente.",
        "garantia": "Alta disponibilidade.",
        "custo": "Exige controle de retry (com exponential backoff + jitter) na aplicação para evitar Race Conditions.",
        "cenario": "Cenário B"
    },
    "DynamoDB + Sharding": {
        "metaphora": "Múltiplos Cofres (Scatter-Gather)",
        "motivacao": "Contas 'Baleia' (Ex: Conta concentradora do iFood ou Mercado Livre) com altíssima ingestão de créditos.",
        "garantia": "Escalabilidade de escrita 'infinita'.",
        "custo": "Leitura do saldo total é complexa/cara. Débito em tempo real é um grande desafio.",
        "cenario": "Cenário C"
    },
    "CockroachDB": {
        "metaphora": "Votação Global (Raft Consensus)",
        "motivacao": "Banco Global, Multi-Região, necessidade de Strong Consistency sem perder a sintaxe SQL.",
        "garantia": "Sobrevive à queda de um Data Center. Garante que o saldo nunca fure, mesmo com latência de rede.",
        "custo": "Latência de escrita maior devido à comunicação entre nós (o preço da consistência global).",
        "cenario": "Cenário D"
    },
    "ScyllaDB / Cassandra": {
        "metaphora": "Pista Expressa (LSM-Tree) + Particionamento",
        "motivacao": "Latência ultrabaixa e throughput massivo, quando a consistência forte não é o requisito principal para cada operação.",
        "garantia": "Performance bruta por nó.",
        "custo": "Consistência eventual por padrão, modelo de dados rígido e alta complexidade operacional.",
        "cenario": "Não simulado diretamente (mas conceitos aplicados nos Cenários B e C)"
    }
}

st.title("Matriz de Decisão Interativa")

st.markdown("""
Selecione uma tecnologia de banco de dados abaixo para ver uma análise detalhada de sua abordagem, motivação e os trade-offs envolvidos, baseada nos cenários que exploramos.
""")

# --- Seletor Interativo ---
option = st.selectbox(
    "Selecione a Tecnologia de Banco de Dados:",
    options=list(db_data.keys())
)

st.divider()

# --- Exibição das Informações ---
if option:
    data = db_data[option]
    st.header(f"Análise: {option}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Metáfora Visual")
        st.info(data["metaphora"])
        
        st.subheader("Quando Usar (Motivação)")
        st.write(data["motivacao"])
    
    with col2:
        st.subheader("Garantias")
        st.success(f"✔️ {data['garantia']}")

        st.subheader("Custo / Trade-off")
        st.error(f"❌ {data['custo']}")
        
    st.subheader("Cenário de Simulação Relacionado")
    st.page_link(f"pages/{data['cenario'].replace(' ', '_')}.py", label=f"Ir para a simulação do **{data['cenario']}**", icon="🔬")

st.divider()

# --- O restante do conteúdo permanece o mesmo ---
st.header("Estratégias de Arquitetura para um Sistema de Pagamentos")
# ... (o resto do arquivo que já existia)
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