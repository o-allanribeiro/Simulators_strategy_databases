import streamlit as st
import graphviz
import random
import time
import pandas as pd
import hashlib

st.set_page_config(layout="wide", page_title="Estudo de Caso 3: Escalabilidade com Write Sharding")

# --- Funções do Estado da Simulação ---
def inicializar_estado_sharding():
    # Estado para a Simulação 1 (DynamoDB)
    if 'shards_dynamo' not in st.session_state:
        st.session_state.shards_dynamo = [{"id": i, "wcu": 0} for i in range(10)]
    if 'log_dynamo' not in st.session_state:
        st.session_state.log_dynamo = ["Simulação DynamoDB iniciada."]
    if 'total_requests_dynamo' not in st.session_state:
        st.session_state.total_requests_dynamo = 0
    if 'throttled_requests_dynamo' not in st.session_state:
        st.session_state.throttled_requests_dynamo = 0

    # Estado para a Simulação 2 (App-Level)
    if 'shards_app' not in st.session_state:
        st.session_state.shards_app = {i: [] for i in range(4)}
    if 'last_account_id_app' not in st.session_state:
        st.session_state.last_account_id_app = None
    if 'last_shard_target_app' not in st.session_state:
        st.session_state.last_shard_target_app = None

def reset_dynamo_simulation():
    st.session_state.shards_dynamo = [{"id": i, "wcu": 0} for i in range(10)]
    st.session_state.log_dynamo = ["Simulação DynamoDB reiniciada."]
    st.session_state.total_requests_dynamo = 0
    st.session_state.throttled_requests_dynamo = 0

def reset_app_shards(num_shards):
    st.session_state.shards_app = {i: [] for i in range(num_shards)}
    st.session_state.last_account_id_app = None
    st.session_state.last_shard_target_app = None

# --- Início da Renderização da Página ---
inicializar_estado_sharding()

st.title("Estudo de Caso 3: Escalabilidade Horizontal com Write Sharding")
st.markdown("---")
st.markdown("""
### Resumo
Quando o volume de escritas para um único registro (uma "conta quente") excede a capacidade de um único servidor, nem o bloqueio pessimista nem o otimista podem resolver o problema. A solução fundamental é a **escalabilidade horizontal**, e a técnica primária para isso é o **Particionamento Horizontal**, ou **Sharding**. Este estudo analisa duas implementações principais de sharding: a nível de banco de dados (modelado pelo DynamoDB) e a nível de aplicação.

**Sharding** é a prática de dividir um grande conjunto de dados em subconjuntos menores e independentes (shards), distribuindo-os por múltiplos servidores. Isso permite que a carga de leitura e escrita seja paralelizada, superando as limitações físicas de um único nó.
""")
st.markdown("---")

# --- Teoria ---
st.header("Fundamentação Teórica: Estratégias de Particionamento")
st.markdown("""
A decisão de *como* distribuir os dados é crítica e determinada pela **chave de sharding** e pela **estratégia de particionamento**.

1.  **Sharding Baseado em Hash (Hash-Based Sharding):**
    -   **Método:** Uma chave de sharding (ex: `ID_da_conta`) é passada por uma função de hash. O resultado do hash determina em qual shard o dado reside. Ex: `shard = hash(ID_da_conta) % N_de_shards`.
    -   **Vantagens:** Distribui os dados de forma muito uniforme, ideal para escalabilidade de escrita.
    -   **Desvantagens:** Torna as consultas por intervalo (range queries) ineficientes, pois os dados sequenciais são espalhados aleatoriamente.
    -   **Caso de Uso:** Ideal para acesso por chave-valor, como "obter o saldo da conta X". Usado por DynamoDB e Cassandra.

2.  **Sharding Baseado em Intervalo (Range-Based Sharding):**
    -   **Método:** Os dados são particionados com base em intervalos contíguos da chave de sharding (ex: Contas 1-1000 no Shard A, 1001-2000 no Shard B).
    -   **Vantagens:** Extremamente eficiente para consultas por intervalo.
    -   **Desvantagens:** Suscetível a hotspots se uma faixa específica (ex: contas recém-criadas) receber a maior parte da carga.
    -   **Caso de Uso:** Sistemas que necessitam de varreduras ordenadas de dados.
""")
st.markdown("---")

# --- Simulação 1: Database-Level Sharding ---
st.header("Estudo de Caso 1: Sharding Gerenciado pelo Banco de Dados (e.g., DynamoDB)")
st.markdown("""
Neste modelo, o banco de dados abstrai a complexidade do sharding. No entanto, se a chave de partição for mal projetada, pode-se criar uma **"Hot Partition"**. Esta simulação demonstra como o padrão **Write Sharding**, que usa uma chave de partição composta (`ID_CONTA#sufixo_aleatorio`), resolve o problema distribuindo a carga.
""")

