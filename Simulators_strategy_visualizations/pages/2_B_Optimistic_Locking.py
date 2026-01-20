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
            
    st.header("Análise Teórica no Contexto PIX")
    st.markdown("""
    **O Problema:** O bloqueio pessimista (Cenário A) não escala para contas com alto volume de transações PIX. Como processar múltiplos **PIX Débito** e **PIX Crédito** concorrentes em uma única conta sem criar uma fila massiva no banco de dados?

    **A Solução (Otimista com Compare-and-Swap - CAS):**
    Bancos de dados como o DynamoDB são "otimistas". Eles assumem que conflitos são raros. Em vez de trancar a porta, todos podem ler o saldo ao mesmo tempo. A verificação acontece apenas no final.

    O processo para um **PIX Débito** é:
    1.  A aplicação lê o saldo da conta: `(Saldo: R$100, Versão: 1)`.
    2.  Calcula o novo saldo localmente (ex: `R$100 - R$10 = R$90`).
    3.  Tenta escrever no banco com uma condição: `UPDATE saldo SET valor=90, versao=2 WHERE id=? AND versao=1;`
        - **Este é o Compare-and-Swap (CAS).** A escrita só funciona **SE** a versão no banco ainda for a mesma que a aplicação leu (versão 1).
    4.  **Sucesso:** Se a versão bate, a escrita é feita e o novo número de versão (2) é salvo. A primeira thread a chegar vence.
    5.  **Falha:** Se outra thread já atualizou o saldo (e a versão agora é 2), a condição `versao=1` falha. A transação é rejeitada com um `ConditionalCheckFailedException`. A aplicação precisa então reiniciar todo o processo: reler o saldo (`Versão: 2`), recalcular e tentar de novo.

    - **O que a visualização mostra:** Múltiplas threads (processando múltiplos PIX) tentam escrever ao mesmo tempo. Apenas uma vence (luz verde). As outras falham (luz vermelha) e precisam entrar em um "loop de retry".
    
    - **A Otimização (Solução do Itaú com Fila em Memória):** O "loop de retry" pode ser caro e sobrecarregar a aplicação. A solução é organizar a bagunça *antes* de chegar no banco. A aplicação cria uma fila em memória (usando Kafka, SQS, ou um buffer local) para cada conta de destino. Isso garante que, para uma mesma conta, as operações PIX (débitos e créditos) sejam processadas uma de cada vez (Single Thread per Account), eliminando a chance de conflitos de versão e a necessidade de retentativas no banco de dados. O gargalo de concorrência é movido do banco para a aplicação, que é mais fácil e barato de escalar.
    - **Trade-offs para PIX:**
        - **Prós:** Extremamente escalável, pois não há bloqueios no banco, permitindo alta vazão de transações em contas diferentes.
        - **Contras:** A complexidade do "loop de retry" é transferida para a aplicação. Sem uma fila de otimização, alta concorrência *na mesma conta* pode levar a muitas falhas e retentativas, aumentando a latência.
    """)

render_optimistic_locking_page()
