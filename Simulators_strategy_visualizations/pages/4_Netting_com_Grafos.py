import streamlit as st
import graphviz
from collections import defaultdict

st.set_page_config(layout="wide")

st.title("Estratégia de Netting Interbancário com Grafos")

st.write("""
Esta simulação demonstra como a detecção de ciclos em um grafo de transações pode ser usada para otimizar a liquidez em um sistema interbancário. A ideia é identificar "anéis de compensação" onde as obrigações se anulam, permitindo liquidar múltiplas transações sem a necessidade de movimentar o volume total de dinheiro.
""")

# --- 1. Estrutura de Dados Aprimorada ---
st.write("### 1. Estrutura de Dados: Transações Complexas")
st.write("""
Abandonamos a lista simples de transações e adotamos uma estrutura que suporta operações de 1-para-N (um débito, múltiplos créditos) e N-para-1. Cada transação é um objeto com uma lista de débitos e uma lista de créditos.
""")
transactions = [
    {"id": "TX1", "debits": [{"from": "Banco A", "amount": 100}], "credits": [{"to": "Banco B", "amount": 100}]},
    {"id": "TX2", "debits": [{"from": "Banco B", "amount": 70}], "credits": [{"to": "Banco C", "amount": 70}]},
    {"id": "TX3", "debits": [{"from": "Banco C", "amount": 100}], "credits": [{"to": "Banco A", "amount": 100}]},
    {"id": "TX4", "debits": [{"from": "Banco D", "amount": 50}], "credits": [{"to": "Banco A", "amount": 50}]}, # Externa ao ciclo principal
    {"id": "TX5", "debits": [{"from": "Banco B", "amount": 30}], "credits": [{"to": "Banco D", "amount": 20}, {"to": "Banco E", "amount": 10}]}, # Exemplo 1-para-N
]
st.json(transactions)


# --- 2. Construção do Grafo ---
st.write("### 2. Construção do Grafo de Dependências")
st.write("""
O grafo é construído onde cada nó é um banco. Uma aresta `(U, V)` significa que o banco `U` tem uma obrigação a pagar ao banco `V`. Isso nos permite visualizar as dependências de pagamento.
""")
adjacency_list = defaultdict(list)
all_participants = set()

for tx in transactions:
    sources = [d["from"] for d in tx["debits"]]
    destinations = [c["to"] for c in tx["credits"]]
    for source in sources:
        all_participants.add(source)
        for dest in destinations:
            all_participants.add(dest)
            adjacency_list[source].append(dest)

# Visualização do Grafo Completo
dot = graphviz.Digraph(comment='Grafo de Transações')
dot.attr('node', shape='box', style='rounded')
for node in all_participants:
    dot.node(node, node)

edge_labels = defaultdict(int)
for tx in transactions:
    for debit in tx["debits"]:
        for credit in tx["credits"]:
            # Agregando valores para múltiplas transações entre os mesmos bancos
            edge_labels[(debit["from"], credit["to"])] += debit["amount"]

for (source, dest), amount in edge_labels.items():
    dot.edge(source, dest, label=f'€{amount}')

st.graphviz_chart(dot)


# --- 3. Algoritmo de Detecção de Ciclos (DFS) ---
st.write("### 3. Detecção de Ciclos (DFS)")
st.write("""
Usamos o algoritmo de Busca em Profundidade (DFS) para encontrar ciclos no grafo. Um ciclo como `A -> B -> C -> A` representa uma potencial oportunidade de netting.
""")
def find_cycles(graph):
    cycles = []
    visited = set()
    recursion_stack = set()

    def dfs(node, path):
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                # O ciclo será adicionado quando a recursão encontrar um nó já na pilha
                new_cycles = dfs(neighbor, path)
                if new_cycles:
                    cycles.extend(new_cycles)
            elif neighbor in recursion_stack:
                # Ciclo encontrado!
                cycle_start_index = path.index(neighbor)
                cycles.append(path[cycle_start_index:] + [neighbor])
        
        # Backtrack
        recursion_stack.remove(node)
        path.pop()
        return cycles

    all_nodes = list(graph.keys())
    for node in all_nodes:
        if node not in visited:
            find_cycles_recursive(graph, node, set(), set(), [], cycles)
    
    # Filtrar ciclos duplicados
    unique_cycles = []
    for cycle in cycles:
        sorted_cycle = tuple(sorted(cycle))
        if sorted_cycle not in [tuple(sorted(c)) for c in unique_cycles]:
            unique_cycles.append(cycle)
            
    return unique_cycles

