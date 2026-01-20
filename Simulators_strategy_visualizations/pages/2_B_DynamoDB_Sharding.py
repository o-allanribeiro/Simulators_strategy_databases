import streamlit as st
import graphviz
import random
import time
import pandas as pd

st.set_page_config(layout="wide", page_title="Modelo Físico: DynamoDB Sharding")

# --- Estado da Simulação ---
if 'shards' not in st.session_state:
    st.session_state.shards = [{"id": i, "wcu": 0, "requests": []} for i in range(10)]
if 'log' not in st.session_state:
    st.session_state.log = []
if 'total_requests' not in st.session_state:
    st.session_state.total_requests = 0
if 'throttled_requests' not in st.session_state:
    st.session_state.throttled_requests = 0

def reset_simulation():
    st.session_state.shards = [{"id": i, "wcu": 0, "requests": []} for i in range(10)]
    st.session_state.log = ["Simulação reiniciada."]
    st.session_state.total_requests = 0
    st.session_state.throttled_requests = 0

# --- Funções de Visualização ---
def create_dynamo_graph(shards, strategy, tps):
    dot = graphviz.Digraph('DynamoDBShards', comment='DynamoDB Write Sharding')
    dot.attr('graph', rankdir='TB', splines='ortho', label=f'Estratégia: {strategy} | Carga: {tps} TPS', fontname="Arial", fontsize="14")
    dot.attr('node', shape='box', style='rounded,filled', fontname="Arial", fontsize="10")

    # Limitar visualmente as requisições para não poluir
    MAX_REQ_DISPLAY = 5

    # Desenha as requisições recebidas
    with dot.subgraph(name='cluster_requests') as c:
        c.attr(label='', color='white')
        
        # Limita o número de requisições a serem exibidas
        num_requests_to_show = min(tps // 100 if tps > 100 else 1, MAX_REQ_DISPLAY)
        
        for i in range(num_requests_to_show):
            tx_id = f"tx_{random.randint(1000, 9999)}"
            c.node(tx_id, f"Req {tx_id}", shape='ellipse', fillcolor='lightblue')

            if strategy == "Single Partition":
                target_shard_id = 0
                dot.edge(tx_id, f"shard_0", style='dashed')
            else: # Write Sharding
                # O hash pode ser qualquer coisa, vamos simular aleatoriamente
                target_shard_index = random.randint(0, 9)
                dot.edge(tx_id, f"shard_{target_shard_index}", style='dashed')

    # Desenha os shards (cofres)
    with dot.subgraph(name='cluster_shards') as c:
        c.attr(label='Partições Físicas (Shards) no DynamoDB', style='dashed', fontname="Arial", fontsize="12")
        for i, shard in enumerate(shards):
            wcu = shard['wcu']
            
            # Lógica de "Partição Quente"
            if strategy == "Single Partition" and i == 0:
                hot = wcu > 1000
                color = 'salmon' if hot else 'lightgrey'
                label = f"Shard {i} (PK: CONTA-123)\nWCU: {wcu}"
                if hot:
                    label += "\n🔥 HOT PARTITION 🔥\n(THROTTLING!)"
            elif strategy != "Single Partition":
                color = 'lightgrey'
                label = f"Shard {i} (PK: CONTA-123#{i})\nWCU: {wcu}"
            else: # Shards não utilizados no modo Single Partition
                 label = f"Shard {i}\n(Inativo)"
                 color = 'whitesmoke'

            c.node(f"shard_{i}", label, fillcolor=color)
            
    return dot

# --- Lógica da Simulação ---
def run_dynamo_simulation(strategy, tps):
    st.session_state.total_requests += tps
    
    if strategy == "Single Partition":
        shard = st.session_state.shards[0]
        # Se a capacidade do shard (1000 WCU/s) for excedida
        if shard['wcu'] + tps > 1000:
            accepted_tps = 1000 - shard['wcu']
            throttled_tps = tps - accepted_tps
            st.session_state.throttled_requests += throttled_tps
            shard['wcu'] = 1000
            st.session_state.log.insert(0, f"🔴 Throttling! {throttled_tps} requisições rejeitadas. Partição 0 no limite.")
        else:
            accepted_tps = tps
            shard['wcu'] += accepted_tps
            st.session_state.log.insert(0, f"🟢 {accepted_tps} requisições aceitas no Shard 0.")
    
    else: # Write Sharding
        # Distribui o TPS pelos 10 shards
        for _ in range(tps):
            target_shard_index = random.randint(0, 9)
            st.session_state.shards[target_shard_index]['wcu'] += 1
        st.session_state.log.insert(0, f"🟢 {tps} requisições distribuídas entre 10 shards.")

# --- UI ---
st.title("Modelo Físico: DynamoDB - Partições Quentes e Sharding")
st.markdown("""
Esta simulação demonstra o problema da **Hot Partition** no DynamoDB e como a estratégia de **Write Sharding** o resolve.
- **Single Partition**: Todas as escritas para a mesma conta vão para a mesma partição física, que tem um limite de 1000 WCU/s.
- **Write Sharding**: Adicionamos um sufixo aleatório à chave de partição (ex: `CONTA-123#1`, `CONTA-123#2`), distribuindo a carga entre múltiplas partições.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Painel de Controle")
    strategy = st.radio(
        "Estratégia de Armazenamento",
        ("Single Partition", "Write Sharding"),
        key='strategy',
        help="Single Partition concentra a carga. Write Sharding a distribui."
    )
    tps = st.slider(
        "Intensidade de Escrita (TPS)",
        min_value=100,
        max_value=5000,
        step=100,
        value=1000,
        help="Simula o número de requisições de escrita por segundo para a mesma conta."
    )
    
    if st.button("Executar Simulação (1 segundo)"):
        run_dynamo_simulation(strategy, tps)

    if st.button("Reiniciar Simulação"):
        reset_simulation()
        st.rerun()

    st.subheader("Log de Eventos")
    st.code('\n'.join(st.session_state.log[:10]), language='text')

with col2:
    st.header("Visualização da Distribuição de Carga")
    
    if not st.session_state.log:
        st.info("Ajuste os controles e clique em 'Executar' para iniciar.")
    else:
        graph = create_dynamo_graph(st.session_state.shards, st.session_state.strategy, tps)
        st.graphviz_chart(graph)
        
        st.subheader("Análise de Desempenho")
        total_wcu = sum(s['wcu'] for s in st.session_state.shards)
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Requisições Totais", f"{st.session_state.total_requests}")
        kpi2.metric("Requisições Rejeitadas", f"{st.session_state.throttled_requests}", delta=f"{st.session_state.throttled_requests/st.session_state.total_requests:.1%}" if st.session_state.total_requests > 0 else "0%", delta_color="inverse")
        kpi3.metric("WCU Total Consumido", f"{total_wcu}")

        # Gráfico de WCU por Shard
        chart_data = pd.DataFrame({
            "Shard": [f"Shard {s['id']}" for s in st.session_state.shards],
            "WCU Consumido": [s['wcu'] for s in st.session_state.shards]
        }).set_index("Shard")
        
        st.bar_chart(chart_data)

st.header("Análise de Trade-offs")
st.markdown("""
| Estratégia | Performance de Escrita (Write) | Performance de Leitura (Read) | Custo | Complexidade |
| :--- | :--- | :--- | :--- | :--- |
| **Single Partition** |  limitada a 1000 WCU/s. **Gargalo** sob alta carga. | **Ótima**. O saldo total é lido de um único item. | Baixo | Baixa |
| **Write Sharding** | **Altamente escalável**. A carga é distribuída. | **Pior**. Requer uma consulta a todos os N shards para calcular o saldo (`Scatter-Gather`), o que é mais lento e caro. | Alto | Alta |

**O Custo da Leitura (Scatter-Gather):**
Para obter o saldo total de uma conta com Write Sharding, não basta ler um item. É preciso fazer N leituras (uma para cada shard) e somar os resultados na aplicação. Isso aumenta a **latência** e o **custo** da operação de leitura de saldo.

**Conclusão:** Write Sharding é uma técnica poderosa para escalar a **escrita** em contas de altíssimo volume, mas o preço a se pagar é uma maior complexidade e uma performance de **leitura** degradada. É um trade-off clássico em arquitetura de sistemas distribuídos.
""")
