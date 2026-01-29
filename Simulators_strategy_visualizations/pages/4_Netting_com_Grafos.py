import streamlit as st
import graphviz
from collections import defaultdict
import pandas as pd

st.set_page_config(layout="wide", page_title="Estudo de Caso 4: Otimização de Liquidez com Grafos")

# --- Lógica da Simulação (Refatorada para Clareza) ---

@st.cache_data
def get_transactions():
    return [
        # Ciclo de Netting Perfeito (A -> B -> C -> A)
        {"from": "Banco A", "to": "Banco B", "amount": 10},
        {"from": "Banco B", "to": "Banco C", "amount": 10},
        {"from": "Banco C", "to": "Banco A", "amount": 10},

        # Transação "normal" que não faz parte do ciclo principal
        {"from": "Banco D", "to": "Banco A", "amount": 5},

        # Um ciclo menor e mais complexo (D -> E -> D) que não se anula
        {"from": "Banco D", "to": "Banco E", "amount": 7},
        {"from": "Banco E", "to": "Banco D", "amount": 6}, # Note a diferença de valor

        # Outra transação externa
        {"from": "Banco B", "to": "Banco E", "amount": 3},
    ]

def find_cycles(graph):
    """
    Implementação correta e mais limpa de DFS para detecção de ciclos.
    Baseado no algoritmo de Tarjan, mas simplificado para encontrar todos os ciclos elementares.
    """
    cycles = []
    path = []
    visited = set()
    
    def dfs(node):
        path.append(node)
        visited.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor in path:
                try:
                    cycle_start_index = path.index(neighbor)
                    # Adiciona uma cópia do ciclo encontrado
                    cycles.append(path[cycle_start_index:])
                except ValueError:
                    pass
            elif neighbor not in visited:
                dfs(neighbor)
        
        path.pop()

    # Executa DFS para cada nó para garantir que todos os ciclos sejam encontrados
    all_nodes = list(graph.keys())
    for node in all_nodes:
        dfs(node)
        # Limpa o estado para a próxima busca a partir de um novo nó inicial
        visited.clear()
        path.clear()

    # Filtra ciclos duplicados (mantendo a ordem original)
    unique_cycles = []
    seen_cycles = set()
    for cycle in cycles:
        # Cria uma representação canônica do ciclo (tupla ordenada) para verificar duplicatas
        canonical = tuple(sorted(cycle))
        if canonical not in seen_cycles:
            unique_cycles.append(cycle)
            seen_cycles.add(canonical)
            
    return unique_cycles

# --- Renderização da Página ---

st.title("Estudo de Caso 4: Otimização de Liquidez com Teoria dos Grafos")
st.markdown("---")
st.markdown("""
### Resumo
Este estudo avança das otimizações no nível de armazenamento de dados para uma otimização no nível de processo de negócio: a **economia de liquidez em sistemas de pagamento**. Em sistemas de liquidação bruta em tempo real (RTGS), pode ocorrer um fenômeno de **Gridlock** (impasse sistêmico), onde múltiplas instituições financeiras estão mutuamente bloqueadas, cada uma esperando receber fundos para poder liquidar suas próprias obrigações. Esta simulação demonstra um **Mecanismo de Economia de Liquidez (LSM)** que utiliza a teoria dos grafos para identificar e resolver esses impasses através de "netting" (compensação) multilateral, uma abordagem fundamentada nos algoritmos propostos por **Bech & Soramäki (2001)**.
""")
st.markdown("---")

# --- Metodologia ---
st.header("Metodologia: Modelagem de Gridlock com Grafos")
st.markdown("""
Conforme descrito por Bech & Soramäki, a resolução de impasses em sistemas de pagamento pode ser modelada através da análise topológica de um grafo de obrigações.
1.  **Modelagem do Grafo:** As obrigações de pagamento pendentes entre instituições são modeladas como um **grafo direcionado e ponderado**. Cada instituição é um nó, e uma obrigação de pagamento de valor `X` do `Banco U` para o `Banco V` é representada por uma aresta `U -> V` com peso `X`.
2.  **Detecção de Ciclos:** Um impasse no estilo "gridlock" se manifesta como um ou mais ciclos no grafo de dependências (e.g., A deve a B, que deve a C, que deve a A). Utilizamos um algoritmo de **Busca em Profundidade (DFS)** para identificar todos os ciclos elementares no grafo.
3.  **Validação para Netting:** Para cada ciclo detectado, o sistema verifica se as obrigações financeiras entre os participantes do ciclo se anulam mutuamente. Se o fluxo líquido de caixa para cada participante dentro do ciclo for zero, as transações podem ser liquidadas por compensação, sem a necessidade de movimentação de fundos.
""")
st.markdown("---")

