import streamlit as st
import graphviz

st.set_page_config(layout="wide", page_title="Estratégia Interbancária com Grafos", page_icon="🏦")

st.markdown("# Netting Interbancário: Otimização de Liquidez com Grafos")

st.write("""
A arquitetura de alta frequência que discutimos (Kafka + ECS + DynamoDB) é a base para escalar o processamento de transações. Agora, vamos elevar o nível e aplicar um conceito de otimização de liquidez usado em sistemas de pagamento de grande valor (RTGS - Real-Time Gross Settlement), mas de forma adaptada: o **Netting Multilateral usando Grafos**.

O problema que resolvemos aqui é: como reduzir a necessidade de liquidez (dinheiro "travado") em um sistema com múltiplos participantes (bancos)?

**Cenário Clássico (Ineficiente):**
- Banco A deve 10M para o Banco B.
- Banco B deve 10M para o Banco C.
- Banco C deve 10M para o Banco A.

Num sistema RTGS simples, cada transação ocorreria individualmente, exigindo que cada banco tivesse pelo menos 10M em caixa para liquidar sua parte, totalizando uma necessidade de liquidez de 30M no sistema.

**A Solução com Grafos: Encontrar Ciclos de Compensação**
A ideia é tratar as ordens de pagamento como um grafo direcionado, onde os bancos são os nós e as transações são as arestas (com o valor como peso). Se um ciclo for detectado, podemos liquidar todas as transações do ciclo simultaneamente, com um fluxo financeiro líquido de **zero**.
""")

st.markdown("---")

st.markdown("### Simulação Visual da Estratégia")

# 1. Estrutura de Dados: Transações Interbancárias Pendentes
transactions = [
    # Ciclo de Netting Perfeito (A -> B -> C -> A)
    {"from": "Banco A (SPB)", "to": "Banco B (SPB)", "amount": 10, "type": "interbank"},
    {"from": "Banco B (SPB)", "to": "Banco C (SPB)", "amount": 10, "type": "interbank"},
    {"from": "Banco C (SPB)", "to": "Banco A (SPB)", "amount": 10, "type": "interbank"},

    # Transação "normal" que não faz parte do ciclo principal
    {"from": "Banco D (SPB)", "to": "Banco A (SPB)", "amount": 5, "type": "interbank"},

    # Débito de um cliente do Banco A para um cliente do Banco D (1:N)
    # A conta "Power-User" do Banco A está enviando dinheiro para vários recebedores no Banco D
    {"from": "Banco A (Conta Power-User)", "to": "Banco D (Recebedor 1)", "amount": 1.5, "type": "customer"},
    {"from": "Banco A (Conta Power-User)", "to": "Banco D (Recebedor 2)", "amount": 2.5, "type": "customer"},
    {"from": "Banco A (Conta Power-User)", "to": "Banco D (Recebedor 3)", "amount": 1.0, "type": "customer"},

    # Uma transação que cria um ciclo menor e mais complexo (D -> E -> D)
    {"from": "Banco D (SPB)", "to": "Banco E (SPB)", "amount": 7, "type": "interbank"},
    {"from": "Banco E (SPB)", "to": "Banco D (SPB)", "amount": 7, "type": "interbank"},
]

# Construir uma lista de adjacência para o grafo
adjacency_list = {}
for tx in transactions:
    # Ignoramos as contas individuais para a detecção de ciclo interbancário
    sender_node = tx["from"].split(" (")[0]
    receiver_node = tx["to"].split(" (")[0]

    if sender_node not in adjacency_list:
        adjacency_list[sender_node] = []
    if receiver_node not in adjacency_list:
        adjacency_list[receiver_node] = []

    if receiver_node not in adjacency_list[sender_node]:
        adjacency_list[sender_node].append(receiver_node)


st.write("**Transações Pendentes na Câmara de Compensação:**")
st.table(transactions)

# --- Visualização do Grafo ---
dot = graphviz.Digraph('Interbank-Transactions', comment='Fluxo de Pagamentos Interbancários')
dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
dot.attr('edge', color='gray40', fontcolor='gray40')

# Adicionar todos os nós (bancos)
all_nodes = set()
for tx in transactions:
    all_nodes.add(tx["from"].split(" (")[0])
    all_nodes.add(tx["to"].split(" (")[0])

for node in all_nodes:
    dot.node(node, node)

