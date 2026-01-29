import streamlit as st
import graphviz
from collections import defaultdict
import pandas as pd
import json

st.set_page_config(layout="wide", page_title="Estudo de Caso 4: Otimização de Liquidez com Grafos")

# --- Lógica da Simulação (Refatorada para Clareza) ---

@st.cache_data
def get_transactions():
    """
    Conjunto de dados simplificado para focar na didática de dois ciclos independentes:
    1. Um ciclo perfeitamente otimizável.
    2. Um ciclo claramente não otimizável.
    """
    return [
        # Ciclo 1: Perfeitamente otimizável (A -> B -> C -> A)
        {"from": "Banco A", "to": "Banco B", "amount": 10},
        {"from": "Banco B", "to": "Banco C", "amount": 10},
        {"from": "Banco C", "to": "Banco A", "amount": 10},

        # Ciclo 2: Não otimizável (X -> Y -> Z -> X, com valores diferentes)
        {"from": "Banco X", "to": "Banco Y", "amount": 8},
        {"from": "Banco Y", "to": "Banco Z", "amount": 8},
        {"from": "Banco Z", "to": "Banco X", "amount": 7},

        # Transação externa que não forma ciclo
        {"from": "Banco A", "to": "Banco Z", "amount": 5},
    ]

def find_cycles(graph):
    # Algoritmo de busca de ciclo baseado em DFS
    cycles = []
    path = []
    recursion_stack = set()
    
    def dfs(node):
        path.append(node)
        recursion_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor in recursion_stack:
                try:
                    cycle_start_index = path.index(neighbor)
                    cycles.append(path[cycle_start_index:])
                except ValueError:
                    pass
            elif neighbor not in path:
                dfs(neighbor)
        
        path.pop()
        recursion_stack.remove(node)

    all_nodes = list(graph.keys())
    for node in all_nodes:
        dfs(node)

    # Filtra ciclos duplicados
    unique_cycles = []
    seen_cycles = set()
    for cycle in cycles:
        canonical = tuple(sorted(cycle))
        if len(canonical) > 1 and canonical not in seen_cycles:
            unique_cycles.append(cycle)
            seen_cycles.add(canonical)
            
    return unique_cycles

# --- Renderização da Página ---

st.title("Estudo de Caso 4: Otimização de Liquidez com Teoria dos Grafos")
st.markdown("---")
st.markdown("""
### Resumo
Este estudo avança das otimizações no nível de armazenamento de dados para uma otimização no nível de processo de negócio: a **economia de liquidez em sistemas de pagamento**. Em sistemas de liquidação bruta em tempo real (RTGS), pode ocorrer um fenômeno de **Gridlock** (impasse sistêmico). Esta simulação demonstra um **Mecanismo de Economia de Liquidez (LSM)** que utiliza a teoria dos grafos para resolver esses impasses através de "netting", uma abordagem fundamentada nos algoritmos de **Bech & Soramäki (2001)**. Ao final, detalhamos as aplicações práticas desta teoria em sistemas de pagamento, câmaras de compensação e tesouraria corporativa.
""")
st.markdown("---")

st.header("Metodologia: Modelagem de Gridlock com Grafos")
st.markdown("""
1.  **Modelagem do Grafo:** As obrigações de pagamento pendentes são modeladas como um grafo direcionado. Cada instituição é um nó, e uma obrigação de `U` para `V` é uma aresta `U -> V`.
2.  **Detecção de Ciclos:** Um impasse ("gridlock") se manifesta como um ciclo no grafo (e.g., A deve a B, que deve a C, que deve a A). Usamos um algoritmo de Busca em Profundidade (DFS) para encontrar esses ciclos.
3.  **Validação para Netting (Compensação):** Para cada ciclo, o sistema atua como uma **câmara de compensação**. Para cada participante do ciclo, somamos todas as suas **transações de crédito** (dinheiro a receber de outros no ciclo) e subtraímos todas as suas **transações de débito** (dinheiro a pagar a outros no ciclo). Se o resultado (o fluxo líquido) for zero para todos, o ciclo se anula.
""")
st.markdown("---")

st.header("Simulação Interativa")

transactions = get_transactions()
st.subheader("1. Obrigações de Pagamento Pendentes")
st.table(pd.DataFrame(transactions))

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

st.subheader("3. Análise de Ciclos para Netting")
found_cycles = find_cycles(adjacency_list)

if not found_cycles:
    st.info("Nenhum ciclo de dependência encontrado no grafo.")