# --- Simulação ---
st.header("Simulação Interativa")

transactions = get_transactions()
st.subheader("1. Obrigações de Pagamento Pendentes")
st.table(pd.DataFrame(transactions))

# Construção da Adjacency List e visualização do grafo
adjacency_list = defaultdict(list)
all_participants = set()
for tx in transactions:
    adjacency_list[tx["from"]].append(tx["to"])
    all_participants.add(tx["from"])
    all_participants.add(tx["to"])

dot = graphviz.Digraph(comment='Grafo de Transações')
dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
for node in all_participants:
    dot.node(node, node)

edge_labels = defaultdict(int)
for tx in transactions:
    edge_labels[(tx["from"], tx["to"])] += tx["amount"]

for (source, dest), amount in edge_labels.items():
    dot.edge(source, dest, label=f"${amount}M")

st.subheader("2. Grafo de Dependências Financeiras")
st.graphviz_chart(dot)

# Detecção e Análise de Ciclos
st.subheader("3. Análise de Ciclos para Netting")
found_cycles = find_cycles(adjacency_list)

if not found_cycles:
    st.info("Nenhum ciclo de dependência encontrado no grafo.")
else:
    st.write(f"Foram detectados **{len(found_cycles)}** ciclos de dependência:")
    for i, cycle in enumerate(found_cycles):
        cycle_nodes = set(cycle)
        cycle_path = " -> ".join(cycle + [cycle[0]]) # Mostra o fechamento do ciclo
        st.markdown(f"#### Ciclo {i+1}: `{cycle_path}`")

        # Filtrar transações pertencentes apenas a este ciclo
        cycle_transactions = [
            tx for tx in transactions if tx["from"] in cycle_nodes and tx["to"] in cycle_nodes
        ]
        
        # Calcular fluxo líquido
        net_flows = defaultdict(float)
        total_liquidity_in_cycle = 0
        for tx in cycle_transactions:
            # Garante que a transação esteja contida no ciclo atual
            if tx["from"] in cycle and tx["to"] in cycle:
                net_flows[tx["from"]] -= tx["amount"]
                net_flows[tx["to"]] += tx["amount"]
                total_liquidity_in_cycle += tx["amount"]

        # Validar otimização
        is_optimizable = all(abs(flow) < 0.001 for flow in net_flows.values()) and net_flows
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Fluxos Líquidos dos Participantes:**")
            st.json({k: f"{v:+.2f}M" for k, v in net_flows.items()})

        with col2:
            if is_optimizable:
                st.success(f"**Ciclo Otimizável.**")
                st.markdown(f"Um total de **${total_liquidity_in_cycle}M** em liquidez pode ser liberado.")
                st.balloons()
            else:
                st.error("**Ciclo Não Otimizável.**")
                st.markdown("Os fluxos líquidos não se anulam.")
st.markdown("---")

# --- Análise ---
st.header("Análise dos Resultados e Implicações")
st.markdown("""
A simulação demonstra que a identificação de ciclos de dependência é uma ferramenta poderosa.
-   No ciclo `A -> B -> C -> A`, as obrigações de $10M são perfeitamente simétricas. Sem o netting, o sistema precisaria de uma liquidez total de $30M para processar as três transações sequencialmente. Com o netting, as obrigações são compensadas e o resultado é o mesmo, mas com uma necessidade de liquidez de **zero**.
-   No ciclo `D -> E -> D`, as obrigações não são simétricas ($7M vs $6M). O ciclo é detectado, mas a validação falha, pois o fluxo líquido não é zero. O sistema não pode aplicar o netting, e essas transações precisariam ser liquidadas por outros meios.

A aplicação de LSMs em sistemas de pagamento permite uma operação mais eficiente e segura, reduzindo a dependência de grandes reservas de capital para liquidar operações diárias e mitigando o risco de falhas sistêmicas em cascata causadas por um gridlock. A viabilidade de executar tais algoritmos de forma performática em grafos de larga escala é continuamente validada por avanços na ciência da computação, como os apresentados por **Duan et al. (2025)**, que demonstram a resolução de problemas topológicos complexos em tempo quase linear.
""")
st.markdown("---")

st.subheader("Referências e Leitura Adicional")
st.markdown("""
- **Bech, M. L., & Soramäki, K. (2001).** "Gridlock Resolution in Interbank Payment Systems". *Bank of Finland Discussion Paper*. **(Leitura Fundamental)**.
- **Duan, R., & Mao, Y. (2025).** "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths". *Proceedings of the 57th ACM Symposium on Theory of Computing (STOC)*.
- **Bank for International Settlements (BIS).** (Várias publicações sobre "Payment and settlement systems" e "Liquidity saving mechanisms").
""")