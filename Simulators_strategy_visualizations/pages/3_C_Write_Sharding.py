import streamlit as st
import graphviz
import random

st.set_page_config(layout="wide", page_title="Cenário C: Sharding de Saldo")

def generate_write_sharding_graph(transactions, num_shards, read_mode=False):
    # ... (O resto da função de geração de gráfico permanece o mesmo)
    dot = graphviz.Digraph('WriteSharding', comment='The Multiple Coffers')
    dot.attr('graph', rankdir='TB')

    with dot.subgraph(name='cluster_transactions') as c:
        c.attr(label='Transações de Crédito (PIX)', style='dashed')
        for i in range(transactions):
            c.node(f'tx_{i}', f'PIX {i+1}', shape='box', style='rounded')

    with dot.subgraph(name='cluster_shards') as c:
        c.attr(label='Saldo da Conta "Baleia" (Distribuído em Cofres/Shards)', style='filled', color='lightblue')
        c.node_attr.update(shape='box', style='filled', fillcolor='lightyellow')
        for i in range(num_shards):
            c.node(f'shard_{i}', f"Cofre {i+1}\n(Shard)")
    
    if not read_mode:
        for i in range(transactions):
            target_shard = random.randint(0, num_shards - 1)
            dot.edge(f'tx_{i}', f'shard_{target_shard}', label=f'Hash(PIX ID) -> Shard')
    
    if read_mode:
        dot.node('app', 'Aplicação\n(Consulta Saldo)', shape='box', style='filled', fillcolor='lightgreen')
        dot.node('total', 'Saldo Total = Σ (Cofres)', shape='box', style='filled', fillcolor='orange')
        dot.edge('app', 'total', label='Soma na App')
        for i in range(num_shards):
            dot.edge(f'shard_{i}', 'app', label=f'Lê Saldo Parcial', style='dashed', dir='back')

    return dot

def render_write_sharding_page():
    st.title("Cenário C: Sharding de Saldo (Write Sharding)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        num_transactions = st.slider("Transações PIX Crédito Simultâneas", 1, 50, 5)
        num_shards = st.slider("Número de Cofres (Shards)", 2, 20, 4)
        
        st.header("Selecione a Operação")
        operation = st.radio("", ("Escrever Créditos (Scatter)", "Ler Saldo Total (Gather)"))
        
    with col2:
        st.header("Visualização do 'Motor'")
        read_mode = (operation == "Ler Saldo Total (Gather)")
        
        if not read_mode:
            st.info("Simulando a **escrita** de créditos. Cada PIX é enviado para um cofre/shard diferente, permitindo processamento massivamente paralelo.")
        else:
            st.warning("Simulando a **leitura** do saldo. A aplicação precisa consultar **todos** os cofres e somar os resultados. A leitura é mais lenta e cara.")

        graph = generate_write_sharding_graph(num_transactions, num_shards, read_mode)
        st.graphviz_chart(graph)
            
    st.header("Análise Teórica no Contexto PIX")
    st.markdown("""
    **O Problema:** A conta de um grande varejista precisa receber dezenas de milhares de **PIX Crédito** por segundo. As abordagens que operam em um único registro de saldo (Cenários A e B) não escalam, pois atingem o limite de escrita de uma única partição (*Hot Partition*).

    **A Solução (Write Sharding):** A conta é dividida em N "cofres" (shards) para escalar a escrita.
    - **PIX Crédito (Scatter):** Cada PIX é adicionado a um dos N cofres, escolhido por um hash do ID da transação. Isso permite que N escritas ocorram em paralelo, sem conflitos.
    - **PIX Débito (O Desafio do Gather):** Para autorizar um débito, é preciso saber o saldo total. Isso exige ler todos os N cofres e somar os valores na aplicação, uma operação lenta e cara. A execução do débito em si é ainda mais complexa (de qual cofre debitar?), geralmente exigindo um processo de consolidação assíncrono.
    """)

    st.header("Disrupção Matemática e Estrutura de Dados")
    
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Análise Matemática")
        st.markdown("**Taxa de Escrita (Throughput):**")
        st.latex(r'''
        TPS_{escrita\_total} \approx TPS_{shard} \times N_{shards}
        ''')