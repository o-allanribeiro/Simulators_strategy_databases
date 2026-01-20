import streamlit as st
import graphviz
import random

st.set_page_config(layout="wide", page_title="Cenário B: Bloqueio Otimista")

# --- Funções de Simulação e Visualização ---
def generate_optimistic_locking_graph(concurrency, winner_thread, failed_threads, use_buffer):
    dot = graphviz.Digraph('OptimisticLock', comment='Compare-and-Swap')
    dot.attr('graph', rankdir='TB', splines='ortho')

    # --- Subgrafo da Aplicação (Threads) ---
    with dot.subgraph(name='cluster_app') as c:
        c.attr(label='Aplicação (Threads Concorrentes)', style='dashed')
        c.node_attr.update(shape='circle')
        for i in range(concurrency):
            if i == winner_thread:
                c.node(f'thread_{i}', f'Thread {i+1}', style='filled', fillcolor='lightgreen')
            elif i in failed_threads:
                c.node(f'thread_{i}', f'Thread {i+1}', style='filled', fillcolor='salmon')
            else:
                 c.node(f'thread_{i}', f'Thread {i+1}')
    
    # --- Subgrafo do Banco de Dados ---
    with dot.subgraph(name='cluster_db') as c:
        c.attr(label='Banco de Dados (DynamoDB)', style='filled', color='lightblue')
        c.node('db_record', '{Saldo: R$90 | Versão: 2}', shape='record')

    # --- Fila de Buffer (Solução Itaú) ---
    if use_buffer:
        dot.node('buffer', 'Fila em Memória\n(Single Thread per Account)', shape='box', style='filled', fillcolor='lightyellow')
        dot.edge('thread_0', 'buffer', style='invis') # Apenas para layout
        dot.edge('buffer', 'db_record', label=' Acesso Ordenado')
    
    # --- Conexões ---
    if not use_buffer:
        # Modo "corrida livre"
        for i in range(concurrency):
            if i == winner_thread:
                dot.edge(f'thread_{i}', 'db_record', label=' Escreveu com Sucesso!\n(CAS: Versão 1 == 1)', color='green', fontcolor='green')
            elif i in failed_threads:
                dot.edge(f'thread_{i}', 'db_record', label=' Falha na Escrita!\n(CAS: Versão 1 != 2)', color='red', fontcolor='red', style='dashed')
            else:
                dot.edge(f'thread_{i}', 'db_record', label='Lendo Saldo (R$100, Versão 1)', style='dotted')

    return dot

# --- Interface do Streamlit ---
def render_optimistic_locking_page():
    st.title("Cenário B: O Bloqueio Otimista (DynamoDB - Modelo Itaú)")
    st.image("https://i.imgur.com/gL8E3f6.png", caption="Visualização: Controle de Versão e Tentativa de Escrita (Compare-and-Swap)")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Painel de Controle")
        concurrency = st.slider("Threads Concorrentes na Mesma Conta", 2, 50, 5)
        use_buffer = st.checkbox("Usar Fila em Memória (Otimização Itaú)", value=False)
        run_simulation = st.button("Executar Simulação")

    with col2:
        st.header("Visualização do 'Motor'")

        if run_simulation:
            # --- Lógica da Simulação ---
            # Todas as threads leem a versão 1
            st.write("1. **Leitura Concorrente:** Todas as threads leem `Saldo: R$100, Versão: 1` ao mesmo tempo.")
            
            # Uma thread vence a "corrida"
            winner_thread = random.randint(0, concurrency - 1)
            failed_threads = [i for i in range(concurrency) if i != winner_thread]
            
            st.write(f"2. **Tentativa de Escrita:** Todas tentam atualizar o saldo. A **Thread {winner_thread + 1}** chega primeiro!")
            st.write("3. **Compare-and-Swap (CAS):** O banco verifica se a versão ainda é 1. Como é, a escrita da Thread vencedora é aceita e a versão é atualizada para 2.")
            st.write(f"4. **Rejeição:** As outras {concurrency - 1} threads são rejeitadas, pois a versão que elas leram (1) é diferente da versão atual no banco (2). Elas recebem um erro e precisam tentar novamente (Retry Loop).")

            graph = generate_optimistic_locking_graph(concurrency, winner_thread, failed_threads, use_buffer)
            st.graphviz_chart(graph)
        else:
            st.info("Ajuste os controles e clique em 'Executar Simulação' para ver o que acontece.")
            
    st.header("Análise Teórica")
    st.markdown("""
    **O Problema:** Como escalar escritas em uma única conta sem usar o custoso `SELECT FOR UPDATE` do bloqueio pessimista.

    **A Solução (Otimista):** O sistema permite que todos leiam o dado, mas impõe uma condição na hora de escrever: a escrita só é aceita se o dado não tiver sido alterado por outra pessoa desde o momento da leitura. Isso é feito com um "Token de Versão" ou "Número de Versão".

    - **O que a visualização mostra:** Múltiplas threads leem o saldo e a versão (`Versão: 1`). Todas tentam escrever o novo saldo, mas com a condição `SE a versão AINDA FOR 1`. Apenas a primeira que chega consegue. As outras recebem um erro e precisam reiniciar o processo: ler o novo saldo (`Versão: 2`), recalcular e tentar escrever de novo.
    - **A Otimização (Solução do Itaú):** Para evitar a "briga" de retentativas no banco de dados (que é caro), a própria aplicação cria uma fila em memória para cada conta. Isso garante que as operações para uma mesma conta sejam serializadas *antes* de chegarem ao banco, transformando a "corrida livre" em uma "fila organizada" e eliminando a necessidade de retentativas.
    - **Trade-offs:**
        - **Prós:** Altamente escalável para leituras. O banco em si não se torna um gargalo de escrita, pois não há bloqueios longos.
        - **Contras:** A lógica de "retry" se move para a aplicação, que se torna mais complexa. Em cenários de altíssima concorrência na mesma chave, a aplicação pode gastar muito tempo em retentativas se não houver uma otimização como a fila em memória.
    """)

render_optimistic_locking_page()
