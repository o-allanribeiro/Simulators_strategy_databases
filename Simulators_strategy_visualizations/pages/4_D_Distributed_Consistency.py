import streamlit as st
import graphviz
import pandas as pd

st.set_page_config(layout="wide", page_title="Cenário D: Consistência Distribuída")

def generate_consensus_graph(nodes, failed_nodes, leader, step):
    dot = graphviz.Digraph('Consensus', comment='Raft/Paxos Voting')
    dot.attr('graph', rankdir='TB', layout='neato', overlap='false', splines='true')
    dot.node_attr.update(shape='house', style='filled')

    for node in nodes:
        if node in failed_nodes:
            dot.node(node, f'Datacenter {node}\n(FALHOU)', fillcolor='grey', fontcolor='white')
        elif node == leader:
            dot.node(node, f'Datacenter {node}\n(LÍDER)', fillcolor='lightblue')
        else:
            dot.node(node, f'Datacenter {node}\n(SEGUIDOR)', fillcolor='lightgreen')

    followers = [n for n in nodes if n != leader and n not in failed_nodes]
    
    if step >= 1:
        for follower in followers:
            dot.edge(leader, follower, label=' Proposta de PIX', style='dashed', dir='forward')
    
    if step >= 2:
        for follower in followers:
            dot.edge(follower, leader, label=' Voto "Sim"', style='dashed', dir='back')
            
    if step == 3:
        dot.node('quorum_status', 'QUÓRUM ALCANÇADO!\nPIX Confirmado', shape='box', style='filled', fillcolor='orange')
        dot.edge(leader, 'quorum_status', style='invis')
    return dot

def render_distributed_consistency_page():
    st.title("Cenário D: Consistência Distribuída (CockroachDB)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        nodes_options = ["São Paulo", "Rio de Janeiro", "Virginia (EUA)", "Oregon (EUA)", "Frankfurt (ALE)"]
        active_nodes = st.multiselect("Datacenters no Cluster Global", options=nodes_options, default=["São Paulo", "Virginia (EUA)", "Frankfurt (ALE)"])
        failed_nodes = st.multiselect("Simular Falha de Datacenter", options=active_nodes)
        
        st.header("Simulação Passo-a-Passo")
        step = st.slider("Avançar na Votação do PIX", 0, 3, 0, format="Passo %d")

    with col2:
        st.header("Visualização do 'Motor' de Consenso")
        if len(active_nodes) < 3:
            st.error("Um cluster de consenso precisa de pelo menos 3 nós para ser tolerante a falhas.")
        else:
            leader = active_nodes[0]
            live_nodes = [n for n in active_nodes if n not in failed_nodes]
            quorum_needed = len(active_nodes) // 2 + 1
            
            st.write(f"**Total de Datacenters:** {len(active_nodes)}")
            st.write(f"**Datacenters Ativos:** {len(live_nodes)}")
            st.write(f"**Quórum Necessário (Maioria):** {quorum_needed} votos")

            if len(live_nodes) >= quorum_needed:
                st.success(f"Cluster SAUDÁVEL. Com {len(live_nodes)} datacenters ativos, é possível alcançar o quórum de {quorum_needed} votos.")
            else:
                st.error(f"Cluster DEGRADADO. Com apenas {len(live_nodes)} datacenters ativos, é impossível alcançar o quórum. O sistema não aceitará novas transações PIX para garantir a consistência.")
            
            graph = generate_consensus_graph(active_nodes, failed_nodes, leader, step)
            st.graphviz_chart(graph)
            
    st.header("Análise Teórica no Contexto PIX")
    st.markdown("""
    **O Problema:** Uma conta de alto volume de uma empresa global precisa de um balanço de saldo único e consistente, mesmo com datacenters espalhados pelo mundo. Como garantir que um **PIX Crédito** no Brasil e um **PIX Débito** na Europa sejam ordenados corretamente, sem risco de inconsistência, mesmo com falhas?

    **A Solução (Consenso Distribuído):** Bancos como o CockroachDB usam o consenso (Raft) para criar uma **ordem serializável global** para todas as transações. A "votação" que a simulação mostra é o mecanismo que garante essa ordem única e a resiliência a desastres.
    """)

    st.header("Disrupção Matemática e Física")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("A Matemática do Quórum")
        st.markdown("**Garantia contra Split-Brain:**")
        st.latex(r'''
        Quorum = \lfloor \frac{N_{replicas}}{2} \rfloor + 1
        ''')
        st.markdown("Com esta fórmula, é matematicamente impossível que dois grupos de nós consigam quórum ao mesmo tempo. Qualquer subgrupo com quórum terá pelo menos um membro em comum com qualquer outro subgrupo com quórum. Este membro em comum 'lembra' da última transação e impede a criação de duas 'verdades' diferentes.")
    with col4:
        st.subheader("A Física da Latência")
        st.markdown("**O Limite da Velocidade da Luz:**")
        st.latex(r'''
        Lat_{escrita} \geq 2 \times Lat_{rede_inter_regional}
        ''')
        st.markdown("Uma transação exige, no mínimo, uma viagem de ida (proposta) e volta (voto) entre o líder e seus seguidores. A performance é fisicamente limitada pela distância geográfica entre os datacenters.")

    st.subheader("Tabela de Latência (Estimativa)")
    latency_data = {
        "Cluster": ["SP-RJ (Mesmo país)", "SP-Virginia (Continentes diferentes)", "SP-Frankfurt-Tokyo (Global)"],
        "Latência de Rede (Round-Trip)": ["~15ms", "~120ms", "~250ms"],
        "Latência Mínima por PIX": ["~30ms", "~240ms", "~500ms"]
    }
    st.table(pd.DataFrame(latency_data))

    st.header("Trade-offs para Contas de Alto Volume")
    st.markdown("""
        - **Prós:** A mais alta garantia de consistência (`SERIALIZABLE`) em escala global. Tolera a falha de datacenters inteiros. Para uma conta que representa o caixa global de uma empresa, essa garantia não é negociável.
        - **Contras:** A latência é real e um fator limitante. Este modelo é escolhido quando a **corretude global** é mais importante para o negócio do que a **latência mínima** de cada transação individual.
    """)

render_distributed_consistency_page()