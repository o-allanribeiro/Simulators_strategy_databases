import streamlit as st
import graphviz
import pandas as pd
import numpy as np

st.set_page_config(layout="wide", page_title="Cenário A: Bloqueio Pessimista")

def render_pessimistic_locking_page():
    st.title("Cenário A: O Bloqueio Pessimista (Mainframe / PostgreSQL)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        tps = st.slider("Transações por Segundo (TPS) na Conta", 1, 300, 30)
        concurrency = st.slider("Threads Concorrentes na Mesma Conta", 1, 100, 5)
        
        st.header("Cenário de Negócio")
        st.selectbox("Selecione o Cenário", ["PIX Débito Concorrente"], disabled=True)
        
        run_simulation = st.button("Executar Simulação")

    with col2:
        st.header("Visualização do 'Motor'")
        
        mainframe_tps_limit = 40
        is_bottlenecked = tps > mainframe_tps_limit

        if run_simulation:
            if not is_bottlenecked:
                st.success(f"Status: DENTRO DO LIMITE. Com {tps} TPS, o sistema consegue processar as transações e a fila permanece gerenciável.")
            else:
                st.error(f"Status: GARGALO! A taxa de chegada ({tps} TPS) excede a capacidade de serviço ({mainframe_tps_limit} TPS). A fila de transações crescerá indefinidamente.")
            
            queue_size = min(concurrency - 1, 10) if is_bottlenecked else max(0, concurrency - 5)
            dot = graphviz.Digraph('PessimisticLock', comment='The Single Lane Queue')
            dot.attr('graph', rankdir='LR')
            with dot.subgraph(name='cluster_resource') as c:
                c.attr(label=f"Core Bancário (Serviço: {mainframe_tps_limit} TPS)", style='filled', color='lightgrey')
                c.node('thread_active', '1 Transação Ativa\n(LOCK na Conta)', shape='box', style='filled', fillcolor='lightblue')
            with dot.subgraph(name='cluster_queue') as c:
                c.attr(label=f'Fila de Chegada (Chegada: {tps} TPS)', style='dashed')
                if queue_size > 0:
                    for i in range(queue_size):
                        c.node(f'TXN_{i}', f'PIX {i+1}')
                    dot.edge('TXN_0', 'thread_active', label=' Esperando o LOCK')
            st.graphviz_chart(dot)
        else:
            st.info("Ajuste os controles e clique em 'Executar Simulação' para ver o que acontece.")
    
    st.header("Análise Teórica e Matemática do Gargalo")
    st.markdown("""
    **O Problema:** Como um sistema legado (Mainframe) ou um banco relacional de nó único (PostgreSQL) com capacidade de serviço finita lida com picos de transações concorrentes em uma mesma conta?
    """)
    
    st.subheader("Disrupção Matemática: A Teoria das Filas")
    st.markdown(r"""
    Este cenário é um exemplo clássico de um sistema de filas, que pode ser modelado matematicamente. A **Lei de Little** nos dá a relação fundamental:
    """)
    st.latex(r"L = \lambda \times W")
    st.markdown(r"""
    - $L$ = Número médio de clientes no sistema (o tamanho da nossa fila de PIX).
    - $\lambda$ (Lambda) = Taxa média de chegada de clientes (o TPS do nosso sistema).
    - $W$ = Tempo médio de espera de um cliente no sistema (a latência de um PIX).

    O "motor" do nosso sistema (o Mainframe) tem uma **capacidade máxima de serviço**, representada por $\mu$ (Mu). No nosso caso, $\mu = 40$ TPS.

    O colapso do sistema ocorre quando a taxa de chegada é maior que a taxa de serviço:
    """)
    st.latex(r"\lambda > \mu \implies \text{A fila (L) cresce para o infinito}")
    st.markdown(r"""
    Se chegam mais transações do que o sistema consegue processar, a fila aumenta indefinidamente. Pela Lei de Little ($W = L / \lambda$), se $L$ tende ao infinito, o tempo de espera $W$ (latência) também tende ao infinito. **Este é o gargalo matemático**: o sistema não é mais capaz de atender às requisições em um tempo razoável.
    """
    )

    st.header("Análise de Custo e Técnicas de Mitigação")
    st.markdown("""
    - **Mainframe:** Possui um custo fixo altíssimo com um hard cap de ~40 TPS. Escalar é proibitivamente caro.
    - **Cloud (Aurora PostgreSQL):** Opera em "pay-as-you-go". Embora a contenção de "hot row" ainda exista, a nuvem oferece alternativas.
    """
    )
    
    st.subheader("Gráfico: Custo por Transação vs. TPS")
    tps_range = np.arange(1, 301, 1)
    cost_mainframe = [100 / t if t <= 40 else np.nan for t in tps_range]
    cost_cloud = [20 / t * (1 + t/100) for t in tps_range]
    chart_data = pd.DataFrame({
        "TPS": tps_range, "Custo/Transação - Mainframe": cost_mainframe, "Custo/Transação - Cloud (Aurora)": cost_cloud
    }).set_index("TPS")
    st.line_chart(chart_data)
    st.markdown("O gráfico ilustra como o custo do Mainframe se torna 'infinito' após o limite, enquanto a nuvem continua operando, embora com custo crescente devido à contenção.")

    st.subheader("Técnicas de Mitigação para Hot Rows (Mesmo em Modelos Pessimistas)")
    st.markdown("""
    Mesmo sem mudar para um modelo otimista, existem estratégias para aliviar o gargalo:
    1.  **Read Replicas:** Desviar a carga de leitura (consultas analíticas, relatórios) para réplicas do banco de dados. Isso libera o nó primário para focar apenas nas escritas (`UPDATE` de saldo), aumentando sua capacidade de serviço `μ`.
    2.  **Otimização da Aplicação:** Garantir que as transações que usam `SELECT FOR UPDATE` sejam o mais curtas e rápidas possível. O "lock" deve ser mantido pelo menor tempo imaginável.
    3.  **Sharding na Aplicação:** Em vez de um único banco de dados, a aplicação pode se conectar a múltiplos bancos de dados (ex: um para contas com final 0-4, outro para 5-9). Isso divide a carga de "hot rows", mas aumenta drasticamente a complexidade da aplicação.
    """
    )

render_pessimistic_locking_page()
