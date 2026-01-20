import streamlit as st

st.set_page_config(
    page_title="Simuladores de Estratégias de Banco de Dados",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Simuladores de Estratégias de Banco de Dados")

st.markdown("""
Bem-vindo ao painel de visualização de estratégias de bancos de dados distribuídos.

Este projeto, inspirado nas clássicas visualizações da **USFCA**, tem como objetivo demonstrar de forma prática e intuitiva como diferentes tecnologias de banco de dados lidam com problemas comuns de concorrência, consistência e escalabilidade.

### Como Usar:

1.  **Selecione um Cenário:** Use o menu na barra lateral esquerda para escolher um dos cenários de simulação.
2.  **Ajuste os Controles:** Em cada cenário, você encontrará um "Painel de Controle" que permite ajustar parâmetros como Transações por Segundo (TPS) e Concorrência.
3.  **Execute a Simulação:** Clique no botão de execução para ver o "motor" do banco de dados em ação na área de visualização.
4.  **Entenda a Teoria:** Após a visualização, leia a análise teórica que explica os prós, contras e trade-offs da abordagem simulada.

Comece selecionando um cenário na barra lateral!
""")

st.header("Cenários Disponíveis:")

st.info("""
**Cenário A: O Bloqueio Pessimista**  
*Visualiza a "fila única" formada pelo `SELECT FOR UPDATE` em bancos como PostgreSQL e Aurora.*

**Cenário B: O Bloqueio Otimista**  
*Visualiza a "corrida pela escrita" com versionamento (Compare-and-Swap) em bancos como o DynamoDB.*

**Cenário C: Sharding de Saldo**  
*Visualiza a estratégia de "múltiplos cofres" (Scatter-Gather) para escalar a escrita em contas "baleia".*

**Cenário D: Consistência Distribuída**  
*Visualiza o processo de "votação" e consenso (Raft/Paxos) em bancos de dados geograficamente distribuídos como CockroachDB.*
""", icon="👉")

st.sidebar.success("Selecione um cenário de simulação acima.")