def find_cycles_recursive(graph, node, visited, recursion_stack, path, cycles):
    visited.add(node)
    recursion_stack.add(node)
    path.append(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            find_cycles_recursive(graph, neighbor, visited, recursion_stack, path, cycles)
        elif neighbor in recursion_stack:
            try:
                cycle_start_index = path.index(neighbor)
                found_cycle = path[cycle_start_index:]
                # Adicionar uma cópia para não ser afetada pelo pop
                cycles.append(list(found_cycle))
            except ValueError:
                # Pode acontecer em grafos complexos, ignoramos
                pass

    path.pop()
    recursion_stack.remove(node)


found_cycles = find_cycles(adjacency_list)
st.write("Ciclos Detectados:", found_cycles if found_cycles else "Nenhum ciclo detectado.")

# --- 4. Validar e Processar o Netting do Ciclo ---
st.write("### 4. Validação e Netting do Ciclo")
st.write("""
Uma vez que um ciclo é detectado, validamos se as transações *entre os participantes do ciclo* se anulam. Se o fluxo líquido para cada participante for zero, o ciclo é 'otimizável' e as transações podem ser liquidadas internamente.
""")

if not found_cycles:
    st.info("Nenhum ciclo encontrado para otimização.")
else:
    for i, cycle in enumerate(found_cycles):
        st.write("---")
        st.subheader(f"Analisando Ciclo {i+1}: {" -> ".join(cycle)}")
        
        # Desenhar o sub- grafo do ciclo
        cycle_dot = graphviz.Digraph(f'Ciclo {i+1}')
        cycle_dot.attr('node', shape='box', style='rounded', color='blue')
        cycle_nodes = set(cycle[:-1]) # Usa set para participantes unicos
        for node in cycle_nodes:
            cycle_dot.node(node, node)

        # Considerar apenas transações onde AMBOS os lados estão no ciclo
        cycle_transactions = [
            tx for tx in transactions 
            if all(p in cycle_nodes for p in [d["from"] for d in tx["debits"]]) and \
               all(p in cycle_nodes for p in [c["to"] for c in tx["credits"]])
        ]

        if not cycle_transactions:
            st.warning("Nenhuma transação completa encontrada dentro deste ciclo.")
            continue

        st.write("**Transações consideradas para este ciclo:**")
        st.json(cycle_transactions)

        # Calcular o fluxo líquido para cada participante
        net_flows = defaultdict(float)
        for tx in cycle_transactions:
            for debit in tx["debits"]:
                net_flows[debit["from"]] -= debit["amount"]
            for credit in tx["credits"]:
                net_flows[credit["to"]] += credit["amount"]

        # Validar se o fluxo líquido é zero
        # Usamos uma pequena tolerância para problemas de ponto flutuante
        is_optimizable = all(abs(flow) < 0.001 for flow in net_flows.values())

        st.write("**Fluxos Líquidos Calculados:**")
        st.json({k: f"{v:+.2f}" for k, v in net_flows.items()})

        # Desenhar as arestas do ciclo
        cycle_edge_labels = defaultdict(int)
        for tx in cycle_transactions:
            for debit in tx["debits"]:
                for credit in tx["credits"]:
                     cycle_edge_labels[(debit["from"], credit["to"])] += debit["amount"]
        
        for (source, dest), amount in cycle_edge_labels.items():
            cycle_dot.edge(source, dest, label=f'€{amount}', color='blue')

        st.graphviz_chart(cycle_dot)

        if is_optimizable and net_flows:
            st.success(f"**O ciclo é otimizável!** As transações podem ser liquidadas internamente, liberando {sum(cycle_edge_labels.values())} em liquidez.")
            st.balloons()
        else:
            st.error(f"**O ciclo NÃO é otimizável.** Os fluxos não se anulam perfeitamente.")