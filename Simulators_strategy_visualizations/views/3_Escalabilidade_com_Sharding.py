import streamlit as st
import graphviz
import random
import pandas as pd


# --- Estado da Simulação ---
def inicializar_estado():
    if 'shards' not in st.session_state:
        st.session_state.shards = [{"id": i, "wcu": 0, "requests": []} for i in range(10)]
    if 'log' not in st.session_state:
        st.session_state.log = ["Simulação iniciada."]
    if 'total_requests' not in st.session_state:
        st.session_state.total_requests = 0
    if 'throttled_requests' not in st.session_state:
        st.session_state.throttled_requests = 0
    if 'strategy' not in st.session_state:
        st.session_state.strategy = "Single Partition"

def reset_simulation():
    st.session_state.shards = [{"id": i, "wcu": 0, "requests": []} for i in range(10)]
    st.session_state.log = ["Simulação reiniciada."]
    st.session_state.total_requests = 0
    st.session_state.throttled_requests = 0
    # O widget de estratégia (key='strategy') já foi instanciado neste run, então não dá
    # pra reatribuir st.session_state.strategy aqui diretamente (StreamlitAPIException).
    # Em vez disso, marcamos um flag e aplicamos o reset no topo do script, antes do
    # widget ser recriado no próximo rerun.
    st.session_state._reset_strategy_pending = True

# --- Lógica da Simulação ---
def run_simulation(strategy, tps):
    st.session_state.total_requests += tps
    log_entry = ""
    
    if strategy == "Single Partition":
        shard = st.session_state.shards[0]
        if shard['wcu'] + tps > 1000:
            accepted_tps = max(0, 1000 - shard['wcu'])
            throttled_tps = tps - accepted_tps
            st.session_state.throttled_requests += throttled_tps
            shard['wcu'] = 1000
            for _ in range(accepted_tps):
                shard['requests'].append(1)
            log_entry = f"THROTTLING: {throttled_tps} reqs rejeitadas. Partição 0 no limite."
        else:
            shard['wcu'] += tps
            for _ in range(tps):
                shard['requests'].append(1)
            log_entry = f"OK: {tps} reqs aceitas no Shard 0."
    
    else: # Write Sharding
        for _ in range(tps):
            target_shard_index = random.randint(0, 9)
            shard = st.session_state.shards[target_shard_index]
            shard['wcu'] += 1
            shard['requests'].append(1)
        log_entry = f"OK: {tps} reqs distribuídas aleatoriamente entre 10 shards."
    
    st.session_state.log.insert(0, log_entry)

