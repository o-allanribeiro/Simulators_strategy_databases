import streamlit as st
import graphviz
import time

st.set_page_config(layout="wide", page_title="Cenário A: Bloqueio Pessimista")

def render_pessimistic_locking_page():
    st.title("Cenário A: O Bloqueio Pessimista (PostgreSQL / Aurora)")

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
    
    st.header("Análise Teórica no Contexto PIX")
    st.markdown("""
    **O Problema:** Como um sistema de pagamentos processa um **PIX Débito** na conta de um cliente, garantindo que o saldo não fique negativo se, no mesmo instante, outros débitos (ou mesmo um estorno de crédito) estiverem acontecendo?

    **A Solução (Pessimista com `SELECT FOR UPDATE`):**
    A abordagem tradicional em bancos de dados como PostgreSQL ou Aurora é ser "pessimista". Ao processar um PIX Débito, o sistema executa os seguintes passos:
    1.  `BEGIN TRANSACTION;`
    2.  `SELECT saldo FROM contas WHERE id = ? FOR UPDATE;`
        - **Este é o comando chave.** O `FOR UPDATE` age como uma tranca na porta da sala. O banco de dados bloqueia a linha específica daquela conta.
        - Qualquer outra transação (outro PIX Débito, uma transferência, um pagamento de boleto) que tente ler *esta mesma linha com `FOR UPDATE`* é colocada em uma fila.
    3.  A aplicação verifica se o saldo é suficiente.
    4.  Se sim, `UPDATE contas SET saldo = saldo - ? WHERE id = ?;`
    5.  `COMMIT;` (A tranca é liberada e o próximo da fila pode entrar).

    - **O que a visualização mostra:** A "Thread Ativa" é a transação do PIX Débito que conseguiu o bloqueio. A "Fila de Espera" são as outras transações (outros PIX) que estão aguardando a liberação da tranca para poderem acessar o saldo.
    - **Trade-offs para PIX:**
        - **Prós:** Garante consistência de forma absoluta e simples de implementar. É a maneira mais segura de evitar que o saldo "fure" (double-spending).
        - **Contras:** É um desastre para contas muito ativas (*Hot Partitions*). Imagine a conta de um grande e-commerce na Black Friday recebendo milhares de **PIX Crédito** e, ao mesmo tempo, tentando fazer um **PIX Débito** para um fornecedor. A fila para acessar o saldo dessa única conta pode travar o sistema. A latência de cada PIX aumenta drasticamente, pois todos precisam esperar sua vez na "fila da porta".
    """)

render_pessimistic_locking_page()