else:
    st.write(f"Foram detectados **{len(found_cycles)}** ciclos de dependência claros:")
    for i, cycle in enumerate(found_cycles):
        cycle_nodes = set(cycle)
        cycle_path = " -> ".join(cycle + [cycle[0]])
        st.markdown(f"#### Ciclo {i+1}: `{cycle_path}`")

        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Cálculo de Fluxo Líquido:**")
                cycle_transactions = [tx for tx in transactions if tx["from"] in cycle_nodes and tx["to"] in cycle_nodes]
                
                net_flows = defaultdict(float)
                total_liquidity_in_cycle = 0
                for tx in cycle_transactions:
                    if tx["from"] in cycle and tx["to"] in cycle:
                        net_flows[tx["from"]] -= tx["amount"]
                        net_flows[tx["to"]] += tx["amount"]
                        total_liquidity_in_cycle += tx["amount"]

                is_optimizable = all(abs(net_flows.get(node, 0)) < 0.001 for node in cycle_nodes) and net_flows
                
                formatted_flows = {k: f"{v:+.2f}M" for k, v in net_flows.items()}
                st.code(json.dumps(formatted_flows, indent=2), language='json')

            with col2:
                if is_optimizable:
                    st.success("**Ciclo Otimizável**")
                    st.markdown(f"O fluxo líquido é zero para todos os participantes. Um total de **${total_liquidity_in_cycle}M** em liquidez pode ser liberado por compensação.")
                else:
                    st.error("**Ciclo Não Otimizável**")
                    st.markdown("Os fluxos líquidos não se anulam perfeitamente.")
st.markdown("---")

st.header("Análise dos Resultados e Implicações")
st.markdown("""
A simulação agora demonstra de forma clara os dois cenários encontrados por uma câmara de compensação.

-   **No Ciclo 1 (`A -> B -> C -> A`):** As obrigações se anulam perfeitamente.
    -   **Para o Banco A:** A transação `C -> A` é um **crédito** de $10M, enquanto a `A -> B` é um **débito** de $10M. O fluxo líquido é zero.
    -   **Resultado:** O sistema pode liquidar $30M em obrigações com uma necessidade de liquidez de **zero**.

-   **No Ciclo 2 (`X -> Y -> Z -> X`):** As obrigações não são simétricas.
    -   **Para o Banco Z:** O **crédito** de `Y -> Z` é de $8M, mas o **débito** de `Z -> X` é de $7M. O fluxo líquido é de +$1M.
    -   **Resultado:** Como o fluxo não é zero para todos os participantes, o ciclo não pode ser liquidado inteiramente por compensação e exigirá liquidez real para ser resolvido.
""")
st.markdown("---")

st.header("Aplicações no Mundo Real e Benefícios de Negócio")
st.markdown("""
A técnica de netting multilateral via grafos não é apenas um exercício teórico; é um componente central da infraestrutura financeira moderna.

#### 1. Sistemas de Pagamentos de Grande Valor (RTGS)
- **O quê:** Sistemas operados por Bancos Centrais (como o STR no Brasil, Fedwire nos EUA, TARGET2 na Europa).
- **Aplicação:** A principal função de um Mecanismo de Economia de Liquidez (LSM) nestes sistemas é exatamente a que foi simulada: encontrar e liquidar ciclos para prevenir um gridlock sistêmico.

#### 2. Câmaras de Compensação de Ativos (Clearing Houses)
- **O quê:** Entidades que se interpõem entre compradores e vendedores de ativos (ações, derivativos, etc.), como a B3 no Brasil.
- **Aplicação:** O netting é usado para simplificar massivamente a liquidação de negócios, reduzindo o número de transferências de ativos e dinheiro que precisam de fato ocorrer.

#### 3. Tesouraria de Corporações Multinacionais
- **O quê:** Grandes empresas com muitas subsidiárias em diferentes países.
- **Aplicação:** Permite otimizar o fluxo de caixa interno, evitando transações de câmbio internacionais desnecessárias, economizando em taxas e custos operacionais.
""")
st.markdown("---")

st.subheader("Referências e Leitura Adicional")
st.markdown("""
- **Bech, M. L., & Soramäki, K. (2001).** "Gridlock Resolution in Payment Systems". *Bank of Finland Discussion Paper*. **(Leitura Fundamental)**.
- **Duan, R., & Mao, Y. (2025).** "Breaking the Sorting Barrier for Directed Single-Source Shortest Paths". *Proceedings of the 57th ACM Symposium on Theory of Computing (STOC)*.
- **Bank for International Settlements (BIS).** (Várias publicações sobre "Payment and settlement systems" e "Liquidity saving mechanisms").
""")