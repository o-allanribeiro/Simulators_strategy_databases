import streamlit as st
import graphviz
import random
import time
from collections import deque
import uuid
import json

st.set_page_config(layout="wide", page_title="Dashboard de Simulação de DB")

# --- 1. ESTADO DA SIMULAÇÃO (Session State) ---
def get_default_state():
    return {
        "simulation_metadata": {"event_id": "evt_000", "timestamp": time.time(), "trigger": "INIT"},
        "business_state": {
            "account_id": "acc_12345678",
            "balance_view": {
                "pockets": {
                    "book_balance": 1000.0,
                    "blocked_judicial": 0.0,
                    "provisioned_cards": 0.0,
                    "overdraft_limit": 500.0
                }
            }
        },
        "logic_process": {},
        "dynamo_physical_layer": {
            "strategy": "SINGLE_PARTITION",
            "sharding_config": {"total_shards": 10},
            "shards": [{"id": i, "balance": 0.0, "wcu_load": 0} for i in range(10)]
        }
    }

if 'sim_state' not in st.session_state:
    st.session_state.sim_state = get_default_state()
    st.session_state.event_log = deque(maxlen=20)

def log_event(message, level="INFO"):
    st.session_state.event_log.appendleft(f"[{level}] {time.strftime('%H:%M:%S')} - {message}")

# --- 2. PAINEL DE CONTROLE (Lado Esquerdo) ---
with st.sidebar:
    st.header("🔬 Painel de Controle")
    
    engine = st.selectbox("1. Motor do Banco de Dados:", ("Aurora/PostgreSQL (Pessimista)", "DynamoDB (Otimista)"), key='db_engine')
    
    st.subheader("2. Parâmetros de Carga")
    tps = st.slider("Intensidade (Requisições/s)", 10, 10000, 100)
    
    if "DynamoDB" in engine:
        st.session_state.sim_state['dynamo_physical_layer']['strategy'] = st.radio(
            "Estratégia de Sharding:",
            ("SINGLE_PARTITION", "WRITE_SHARDING"),
            key='sharding_strategy'
        )

    st.subheader("3. Injetar Eventos")
    if st.button("💸 PIX Crédito (10x reqs)"):
        for _ in range(10):
            # Lógica de Crédito
            state = st.session_state.sim_state
            if state['dynamo_physical_layer']['strategy'] == "WRITE_SHARDING":
                target_shard_index = random.randint(0, state['dynamo_physical_layer']['sharding_config']['total_shards'] - 1)
                state['dynamo_physical_layer']['shards'][target_shard_index]['balance'] += 50
                log_event(f"PIX Crédito de R$50 creditado no Shard #{target_shard_index}", "SUCCESS")
            else: # Single Partition
                state['business_state']['balance_view']['pockets']['book_balance'] += 50
                log_event("PIX Crédito de R$50 creditado na Partição Única", "SUCCESS")

    if st.button("Consultar Saldo"):
        log_event("Iniciando consulta de saldo (Scatter-Gather se aplicável)...", "WARNING")
        # A lógica de visualização lidará com a animação

# --- Lógica de Simulação de Hot Partition ---
if st.session_state.db_engine == "DynamoDB (Otimista)" and st.session_state.sharding_strategy == "SINGLE_PARTITION":
    if tps > 1000:
        st.session_state.hot_partition_warning = True
        log_event(f"ALERTA DE HOT PARTITION! Carga de {tps} TPS excede o limite de 1000 WCUs.", "ERROR")
    else:
        st.session_state.hot_partition_warning = False

# --- 3. LAYOUT PRINCIPAL ---
st.title("Dashboard de Simulação de Sistemas de Banco de Dados")

# Modelo Conceitual
pockets = st.session_state.sim_state['business_state']['balance_view']['pockets']
total_sharded_balance = sum(s['balance'] for s in st.session_state.sim_state['dynamo_physical_layer']['shards'])
book_balance = pockets['book_balance'] + total_sharded_balance
available_liquidity = book_balance - pockets['blocked_judicial'] - pockets['provisioned_cards'] + pockets['overdraft_limit']

st.subheader("Etapa 1: Modelo Conceitual (Pockets de Saldo)")
col1, col2, col3 = st.columns(3)
col1.metric("Contábil (Total)", f"R$ {book_balance:.2f}")
col2.metric("Disponível (Liquidez)", f"R$ {available_liquidity:.2f}")
col3.metric("🔴 Travas (Judicial+Prov)", f"R$ {pockets['blocked_judicial'] + pockets['provisioned_cards']:.2f}")

st.divider()

# Modelo Lógico e Físico
col_logic, col_physic = st.columns([1, 2])
with col_logic:
    st.subheader("Etapa 2: Modelo Lógico")
    st.write("Fila de Requisições, Regras de Negócio (em construção)...")
    st.json(st.session_state.sim_state)

with col_physic:
    st.subheader(f"Etapa 3: Modelo Físico (Motor: {engine})")
    
    # --- MOTOR B: DYNAMODB ---
    if "DynamoDB" in engine:
        strategy = st.session_state.sharding_strategy
        dot = graphviz.Digraph('DynamoDB')
        dot.attr('graph', rankdir='TB', splines='ortho')
        dot.node('app', 'Aplicação', shape='server')

        if strategy == "SINGLE_PARTITION":
            is_hot = st.session_state.get('hot_partition_warning', False)
            color = "red" if is_hot else "lightblue"
            label = "Partição Única\n(PK: ACC#123)"
            if is_hot:
                label += f"\nTHROTTLING! (Carga: {tps} TPS)"
                dot.node('throttling', '💥 ConditionalCheckFailedException\n💥 ThrottlingException', shape='plaintext', fontcolor='red')

            dot.node('shard_0', label, shape='box3d', style='filled', fillcolor=color)
            
            # Simulação de Race Condition (limitado a 5 para UI)
            reqs = min(tps // 100, 5)
            if reqs > 1:
                winner = random.randint(0, reqs - 1)
                for i in range(reqs):
                    if i == winner:
                        dot.edge('app', 'shard_0', label=f'Thread {i+1}\nSUCESSO (CAS)', color='green')
                    else:
                        dot.edge('app', 'shard_0', label=f'Thread {i+1}\nFALHA (CAS)', color='red', style='dashed')
        
        elif strategy == "WRITE_SHARDING":
            num_shards = st.session_state.sim_state['dynamo_physical_layer']['sharding_config']['total_shards']
            with dot.subgraph(name='cluster_shards') as c:
                c.attr(label=f"Write Sharding Ativo ({num_shards} cofres)")
                c.node_attr.update(shape='box3d', style='filled', fillcolor='lightblue')
                for i in range(num_shards):
                    c.node(f'shard_{i}', f"Cofre #{i}\n(PK: ACC#123#s{i})")
            
            # Simulação de Scatter
            dot.edge('app', 'shard_4', label='hash(TXN_ID) -> Shard 4') # Exemplo estático
            dot.edge('app', 'shard_7', label='hash(TXN_ID) -> Shard 7')
            dot.edge('app', 'shard_1', label='hash(TXN_ID) -> Shard 1')
            st.caption("As requisições são distribuídas (scatter), evitando Hot Partitions.")

        st.graphviz_chart(dot)

    # --- MOTOR A: POSTGRESQL ---
    else: 
        st.info("Visualização para PostgreSQL (Pessimista) em construção.")

st.divider()

# LOG DE EVENTOS
st.subheader("Log de Eventos da Simulação")
log_container = st.container(height=300)
for event in st.session_state.event_log:
    # ... (lógica de cores do log)
    log_container.info(event)