# Adicionar arestas com base nas transações
for tx in transactions:
    sender_node = tx["from"].split(" (")[0]
    receiver_node = tx["to"].split(" (")[0]
    dot.edge(sender_node, receiver_node, label=f"  {tx['amount']}M" if tx['type'] == 'interbank' else f"  {tx['amount']}k")

st.write("### Grafo de Dependências de Pagamento:")
st.graphviz_chart(dot)


# 2. Algoritmo de Detecção de Ciclos (DFS)
def find_cycles(graph):
    cycles = []
    visited = set()
    recursion_stack = set()

    def dfs(node, path):
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            # Assegura que o vizinho existe no grafo antes de processar
            if neighbor in graph:
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in recursion_stack:
                    try:
                        cycle_start_index = path.index(neighbor)
                        # Um ciclo é válido se tiver mais de um nó ou se for um nó para ele mesmo
                        if len(path[cycle_start_index:]) > 1 or path[-1] == neighbor:
                             cycles.append(list(path[cycle_start_index:]))
                    except ValueError:
                        # Pode acontecer em cenários complexos, ignoramos o erro de path
                        pass

        # Backtrack
        recursion_stack.remove(node)
        path.pop()

    for node in list(graph): # Itera sobre uma cópia da lista de chaves
        if node not in visited:
            dfs(node, [])
    return cycles


st.write("### Análise de Otimização")
st.write("**Lista de Adjacência (Base para o Algoritmo):**", adjacency_list)

found_cycles = find_cycles(adjacency_list)
# Filtrar ciclos duplicados ou sub-ciclos
unique_cycles = []
for cycle in found_cycles:
    sorted_cycle = tuple(sorted(cycle))
    if sorted_cycle not in [tuple(sorted(c)) for c in unique_cycles]:
        unique_cycles.append(cycle)


st.write(f"**Ciclos de Netting Detectados ({len(unique_cycles)}):**", unique_cycles)

if unique_cycles:
    st.success("Encontramos oportunidades de otimização de liquidez! 🎉")
    st.write("""
    **Como funciona a Otimização:**
    - Para cada ciclo, o sistema pode validar se a soma dos valores das transações se anula.
    - Se sim, o "netting" é possível. As transações são marcadas como "liquidadas por compensação".
    - **Resultado:** A liquidez de 30M (do nosso exemplo A-B-C) não foi necessária. O saldo dos bancos permanece o mesmo, mas as obrigações foram cumpridas. Apenas as transações que não fazem parte do ciclo (como a do Banco D) precisam de liquidação com dinheiro real.
    """)
else:
    st.warning("Nenhum ciclo de otimização encontrado. Todas as transações seriam processadas individualmente.")


st.markdown("---")
st.markdown("""
### E a Conta 1:N no DynamoDB?

A estratégia de grafos é para a **otimização interbancária**. A estratégia de **agregação (Netting na Aplicação)** que usamos no Kafka/ECS é para o **nível da conta**. As duas trabalham juntas.

1.  **Nível da Conta (Intrabanco - O que o ECS faz):**
    - Milhares de débitos e créditos chegam para a `Conta Power-User` do `Banco A`.
    - O consumer do Kafka para a partição dessa conta agrupa (faz o "netting") dessas milhares de operações em memória: `(Soma(Créditos) - Soma(Débitos)) = SaldoLíquido`.
    - Ele faz **UMA** escrita no DynamoDB para atualizar o saldo da conta e múltiplas escritas para o extrato.
    - **PK/SK no DynamoDB:** `PK: ACCOUNT#BANK_A#POWER_USER`, `SK: BALANCE#CURRENT`.

2.  **Nível do Sistema (Interbancário - O que a Câmara de Compensação faz):**
    - Após o netting na conta, o `Banco A` determina que tem uma obrigação líquida de `5M` para o `Banco D` (resultante das operações da `Conta Power-User` e outras).
    - Essa obrigação `A -> D: 5M` entra no grafo de compensação interbancário.
    - O algoritmo de ciclo tentará usar essa obrigação para compensar outras (como `D -> E -> ... -> A`), reduzindo ainda mais a necessidade de liquidez, mas agora no nível do sistema financeiro como um todo.

**Juntando tudo, temos uma arquitetura que escala e otimiza em duas dimensões:**
- **Vertical (Escala de TPS na Conta):** Graças ao netting no ECS.
- **Horizontal (Otimização de Liquidez no Sistema):** Graças à detecção de ciclos no grafo de pagamentos.
""")
