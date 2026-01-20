import streamlit as st
import graphviz
import random

st.set_page_config(layout="wide", page_title="Cenário C: Sharding de Saldo")

# --- Funções de Simulação e Visualização ---
def generate_write_sharding_graph(transactions, num_shards, read_mode=False):
    dot = graphviz.Digraph('WriteSharding', comment='The Multiple Coffers')
    dot.attr('graph', rankdir='TB')

    # --- Transações de Entrada ---
    with dot.subgraph(name='cluster_transactions') as c:
        c.attr(label='Transações de Crédito (PIX)', style='dashed')
        for i in range(transactions):
            c.node(f'tx_{i}', f'TXN {i+1}', shape='box', style='rounded')

    # --- Cofres (Shards) ---
    with dot.subgraph(name='cluster_shards') as c:
        c.attr(label='Saldo da Conta "Baleia" (Distribuído em Cofres/Shards)', style='filled', color='lightblue')
        c.node_attr.update(shape='box', style='filled', fillcolor='lightyellow')
        for i in range(num_shards):
            c.node(f'shard_{i}', f"Cofre {i+1}\nSaldo Parcial: ???")
    
    # --- Lógica de Distribuição (Scatter) ---
    if not read_mode:
        for i in range(transactions):
            target_shard = random.randint(0, num_shards - 1)
            dot.edge(f'tx_{i}', f'shard_{target_shard}', label=f'Hash(TXN ID) -> {target_shard}')
    
    # --- Lógica de Leitura (Gather) ---
    if read_mode:
        dot.node('app', 'Aplicação\n(Ver Saldo)', shape='box', style='filled', fillcolor='lightgreen')
        dot.node('total', 'Saldo Total = Σ (Cofres)', shape='box', style='filled', fillcolor='orange')
        dot.edge('app', 'total', label='Soma')
        for i in range(num_shards):
            dot.edge(f'shard_{i}', 'app', label=f'Lê Saldo Parcial', style='dashed', dir='back')

    return dot

# --- Interface do Streamlit ---
def render_write_sharding_page():
    st.title("Cenário C: Sharding de Saldo (Write Sharding)")
    st.image("https://i.imgur.com/v1nL0kF.png", caption="Visualização: Os Múltiplos Cofres (Scatter-Gather)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        num_transactions = st.slider("Transações de Crédito Simultâneas", 1, 20, 5)
        num_shards = st.slider("Número de Cofres (Shards)", 2, 20, 4)
        
        st.header("Selecione a Operação")
        operation = st.radio("", ("Escrever (Scatter)", "Ler Saldo (Gather)"))
        
    with col2:
        st.header("Visualização do 'Motor'")

        read_mode = (operation == "Ler Saldo (Gather)")
        
        if not read_mode:
            st.info("Simulando a **escrita** paralela. Cada transação é enviada para um cofre aleatório, permitindo que todas sejam processadas ao mesmo tempo sem conflito.")
        else:
            st.warning("Simulando a **leitura**. Para obter o saldo total, o sistema precisa consultar **todos** os cofres e somar os resultados. A leitura é mais lenta e cara, mas a escrita é extremamente rápida.")

        graph = generate_write_sharding_graph(num_transactions, num_shards, read_mode)
        st.graphviz_chart(graph)
            
    st.header("Análise Teórica")
    st.markdown("""
    **O Problema:** Uma única conta (uma *Hot Partition*) se torna um gargalo. Mesmo com o bloqueio otimista do DynamoDB, há um limite físico de quantas transações uma única partição/servidor pode aguentar (cerca de 1000 escritas por segundo). Como escalar além disso para contas "baleia" (ex: a conta de um grande marketplace)?

    **A Solução (Write Sharding):** Em vez de armazenar o saldo total em um único registro, nós o quebramos em múltiplos "cofres" ou "shards".

    - **O que a visualização mostra:**
        - **Escrita (Scatter):** Quando uma transação de crédito chega, em vez de atualizar um saldo central, o sistema adiciona o valor a um dos N cofres, escolhido aleatoriamente (ou por um hash do ID da transação). Isso permite que N escritas ocorram em paralelo, pois elas estão operando em registros diferentes.
        - **Leitura (Gather):** Para saber o saldo total, o sistema precisa fazer N leituras (uma para cada cofre) e somar os resultados na aplicação.
    - **Trade-offs:**
        - **Prós:** Escalabilidade de escrita virtualmente infinita para uma única entidade lógica (a conta "baleia").
        - **Contras:**
            - **Lentidão na Leitura:** As leituras se tornam muito mais lentas e caras, pois exigem a consulta a múltiplos registros/shards (operação de *Gather*).
            - **Débitos Complexos:** Debitar da conta se torna um problema complexo. De qual cofre você tira o dinheiro? E se um cofre não tiver saldo suficiente? Isso geralmente exige um processo de "drenagem" assíncrono, onde os saldos dos cofres são periodicamente consolidados em um cofre principal, de onde os débitos são feitos.
    """)

render_write_sharding_page()
