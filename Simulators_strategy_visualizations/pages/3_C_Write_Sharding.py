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
            
    st.header("Análise Teórica no Contexto PIX")
    st.markdown("""
    **O Problema:** A conta de um grande varejista precisa receber dezenas de milhares de **PIX Crédito** por segundo. As abordagens dos Cenários A e B, que operam em um único registro de saldo, não conseguem escalar para essa demanda, pois atingem o limite de escrita de uma única partição/servidor (Hot Partition).

    **A Solução (Write Sharding - Múltiplos Cofres):**
    Esta estratégia é projetada para escalar a **escrita** de forma massiva. Em vez de um único registro de saldo, a conta é dividida em N "cofres" (shards).

    - **Processando PIX Crédito (A Operação de "Scatter"):**
        - Quando um PIX de crédito é recebido, o sistema não precisa ler o saldo atual. Ele simplesmente adiciona o valor a um dos N cofres.
        - A escolha do cofre é geralmente feita por um hash do ID da transação PIX, o que distribui as escritas de forma aleatória e uniforme.
        - **Resultado:** O sistema pode processar N créditos simultaneamente, um em cada cofre, sem nenhum tipo de bloqueio ou conflito. A capacidade de escrita é multiplicada por N.

    - **O Grande Desafio: Processar PIX Débito (A Operação de "Gather"):**
        - Esta é a parte difícil e o núcleo do seu problema de modelagem de débito. Para autorizar um **PIX Débito**, você precisa saber o saldo **total** e consolidado.
        - **Leitura (Gather):** Como a visualização mostra, para obter o saldo total, a aplicação precisa ler o saldo parcial de **todos os N cofres** e somá-los. Esta operação é lenta, cara e complexa.
        - **Execução do Débito:** Uma vez que você tem o saldo total, de qual cofre você subtrai o valor?
            - Se você escolher um cofre aleatório, ele pode não ter saldo suficiente.
            - Se você tentar debitar um pouco de cada cofre, a operação se torna uma transação distribuída complicada e lenta.
        - **Solução Comum:** Geralmente, os débitos não são feitos diretamente dos cofres de escrita. Em vez disso, um processo assíncrono (um "dreno") periodicamente consolida o dinheiro dos múltiplos cofres em um único "cofre de pagamento" principal, de onde os **PIX Débito** são efetivamente realizados. Isso, no entanto, introduz latência (o dinheiro do crédito não fica disponível para débito instantaneamente).

    - **Trade-offs para PIX:**
        - **Prós:** Escalabilidade de **crédito** quase infinita. Perfeito para casos de uso de ingestão massiva de pagamentos.
        - **Contras:** A leitura do saldo é lenta e cara. A lógica de **débito** se torna extremamente complexa e muitas vezes não é em tempo real, o que pode não ser aceitável para todos os modelos de negócio.
    """)

render_write_sharding_page()
