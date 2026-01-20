import streamlit as st
import graphviz

st.set_page_config(layout="wide", page_title="Cenário D: Consistência Distribuída")

# --- Funções de Simulação e Visualização ---
def generate_consensus_graph(nodes, failed_nodes, leader, step):
    dot = graphviz.Digraph('Consensus', comment='Raft/Paxos Voting')
    dot.attr('graph', rankdir='TB', layout='sfdp') # Use a force-directed layout
    dot.node_attr.update(shape='circle', style='filled')

    # --- Nós do Cluster ---
    for node in nodes:
        if node in failed_nodes:
            dot.node(node, f'Node {node}\n(FAILED)', fillcolor='grey', fontcolor='white')
        elif node == leader:
            dot.node(node, f'Node {node}\n(LEADER)', fillcolor='lightblue')
        else:
            dot.node(node, f'Node {node}\n(FOLLOWER)', fillcolor='lightgreen')

    # --- Lógica de Visualização por Passo ---
    followers = [n for n in nodes if n != leader and n not in failed_nodes]
    
    if step >= 1: # Líder envia proposta
        for follower in followers:
            dot.edge(leader, follower, label=' Proposta de Escrita', style='dashed', dir='forward')
    
    if step >= 2: # Seguidores respondem
        for follower in followers:
            dot.edge(follower, leader, label=' Voto "Sim"', style='dashed', dir='back')
            
    if step == 3: # Quórum alcançado
        dot.node('quorum_status', 'QUÓRUM ALCANÇADO!', shape='box', style='filled', fillcolor='orange')
        dot.edge(leader, 'quorum_status', style='invis')


    return dot

# --- Interface do Streamlit ---
def render_distributed_consistency_page():
    st.title("Cenário D: Consistência Distribuída (CockroachDB / ScyllaDB LWT)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        nodes_options = ["São Paulo", "Rio de Janeiro", "New York", "Tokyo", "Frankfurt"]
        active_nodes = st.multiselect("Nós Ativos no Cluster", options=nodes_options, default=["São Paulo", "Rio de Janeiro", "New York"])
        failed_nodes = st.multiselect("Simular Falha de Nós", options=active_nodes)
        
        st.header("Simulação Passo-a-Passo")
        step = st.slider("Avançar na Simulação", 0, 3, 0, 
                         format="Passo %d",
                         help="Passo 0: Início. Passo 1: Líder envia proposta. Passo 2: Seguidores respondem. Passo 3: Quórum confirmado.")

    with col2:
        st.header("Visualização do 'Motor'")

        if len(active_nodes) < 3:
            st.error("Um cluster de consenso precisa de pelo menos 3 nós para ser tolerante a falhas.")
        else:
            # --- Lógica da Simulação ---
            leader = active_nodes[0] # Simplificação: o primeiro nó é sempre o líder
            live_nodes = [n for n in active_nodes if n not in failed_nodes]
            quorum_needed = len(active_nodes) // 2 + 1
            
            st.write(f"**Total de Nós:** {len(active_nodes)}")
            st.write(f"**Nós Ativos:** {len(live_nodes)}")
            st.write(f"**Quórum Necessário (Maioria):** {quorum_needed} votos")

            if len(live_nodes) >= quorum_needed:
                st.success(f"O cluster está saudável. Com {len(live_nodes)} nós ativos, é possível alcançar o quórum de {quorum_needed} votos.")
                if step == 3:
                     st.info("O líder recebeu votos suficientes, a escrita é confirmada (commit) e o novo saldo é replicado para todos.")
            else:
                st.error(f"O cluster perdeu o quórum! Com apenas {len(live_nodes)} nós ativos, é impossível alcançar os {quorum_needed} votos necessários. O cluster não aceitará novas escritas para garantir a consistência.")
            
            graph = generate_consensus_graph(active_nodes, failed_nodes, leader, step)
            st.graphviz_chart(graph)
            
    st.header("Análise Teórica no Contexto PIX")
    st.markdown(f"""
    **O Problema:** Uma conta de alto volume pertence a uma empresa global que opera no Brasil e na Europa. A empresa precisa de um **único balanço de saldo global**, mas com altíssima disponibilidade e resiliência a desastres. Como garantir que um **PIX Crédito** recebido no Brasil (processado pelo nó de São Paulo) e um **PIX Débito** para um fornecedor na Europa (processado pelo nó de Frankfurt) sejam ordenados corretamente, sem risco de inconsistência, mesmo que um dos datacenters caia no meio da operação?

    **A Solução (Consenso Distribuído para Ordem Global):**
    É aqui que o custo de latência do consenso se torna um investimento em corretude. Bancos como o CockroachDB usam o consenso (Raft) não apenas para tolerar falhas, mas para criar uma **ordem serializável global** para todas as transações.

    1.  A transação do **PIX Débito** chega a Frankfurt. O nó de Frankfurt se torna o **Líder** para esta transação.
    2.  Simultaneamente, a transação do **PIX Crédito** chega a São Paulo, que se torna líder para *sua* transação.
    3.  Ambos os líderes enviam propostas para os outros nós (os Seguidores) para "reservar" seu lugar na fila global de transações.
    4.  Através do processo de votação, o protocolo de consenso estabelece uma ordem inequívoca. Por exemplo, o sistema pode decidir globalmente que a transação de CRÉDITO tem precedência.
    5.  A transação de crédito é confirmada (commit) após obter quórum.
    6.  A transação de débito, ao tentar obter seu quórum, agora verá o resultado da transação de crédito já aplicada, garantindo que o cálculo do saldo seja feito sobre o valor mais recente e correto.

    - **O que a visualização mostra:** O mecanismo que permite essa ordem. Ao simular uma falha, você vê que a capacidade de formar um "acordo majoritário" (quórum) é a chave para o sistema continuar operando e, mais importante, continuar ordenando as transações corretamente. Sem quórum, o sistema para, pois não pode mais garantir essa ordem, o que para um sistema financeiro é a única decisão segura a ser tomada.
    
    - **Trade-offs para Contas de Alto Volume:**
        - **Prós:** É a única maneira de garantir consistência ACID *serializável* em escala global. Para uma conta de alto volume que representa o caixa de uma empresa inteira, essa garantia não é negociável. Previne fraudes e erros contábeis que poderiam surgir de "race conditions" entre diferentes regiões.
        - **Contras:** A latência é real. Cada transação paga o preço da comunicação inter-regional para garantir a consistência. Este modelo é escolhido quando a **corretude global** é mais importante para o negócio do que a **latência mínima** de cada transação individual.
    """)

render_distributed_consistency_page()
