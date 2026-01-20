import streamlit as st
import graphviz
import time

st.set_page_config(layout="wide", page_title="Cenário A: Bloqueio Pessimista")

def render_pessimistic_locking_page():
    st.title("Cenário A: O Bloqueio Pessimista (PostgreSQL / Aurora)")
    st.image("https://i.imgur.com/7H2gn5Y.png", caption="Visualização: A Fila Única (The Single Lane Queue)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        tps = st.slider("Transações por Segundo (TPS)", 1, 10000, 100)
        concurrency = st.slider("Threads Concorrentes na Mesma Conta", 1, 100, 10)
        
        st.header("Cenário de Negócio")
        st.selectbox("Selecione o Cenário", ["Transferência Simples", "Ataque de Concorrência (Double Spend)", "Bloqueio Judicial"], disabled=True)
        
        run_simulation = st.button("Executar Simulação")

    with col2:
        st.header("Visualização do 'Motor'")
        
        # --- Lógica da Simulação ---
        # Fator de engasgo: uma métrica simples para simular o gargalo
        choke_factor = (tps * concurrency) / 5000  # Limiar arbitrário

        queue_size = 0
        if run_simulation:
            if choke_factor < 0.5:
                status_text = "Tudo certo! A fila anda rápido."
                status_color = "green"
                queue_size = 0
            elif choke_factor < 1.5:
                status_text = "Atenção. A fila está começando a crescer."
                status_color = "orange"
                queue_size = min(concurrency - 1, 5)
            else:
                status_text = "GARGALO! A latência está subindo, o sistema vai engasgar."
                status_color = "red"
                queue_size = concurrency -1
            
            st.markdown(f'<p style="background-color:{status_color}; color:white; padding:10px;"><b>Status:</b> {status_text}</p>', unsafe_allow_html=True)

            # --- Geração do Gráfico ---
            dot = graphviz.Digraph('PessimisticLock', comment='The Single Lane Queue')
            dot.attr('graph', rankdir='LR')

            # A "Sala" trancada (Recurso)
            with dot.subgraph(name='cluster_resource') as c:
                c.attr(label='Conta Bancária (Recurso)', style='filled', color='lightgrey')
                c.node('thread_active', 'Thread Ativa (Trancou a Porta)', shape='circle', style='filled', fillcolor='lightblue')

            # A Fila de Threads
            with dot.subgraph(name='cluster_queue') as c:
                c.attr(label='Fila de Espera', style='dashed')
                c.node_attr.update(shape='circle')
                if queue_size == 0:
                    c.node('queue_empty', '(Fila Vazia)', shape='plaintext')
                else:
                    queue_nodes = [f'thread_{i}' for i in range(queue_size)]
                    for i, node in enumerate(queue_nodes):
                        c.node(node, f'Thread {i+1}')
                    # Chain them together
                    for i in range(len(queue_nodes) - 1):
                        dot.edge(queue_nodes[i], queue_nodes[i+1])
            
            # Conexão da Fila com o Recurso
            if queue_size > 0:
                dot.edge('thread_0', 'thread_active', label='Esperando a porta abrir')
            
            st.graphviz_chart(dot)
        else:
            st.info("Ajuste os controles e clique em 'Executar Simulação' para ver o que acontece.")
    
    st.header("Análise Teórica")
    st.markdown("""
    **O Problema:** Garantir que o saldo de uma conta não fique negativo ou inconsistente quando múltiplas transações (débitos) tentam alterá-lo ao mesmo tempo.

    **A Solução (Pessimista):** O banco de dados "tranca" a linha da conta com o comando `SELECT FOR UPDATE`. Isso força qualquer outra transação que queira mexer naquela mesma linha a esperar em uma fila.

    - **O que a visualização mostra:** Quando uma transação (bonequinho) adquire o "lock", ela entra na "sala" para trabalhar no saldo. As outras transações concorrentes são forçadas a formar uma fila do lado de fora.
    - **Trade-offs:**
        - **Prós:** Garante consistência de forma muito forte e simples. É o comportamento padrão e esperado de bancos de dados relacionais.
        - **Contras:** Funciona mal para *Hot Partitions* (ou "Hot Rows") - contas que recebem um volume muito alto de transações concorrentes (ex: a conta de um grande varejista no dia da Black Friday). A fila cresce, a latência aumenta drasticamente e o sistema inteiro pode ser afetado pelo gargalo em uma única conta.
    """)

render_pessimistic_locking_page()
