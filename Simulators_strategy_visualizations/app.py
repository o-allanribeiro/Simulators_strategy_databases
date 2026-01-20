import streamlit as st

st.set_page_config(
    page_title="Simulador de Sistemas Distribuídos para Finanças",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔬 Simulador de Sistemas Distribuídos para Finanças")

st.markdown("""
---
### Premissas e Motivação Científica

Este painel é um **laboratório de experimentos computacionais** projetado para modelar e visualizar a dinâmica de sistemas de banco de dados sob estresse, especificamente no contexto de sistemas de pagamento de alta performance como o PIX.

A premissa fundamental é que a escolha de uma arquitetura de dados não é uma busca pela "melhor" tecnologia, mas um **exercício de engenharia de trade-offs**. Todo sistema financeiro deve balancear três forças concorrentes, conforme definido pelo **Teorema CAP** e suas extensões (PACELC):

1.  **Consistência (C):** Todos os nós do sistema veem os mesmos dados ao mesmo tempo? Para um saldo bancário, a consistência é crítica.
2.  **Disponibilidade (A - Availability):** O sistema está sempre disponível para aceitar transações?
3.  **Performance / Baixa Latência (P / L):** Quão rápido o sistema responde a uma requisição?

O objetivo deste simulador é tornar esses trade-offs, muitas vezes abstratos, em visualizações concretas e intuitivas. Através da simulação de diferentes cenários, podemos explorar como as escolhas de arquitetura (ex: bloqueio pessimista vs. otimista) e as leis fundamentais da ciência da computação (ex: Teoria das Filas, limites de velocidade da rede) impactam o comportamento de um sistema no mundo real.

---
""")

st.header("Experimentos Disponíveis")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cenário A: O Gargalo da Fila Única")
    st.markdown("""
    *(`Pessimistic Locking`)*
    
    **Experimento:** Modelar um sistema legado (Mainframe/PostgreSQL) com um bloqueio exclusivo.
    
    **O que observar:** Como a latência de um **PIX Débito** explode quando a taxa de chegada de transações (`λ`) excede a capacidade de serviço (`μ`) do sistema, validando a **Teoria das Filas**.
    """)

    st.subheader("Cenário C: A Escalabilidade da Escrita")
    st.markdown("""
    *(`Write Sharding`)*

    **Experimento:** Modelar uma arquitetura de "múltiplos cofres" para absorver um volume massivo de **PIX Crédito**.

    **O que observar:** Como a capacidade de escrita escala linearmente com o número de shards, mas cria um desafio fundamental para a leitura e consolidação do saldo para **PIX Débito**.
    """)

with col2:
    st.subheader("Cenário B: A Corrida pela Escrita")
    st.markdown("""
    *(`Optimistic Locking`)*

    **Experimento:** Modelar um sistema NoSQL (DynamoDB) usando versionamento para processar débitos concorrentes.

    **O que observar:** A "corrida pela escrita" (race condition) e o impacto das falhas de escrita condicional na latência e no custo, demonstrando a necessidade de uma fila na aplicação.
    """)

    st.subheader("Cenário D: O Custo da Confiança Global")
    st.markdown("""
    *(`Distributed Consistency`)*

    **Experimento:** Modelar um banco de dados geograficamente distribuído (CockroachDB) que usa um algoritmo de consenso (votacão).
    
    **O que observar:** Como a consistência global é garantida ao custo da latência, que é fisicamente limitada pela distância entre os datacenters (velocidade da luz).
    """)

st.sidebar.success("Selecione um experimento acima.")