def run_dynamo_simulation(strategy, tps):
    st.session_state.total_requests_dynamo += tps
    log_entry = ""
    if strategy == "Single Partition":
        shard = st.session_state.shards_dynamo[0]
        if shard['wcu'] + tps > 1000:
            accepted_tps = max(0, 1000 - shard['wcu'])
            throttled_tps = tps - accepted_tps
            st.session_state.throttled_requests_dynamo += throttled_tps
            shard['wcu'] = 1000
            log_entry = f"🔴 Throttling! {throttled_tps} reqs rejeitadas. Partição 0 no limite."
        else:
            shard['wcu'] += tps
            log_entry = f"🟢 {tps} reqs aceitas no Shard 0."
    else: # Write Sharding
        for _ in range(tps):
            target_shard_index = random.randint(0, 9)
            st.session_state.shards_dynamo[target_shard_index]['wcu'] += 1
        log_entry = f"🟢 {tps} reqs distribuídas aleatoriamente entre 10 shards."
    st.session_state.log_dynamo.insert(0, log_entry)

def create_dynamo_graph(shards, strategy):
    dot = graphviz.Digraph()
    dot.attr('graph', rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled')
    with dot.subgraph(name='cluster_shards') as c:
        c.attr(label='Partições Físicas no DynamoDB', style='dashed')
        for i, shard in enumerate(shards):
            wcu = shard['wcu']
            hot = wcu >= 1000
            color = 'salmon' if hot else 'lightgrey'
            pk = f"PK: CONTA-123" if strategy == "Single Partition" else f"PK: CONTA-123#..."
            label = f"Shard {i}\n({pk})\nWCU: {wcu}"
            if hot: label += "\n🔥 HOT PARTITION 🔥"
            c.node(f"shard_{i}", label, fillcolor=color)
    return dot

col_dynamo1, col_dynamo2 = st.columns([1, 2])
with col_dynamo1:
    st.subheader("Painel de Controle (DynamoDB)")
    strategy_dynamo = st.radio("Estratégia de Chave de Partição", ("Single Partition", "Write Sharding (Chave Composta)"))
    tps_dynamo = st.slider("Carga de Escrita (TPS)", 100, 5000, 1000, 100, key="tps_dynamo")
    if st.button("Executar Carga de 1s (DynamoDB)"):
        run_dynamo_simulation(strategy_dynamo, tps_dynamo)
    if st.button("Resetar (DynamoDB)"):
        reset_dynamo_simulation()
        st.rerun()

    st.markdown("**Log de Eventos (DynamoDB)**")
    st.code('\n'.join(st.session_state.log_dynamo[:5]), language='text')

with col_dynamo2:
    st.subheader("Visualização da Carga nos Shards")
    st.graphviz_chart(create_dynamo_graph(st.session_state.shards_dynamo, strategy_dynamo))
    total_wcu = sum(s['wcu'] for s in st.session_state.shards_dynamo)
    if st.session_state.total_requests_dynamo > 0:
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Requisições Totais", f"{st.session_state.total_requests_dynamo}")
        kpi2.metric("Requisições Rejeitadas (Throttling)", f"{st.session_state.throttled_requests_dynamo}", delta=f"{st.session_state.throttled_requests_dynamo/st.session_state.total_requests_dynamo:.1%}", delta_color="inverse")
        chart_data = pd.DataFrame({"Shard": [f"Shard {s['id']}" for s in st.session_state.shards_dynamo], "WCU Consumido": [s['wcu'] for s in st.session_state.shards_dynamo]}).set_index("Shard")
        st.bar_chart(chart_data)
st.markdown("---")

# --- Simulação 2: Application-Level Sharding ---
st.header("Estudo de Caso 2: Sharding Gerenciado pela Aplicação")
st.markdown("""
Neste modelo, a aplicação assume a responsabilidade de rotear as escritas. Ela usa uma função de hash para determinar para qual banco de dados (fisicamente separado) uma escrita deve ser enviada. Isso permite escalar horizontalmente até mesmo bancos de dados relacionais tradicionais.
""")

def simulate_app_write(num_shards):
    account_id = f"acc_{random.randint(10000, 99999)}"
    st.session_state.last_account_id_app = account_id
    hash_object = hashlib.sha1(account_id.encode())
    int_hash = int(hash_object.hexdigest(), 16)
    target_shard = int_hash % num_shards
    st.session_state.last_shard_target_app = target_shard
    if target_shard not in st.session_state.shards_app:
        st.session_state.shards_app[target_shard] = []
    st.session_state.shards_app[target_shard].append(account_id)

def draw_app_sharding_projection(num_shards, account_id_str, target_shard):
    dot = graphviz.Digraph()
    dot.attr('graph', rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled')
    dot.node('app_router', 'App Router\n(Lógica de Sharding)', shape='doublecircle', fillcolor='lightblue')
    if account_id_str:
        formula = f"shard = hash('{account_id_str}') % {num_shards} = {target_shard}"
        dot.node('hash_calc', formula, shape='plaintext')
        dot.edge('app_router', 'hash_calc', style='dashed', arrowhead='none')
    with dot.subgraph(name='cluster_shards_app') as c:
        c.attr(label="Cluster de Bancos de Dados Independentes", style='dashed')
        for i in range(num_shards):
            label = f"Shard #{i}\n(e.g., PostgreSQL instance)"
            fillcolor = "lightgreen" if i == target_shard else "lightgrey"
            c.node(f'shard_app_{i}', label, shape='folder', height='1.5', fillcolor=fillcolor)
    if account_id_str is not None and target_shard is not None:
         dot.edge('hash_calc', f'shard_app_{target_shard}', label=f"Roteia escrita")
    return dot

col_app1, col_app2 = st.columns([1, 2])
with col_app1:
    st.subheader("Painel de Controle (App-Level)")
    num_shards_app = st.slider("Número de Shards no Cluster", 2, 16, 4, key='num_shards_app')
    if len(st.session_state.shards_app) != num_shards_app:
        reset_app_shards(num_shards_app)
    if st.button("Simular Nova Escrita (App-Level)"):
        simulate_app_write(num_shards_app)
    if st.button("Resetar Cluster (App-Level)"):
        reset_app_shards(num_shards_app)
        st.rerun()

with col_app2:
    st.subheader("Visualização do Roteamento")
    st.graphviz_chart(draw_app_sharding_projection(num_shards_app, st.session_state.last_account_id_app, st.session_state.last_shard_target_app))
    if st.session_state.last_account_id_app:
        st.success(f"A conta **{st.session_state.last_account_id_app}** foi roteada para o **Shard #{st.session_state.last_shard_target_app}**.")

st.markdown("---")
st.header("Análise Comparativa e Conclusões")

st.subheader("Case de Mercado: A 'Camada Zero' e o 'Shadow Ledger' do Itaú")
st.markdown("""
A arquitetura de desacoplamento e uso de um banco de dados NoSQL para alta performance não é apenas teórica. Em palestras no AWS re:Invent, a equipe de engenharia do Itaú descreveu sua **"Camada Zero"**, uma arquitetura de "shadow ledger" criada para suportar o volume do Pix.
- **O Problema:** O sistema de core bancário (Mainframe) não foi projetado para a disponibilidade 24/7 e o volume de TPS do Pix.
- **A Solução:** Eles criaram uma camada de microsserviços na AWS que recebe as transações do Pix. O saldo autoritativo para o canal digital passou a residir em um banco de dados NoSQL altamente escalável (similar ao DynamoDB em conceito). Este "ledger sombra" processa as transações em tempo real.
- **Consistência Eventual:** O Mainframe é então atualizado de forma assíncrona, em lote, para fins contábeis e regulatórios.
Isto valida a abordagem de usar a ferramenta certa para o trabalho certo: um sistema de altíssima performance para o tempo real e o sistema legado para a contabilidade em batch, conectados por consistência eventual.
""")


st.markdown("""
| Critério | Sharding no BD (DynamoDB) | Sharding na Aplicação |
| :--- | :--- | :--- |
| **Escalabilidade de Escrita** | Excelente, gerenciada pela nuvem. | Excelente, limitada pelo número de nós do cluster. |
| **Complexidade Operacional** | **Baixa.** O provedor de nuvem gerencia o sharding, o rebalanceamento e a manutenção. | **Alta.** A equipe de desenvolvimento é responsável por provisionar, manter, monitorar e rebalancear o cluster. |
| **Consultas de Leitura** | **Complexas para saldo total.** Requerem `Scatter-Gather` se a escrita for distribuída, aumentando custo e latência. | **Complexas para saldo total.** Também requerem `Scatter-Gather` implementado na aplicação. |
| **Transações Cross-Shard** | Geralmente limitadas ou não suportadas atomicamente. | Extremamente complexas. Requerem padrões como Saga ou Two-Phase Commit, que aumentam muito a complexidade do código. |
| **Flexibilidade** | Menor. Preso às primitivas do banco de dados (ex: chaves de partição do DynamoDB). | Maior. A aplicação pode implementar qualquer lógica de roteamento e pode, teoricamente, usar diferentes tipos de banco de dados. |

**Conclusão:** Sharding é uma ferramenta poderosa e essencial para a escalabilidade massiva de escrita. **Sharding gerenciado pelo banco de dados** (como no DynamoDB) oferece uma solução com menor sobrecarga operacional, ideal para muitas cargas de trabalho. **Sharding a nível de aplicação** oferece flexibilidade máxima, mas a um custo significativamente maior de complexidade de desenvolvimento e manutenção. A escolha depende do nível de controle desejado versus o custo operacional que a equipe está disposta a arcar.
""")

st.markdown("---")
st.subheader("Referências e Leitura Adicional")
st.markdown("""
- **DeCandia, G., et al. (2007).** "Dynamo: Amazon's Highly Available Key-value Store". *Symposium on Operating Systems Principles (SOSP)*.
- **Corbett, J. C., et al. (2012).** "Spanner: Google's Globally-Distributed Database". *Symposium on Operating Systems Design and Implementation (OSDI)*.
- **AWS Documentation & Itaú Engineering Blogs.** "Choosing the Right Partition Key" & "Cell-Based Architecture".
""")
