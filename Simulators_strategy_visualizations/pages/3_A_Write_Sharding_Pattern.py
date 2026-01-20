import streamlit as st
import graphviz
import random
import hashlib

st.set_page_config(layout="wide", page_title="Padrão: Write Sharding")

# --- Estado da Simulação ---
if 'shards_data' not in st.session_state:
    st.session_state.shards_data = {}
if 'last_account_id' not in st.session_state:
    st.session_state.last_account_id = None
if 'last_shard_target' not in st.session_state:
    st.session_state.last_shard_target = None

def reset_shards(num_shards):
    st.session_state.shards_data = {i: [] for i in range(num_shards)}
    st.session_state.last_account_id = None
    st.session_state.last_shard_target = None

# --- Funções de Visualização ---
def draw_sharding_projection(num_shards, account_id_str, target_shard):
    dot = graphviz.Digraph('WriteSharding', comment='Application-Level Write Sharding')
    dot.attr('graph', rankdir='TB', splines='spline', label="Projeção de Armazenamento com Write Sharding", labelloc="t", fontsize="16")
    dot.attr('node', shape='box', style='rounded,filled')

    # Nó da Aplicação/Roteador
    dot.node('app_router', 'App Router\n(Lógica de Sharding)', shape='doublecircle', fillcolor='lightblue')
    
    if account_id_str:
        # Mostra o cálculo do hash
        hash_object = hashlib.sha1(account_id_str.encode())
        hex_dig = hash_object.hexdigest()
        int_hash = int(hex_dig, 16)
        
        formula = f"shard = hash({account_id_str}) % {num_shards}\nshard = {int_hash % num_shards}"
        dot.node('hash_calc', formula, shape='plaintext')
        dot.edge('app_router', 'hash_calc', style='dashed', arrowhead='none')


    # Cluster dos Shards de Banco de Dados
    with dot.subgraph(name='cluster_shards') as c:
        c.attr(label="Cluster de Banco de Dados (Ex: Múltiplos PostgreSQL)", style="dashed")
        for i in range(num_shards):
            shard_data = st.session_state.shards_data.get(i, [])
            
            # Formata a lista de contas para exibição
            accounts_display = '\n'.join(shard_data[-5:]) # Mostra apenas as últimas 5 contas
            if len(shard_data) > 5:
                accounts_display = '...\n' + accounts_display
            
            label = f"Shard #{i}\n\nContas Armazenadas:\n{accounts_display}"
            
            fillcolor = "lightgreen" if i == target_shard else "lightgrey"
            c.node(f'shard_{i}', label, shape='folder', height='2', fillcolor=fillcolor)

    if account_id_str is not None and target_shard is not None:
         dot.edge('hash_calc', f'shard_{target_shard}', label=f"Roteia escrita para\nconta '{account_id_str}'")

    return dot

# --- Lógica da Simulação ---
def simulate_write(num_shards):
    # Gera um ID de conta aleatório
    account_id = f"acc_{random.randint(10000, 99999)}"
    st.session_state.last_account_id = account_id
    
    # Lógica de Sharding: hash(account_id) % num_shards
    hash_object = hashlib.sha1(account_id.encode())
    int_hash = int(hash_object.hexdigest(), 16)
    target_shard = int_hash % num_shards
    st.session_state.last_shard_target = target_shard

    # "Armazena" a conta no shard correto
    if target_shard not in st.session_state.shards_data:
        st.session_state.shards_data[target_shard] = []
    st.session_state.shards_data[target_shard].append(account_id)


# --- UI ---
st.title("Modelo 'C': Padrão de Write Sharding")
st.markdown("""
Esta simulação demonstra o padrão de **Write Sharding no nível da aplicação**. Em vez de depender de um recurso nativo do banco de dados (como no DynamoDB), a própria aplicação contém a lógica para distribuir as escritas entre múltiplos bancos de dados independentes (ou tabelas).
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Painel de Controle")
    num_shards = st.slider(
        "Número de Shards no Cluster",
        min_value=2,
        max_value=16,
        value=4,
        key='num_shards',
        help="Simula o número de bancos de dados independentes no nosso cluster."
    )
    
    if st.session_state.shards_data.get(0) is None or len(st.session_state.shards_data) != num_shards:
        reset_shards(num_shards)

    if st.button("Simular Nova Escrita (Conta Aleatória)"):
        simulate_write(num_shards)

    if st.button("Reiniciar Cluster"):
        reset_shards(num_shards)
        st.rerun()

    st.subheader("Análise do Padrão")
    st.markdown("""
    **Como Funciona:**
    1.  A aplicação recebe uma requisição (ex: criar uma nova conta).
    2.  Ela aplica uma **função de sharding** determinística sobre uma **chave de sharding** (geralmente o ID da conta ou do cliente).
    3.  A fórmula `shard = hash(chave) % numero_de_shards` decide em qual banco de dados a escrita deve ser direcionada.
    4.  A aplicação então abre uma conexão com o banco de dados correto e executa a transação.
    
    **Vantagens:**
    - **Escalabilidade Massiva de Escrita:** Permite que sistemas relacionais como PostgreSQL ou MySQL escalem horizontalmente para escrita, superando o gargalo de um nó único.
    - **Isolamento de Falha:** Uma falha em um shard geralmente não afeta os outros.

    **Desvantagens:**
    - **Complexidade na Aplicação:** A lógica de roteamento agora vive na sua aplicação, tornando-a mais complexa.
    - **Consultas Cross-Shard:** Obter dados de múltiplos shards é difícil e lento (ex: "listen todas as contas com saldo > X"). Requer uma abordagem de *Scatter-Gather*.
    - **Transações Distribuídas:** Transações que precisam tocar em múltiplos shards (ex: transferir dinheiro entre contas em shards diferentes) são extremamente complexas de se fazer de forma atômica (requerem SAGA, Two-Phase Commit, etc.).
    - **Re-sharding:** Adicionar ou remover shards do cluster é uma operação complexa e arriscada que exige a movimentação de dados.
    """)

with col2:
    st.header("Gráfico de Projeção do Armazenamento")
    
    st.graphviz_chart(
        draw_sharding_projection(
            num_shards,
            st.session_state.last_account_id,
            st.session_state.last_shard_target
        )
    )

    if st.session_state.last_account_id:
        st.success(f"A conta **{st.session_state.last_account_id}** foi roteada e armazenada no **Shard #{st.session_state.last_shard_target}**.")
    else:
        st.info("Clique em 'Simular Nova Escrita' para ver o roteamento em ação.")
