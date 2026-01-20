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
    st.image("https://i.imgur.com/2A6nFz8.png", caption="Visualização: O Consenso (Raft/Paxos Voting)")

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
            
    st.header("Análise Teórica")
    st.markdown(f"""
    **O Problema:** Como garantir que o saldo de uma conta seja consistente em um banco de dados distribuído geograficamente, mesmo que um datacenter inteiro caia? Como evitar um "Split Brain", onde duas versões diferentes da verdade (do saldo) possam existir temporariamente?

    **A Solução (Consenso):** Antes de confirmar uma escrita, a maioria dos nós que hospedam os dados precisa concordar com a operação. Esse processo de votação é gerenciado por um algoritmo de consenso como o **Raft** (usado no CockroachDB) ou o **Paxos** (usado para Lightweight Transactions no ScyllaDB e Cassandra).

    - **O que a visualização mostra:**
        1.  Uma escrita chega a um dos nós, que atua como **Líder** para aquela transação.
        2.  O Líder envia uma proposta de escrita para os outros nós (**Seguidores**).
        3.  Os Seguidores validam a proposta e enviam um voto de "Sim" de volta.
        4.  Assim que o Líder recebe votos da **maioria** do grupo (o "quórum"), a transação é considerada confirmada (*committed*). Só então o cliente recebe a confirmação de sucesso.
    - **Tolerância a Falhas:** Se um nó (ou até mesmo um datacenter) cair, o cluster continua funcionando normalmente, desde que a maioria dos nós ainda esteja online e possa formar um quórum. Se a maioria dos nós cair, o cluster para de aceitar escritas para evitar inconsistência.
    - **Trade-offs:**
        - **Prós:** Garante a maior consistência possível (Serializável) em um ambiente distribuído. Previne "Split Brain" e sobrevive a desastres regionais sem perda de dados.
        - **Contras:** A latência de escrita é maior, pois exige pelo menos um round-trip de comunicação entre os nós do cluster para cada transação.
    """)

render_distributed_consistency_page()
