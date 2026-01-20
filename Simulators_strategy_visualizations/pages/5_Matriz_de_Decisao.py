import streamlit as st
import graphviz

st.set_page_config(layout="wide", page_title="Matriz de Decisão")

# --- Funções de Desenho dos Diagramas de Trade-off ---

def draw_aurora_tradeoff():
    dot = graphviz.Digraph('AuroraTradeoff', graph_attr={'rankdir': 'TB', 'splines': 'ortho'})
    dot.attr('node', shape='box', style='rounded')
    dot.node('req1', 'Req 1', shape='ellipse')
    dot.node('req2', 'Req 2', shape='ellipse')
    dot.node('req3', 'Req 3', shape='ellipse')
    dot.node('lock', 'LOCK na Conta\n(SELECT FOR UPDATE)', shape='octagon', style='filled', fillcolor='salmon')
    dot.edge('req1', 'lock', label='Processando')
    dot.edge('req2', 'lock', label='Esperando na fila')
    dot.edge('req3', 'lock', label='Esperando na fila')
    dot.attr(label='Fluxo Aurora/PostgreSQL: A Fila Única', labelloc="t", fontsize="14")
    return dot

def draw_dynamo_tradeoff():
    dot = graphviz.Digraph('DynamoTradeoff', graph_attr={'rankdir': 'TB'})
    dot.attr('node', shape='box', style='rounded,filled')

    with dot.subgraph(name='cluster_write') as c:
        c.attr(label='Escrita (Write Sharding)', style='dashed', color='green')
        c.node('write', 'Nova Transação', shape='ellipse', fillcolor='white')
        c.node('shard1', 'Shard 1', fillcolor='lightgreen')
        c.node('shard2', 'Shard 2', fillcolor='lightgreen')
        c.node('shard3', 'Shard 3', fillcolor='lightgreen')
        c.edge('write', 'shard2', label=' hash(id) % 3 ')

    with dot.subgraph(name='cluster_read') as c:
        c.attr(label='Leitura (Scatter-Gather)', style='dashed', color='red')
        c.node('read', 'Calcular Saldo Total', shape='ellipse', fillcolor='white')
        c.edge('read', 'shard1', label='Lê')
        c.edge('read', 'shard2', label='Lê')
        c.edge('read', 'shard3', label='Lê')
    
    dot.attr(label='Fluxo DynamoDB com Sharding: Escrita Fácil, Leitura Cara', labelloc="t", fontsize="14")
    return dot

def draw_cockroach_tradeoff():
    dot = graphviz.Digraph('CockroachTradeoff')
    dot.attr('node', shape='box', style='rounded')
    
    with dot.subgraph(name='cluster_sp') as sp:
        sp.attr(label='Data Center: São Paulo')
        sp.node('sp_node', 'Nó 1 (Leader)', style='filled', fillcolor='lightblue')

    with dot.subgraph(name='cluster_us') as us:
        us.attr(label='Data Center: Virginia (EUA)')
        us.node('us_node', 'Nó 2')

    with dot.subgraph(name='cluster_eu') as eu:
        eu.attr(label='Data Center: Irlanda (EU)')
        eu.node('eu_node', 'Nó 3')

    dot.edge('sp_node', 'us_node', label=' Latência de Rede\n(Consenso Raft)')
    dot.edge('us_node', 'eu_node', label=' Latência de Rede\n(Consenso Raft)')
    dot.edge('eu_node', 'sp_node', label=' Latência de Rede\n(Consenso Raft)')
    dot.attr(label='Fluxo CockroachDB: Consenso Distribuído', labelloc="t", fontsize="14")
    return dot


# --- Dados dos Bancos (Estrutura Corrigida para URL de Markdown) ---
db_data = {
    "Aurora PostgreSQL": {
        "metaphora": "Fila Única (Lock Pessimista)",
        "motivacao": "Bancos tradicionais, baixo/médio TPS por conta, migração 'as-is' de legado.",
        "garantia": "ACID completo, SQL padrão.",
        "custo": "Sofre com Hot Partitions (a fila trava o sistema).",
        "pagina_url": "1_A_Pessimistic_Locking",
        "nome_simulacao": "Modelo Pessimista",
        "diagrama": draw_aurora_tradeoff
    },
    "DynamoDB + Sharding": {
        "metaphora": "Múltiplos Cofres (Scatter-Gather)",
        "motivacao": "Contas 'Baleia' (Ex: Conta concentradora de marketplaces) com altíssima ingestão de créditos.",
        "garantia": "Escalabilidade de escrita 'infinita'.",
        "custo": "Leitura do saldo total é complexa e cara (Scatter-Gather). Débito em tempo real é um desafio.",
        "pagina_url": "2_B_DynamoDB_Sharding",
        "nome_simulacao": "Escalando com Sharding",
        "diagrama": draw_dynamo_tradeoff
    },
    "CockroachDB": {
        "metaphora": "Votação Global (Consenso Raft)",
        "motivacao": "Banco Global, Multi-Região, necessidade de Strong Consistency sem perder a sintaxe SQL.",
        "garantia": "Sobrevive à queda de um Data Center. Garante que o saldo nunca erre, mesmo com latência de rede.",
        "custo": "Latência de escrita maior devido à comunicação entre nós (o preço da consistência global).",
        "pagina_url": None,
        "nome_simulacao": "Consenso Distribuído",
        "diagrama": draw_cockroach_tradeoff
    }
}

st.title("Matriz de Decisão Interativa")
st.markdown("Selecione uma tecnologia de banco de dados para ver uma análise de sua abordagem e os trade-offs envolvidos.")

option = st.selectbox(
    "Selecione a Tecnologia de Banco de Dados:",
    options=list(db_data.keys())
)

st.divider()

if option:
    data = db_data[option]
    st.header(f"Análise: {option}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Metáfora Visual")
        st.info(data["metaphora"])
        
        st.subheader("Quando Usar (Motivação)")
        st.write(data["motivacao"])
        
        st.subheader("Garantias")
        st.success(f"✔️ {data['garantia']}")

        st.subheader("Custo / Trade-off")
        st.error(f"❌ {data['custo']}")
    
    with col2:
        st.subheader("Diagrama do Fluxo de Trade-off")
        st.graphviz_chart(data["diagrama"]())

    st.divider()

    if data["pagina_url"]:
        st.subheader("Cenário de Simulação Relacionado")
        # CORREÇÃO: Usando st.markdown para criar o link como alternativa ao st.page_link
        link_markdown = f"""
        <a href="{data['pagina_url']}" target="_self" style="display: inline-block; padding: 0.5em 1em; background-color: #0068c9; color: white; text-decoration: none; border-radius: 0.25rem; font-weight: 600;">
            🔬 Ir para a simulação do <strong>{data['nome_simulacao']}</strong>
        </a>
        """
        st.markdown(link_markdown, unsafe_allow_html=True)
    else:
        st.info(f"Ainda não há uma simulação interativa específica para o cenário de **{data['nome_simulacao']}**.")