# --- Funções de Visualização ---
def create_graph(shards, strategy, tps):
    dot = graphviz.Digraph('Sharding', comment='Sharding Simulation')
    dot.attr('graph', rankdir='TB', splines='ortho', label=f'Estratégia: {strategy} | Carga: {tps} TPS', fontname="Arial", fontsize="14")
    dot.attr('node', shape='box', style='rounded,filled', fontname="Arial", fontsize="10")

    with dot.subgraph(name='cluster_requests') as c:
        c.attr(label='', color='white')
        tx_id = f"tx_batch"
        c.node(tx_id, f"Lote de {tps} Requisições", shape='ellipse', fillcolor='lightblue')
        
        # Lógica de visualização das setas
        if strategy == "Single Partition":
            dot.edge(tx_id, f"shard_0", style='dashed', label='Todas para o mesmo destino')
        else: # Write Sharding - Mostra múltiplas setas para ilustrar distribuição
            num_arrows = min(tps // 500, 3) if tps > 500 else 1
            for i in range(num_arrows):
                dot.edge(tx_id, f"shard_{random.randint(0,9)}", style='dashed', label='Distribuindo...' if i==0 else '')

    with dot.subgraph(name='cluster_shards') as c:
        c.attr(label='Partições Físicas no Banco de Dados', style='dashed', fontname="Arial", fontsize="12")
        for i, shard in enumerate(shards):
            wcu = shard['wcu']
            req_count = len(shard['requests'])
            hot = wcu >= 1000
            
            if strategy == "Single Partition" and i == 0:
                pk = "PK: CONTA-123"
                color = 'salmon' if hot else 'lightgrey'
                label = f"Shard {i}\n({pk})\nWCU: {wcu}\nReqs: {req_count}"
                if hot: label += "\nHOT PARTITION"
            elif strategy == "Single Partition" and i > 0:
                color = 'whitesmoke'
                label = f"Shard {i}\n(Inativo)"
            else: # Write Sharding
                pk = "PK: CONTA-123#..."
                color = 'lightgreen'
                label = f"Shard {i}\n({pk})\nWCU: {wcu}\nReqs: {req_count}"

            c.node(f"shard_{i}", label, fillcolor=color)
            
    return dot

# --- UI ---
inicializar_estado()

if st.session_state.get("_reset_strategy_pending"):
    st.session_state.strategy = "Single Partition"
    st.session_state._reset_strategy_pending = False

st.title("Estudo de Caso 3: Sharding e o Problema da 'Hot Partition'")
st.markdown("---")
st.markdown("""
### Resumo
Este experimento simula um problema comum em bancos de dados NoSQL como o DynamoDB: quando todas as escritas de uma conta de altíssimo volume ("hot account") vão para a mesma chave de partição, essa partição física tem um limite de capacidade (WCU/s) que pode ser excedido, causando **throttling** (rejeição de requisições). A estratégia de **Write Sharding** resolve isso distribuindo as escritas dessa mesma conta lógica entre múltiplas partições físicas, usando um sufixo aleatório na chave de partição.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Painel de Controle")
    strategy = st.radio(
        "Estratégia de Chave de Partição",
        ("Single Partition", "Write Sharding"),
        key='strategy',
        help="Single Partition: PK='CONTA-123'. Write Sharding: PK='CONTA-123#sufixo_aleatorio'."
    )
    tps = st.slider("Carga de Escrita (Requisições por Segundo)", 100, 5000, 1000, 100)
    
    if st.button("Executar Simulação (1 segundo)"):
        run_simulation(strategy, tps)

    if st.button("Reiniciar Simulação"):
        reset_simulation()
        st.rerun()

    st.subheader("Métricas de Desempenho")
    if st.session_state.total_requests > 0:
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Requisições Totais", f"{st.session_state.total_requests}")
        kpi2.metric("Falhas (Throttling)", f"{st.session_state.throttled_requests}", delta=f"{st.session_state.throttled_requests/st.session_state.total_requests:.1%}" if st.session_state.throttled_requests > 0 else None, delta_color="inverse")
    else:
        st.info("Execute a simulação para ver as métricas.")

    st.subheader("Log de Eventos")
    st.code('\n'.join(st.session_state.log[:10]), language='text')

with col2:
    st.header("Visualização da Distribuição de Carga")
    st.graphviz_chart(create_graph(st.session_state.shards, st.session_state.strategy, tps))
    
    st.subheader("Consumo de WCU (Write Capacity Units) por Partição")
    chart_data = pd.DataFrame({
        "Shard": [f"Shard {s['id']}" for s in st.session_state.shards],
        "WCU Consumido": [s['wcu'] for s in st.session_state.shards]
    }).set_index("Shard")
    st.bar_chart(chart_data)

st.markdown("---")
st.header("Análise e Conclusões")
st.markdown("""
**Observação Empírica:**
-   **Modo "Single Partition":** Toda a carga é direcionada ao `Shard 0`. Quando a carga (TPS) ultrapassa a capacidade da partição (1000 WCU/s no DynamoDB), o banco de dados começa a rejeitar requisições (**Throttling**), resultando em falhas. O sistema não escala.
-   **Modo "Write Sharding":** Ao adicionar um sufixo aleatório à chave de partição, as requisições para a mesma conta lógica são distribuídas entre múltiplas partições físicas. A carga é balanceada, e o sistema como um todo pode absorver um volume de escritas muito maior, limitado apenas pelo número total de shards.

**Trade-off: A Complexidade da Leitura**
A grande desvantagem do Write Sharding é que a leitura do saldo total se torna uma operação complexa e cara. Para saber o saldo da `CONTA-123`, a aplicação precisa consultar **todos os 10 shards** e somar os resultados, um padrão conhecido como **Scatter-Gather**.
""")

st.subheader("Case de Mercado: A 'Camada Zero' e o 'Shadow Ledger' do Itaú")
st.markdown("""
A arquitetura de desacoplamento e uso de um banco de dados NoSQL para alta performance não é apenas teórica. Em palestras, a engenharia do Itaú descreveu sua **"Camada Zero"**, uma arquitetura de "shadow ledger" criada para suportar o volume do Pix.
- **O Problema:** O sistema de core bancário (Mainframe) não foi projetado para a disponibilidade 24/7 e o volume de TPS do Pix.
- **A Solução:** Eles criaram uma camada de microsserviços na AWS que recebe as transações do Pix. O saldo autoritativo para o canal digital passou a residir em um banco de dados NoSQL altamente escalável. Este "ledger sombra" processa as transações em tempo real usando padrões como o Write Sharding.
- **Consistência Eventual:** O Mainframe é então atualizado de forma assíncrona, em lote, para fins contábeis e regulatórios.
Isto valida a abordagem de usar a ferramenta certa para o trabalho certo: um sistema de altíssima performance para o tempo real e o sistema legado para a contabilidade em batch.
""")

st.markdown("---")
st.subheader("Referências e Leitura Adicional")
st.markdown("""
- **DeCandia, G., et al. (2007).** "Dynamo: Amazon's Highly Available Key-value Store". *Symposium on Operating Systems Principles (SOSP)*.
- **AWS Documentation & Itaú Engineering Blogs.** "Choosing the Right Partition Key", "Write Sharding for Hot Partitions", e "Cell-Based Architecture".
""")