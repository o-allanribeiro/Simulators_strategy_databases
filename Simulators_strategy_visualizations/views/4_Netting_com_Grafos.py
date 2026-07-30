import streamlit as st
import graphviz
from collections import defaultdict
import pandas as pd


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

st.header("O problema, em uma frase")
st.info(
    "Se um grupo de pessoas (ou bancos) deve dinheiro uns aos outros formando um ciclo fechado, "
    "às vezes ninguém precisa pagar nada de verdade — as dívidas se cancelam sozinhas. O desafio é "
    "**encontrar esses ciclos automaticamente**, mesmo quando existem milhares de dívidas cruzadas."
)

st.subheader("Um exemplo do dia a dia")
st.markdown("""
Imagine três amigos: **Ana deve R$ 100 para Bruno**, **Bruno deve R$ 100 para Carla**, e **Carla deve R$ 100 para Ana**.

Se cada um pagar sua dívida separadamente, R$ 300 precisam trocar de mãos. Mas se os três se sentarem numa mesa e compararem as contas, vão perceber que **ninguém precisa pagar nada** — a dívida de cada um cancela exatamente o que tem a receber. É um ciclo fechado.

Agora troque "Ana, Bruno e Carla" por **bancos**, e "R$ 100" por **milhões de reais em pagamentos entre instituições financeiras por dia**. É exatamente esse tipo de ciclo que a simulação abaixo encontra — automaticamente, entre vários participantes e transações.
""")

with st.expander("Como o algoritmo encontra esses ciclos (aprofundamento técnico)"):
    st.markdown("""
    1.  **Modelagem do Grafo:** As obrigações de pagamento pendentes são modeladas como um grafo direcionado. Cada instituição é um nó, e uma obrigação de `U` para `V` é uma aresta `U -> V`.
    2.  **Detecção de Ciclos:** Um impasse ("gridlock") se manifesta como um ciclo no grafo (e.g., A deve a B, que deve a C, que deve a A). Usamos um algoritmo de Busca em Profundidade (DFS) para encontrar esses ciclos.
    3.  **Validação para Netting (Compensação):** Para cada ciclo, o sistema atua como uma **câmara de compensação**. Para cada participante do ciclo, somamos todas as suas **transações de crédito** (dinheiro a receber de outros no ciclo) e subtraímos todas as suas **transações de débito** (dinheiro a pagar a outros no ciclo). Se o resultado (o fluxo líquido) for zero para todos, o ciclo se anula.

    Em sistemas reais, esse mecanismo é chamado de **Liquidity Saving Mechanism (LSM)**, e o impasse sistêmico que ele evita é conhecido como **Gridlock** — baseado nos algoritmos descritos por **Bech & Soramäki (2001)**.
    """)
st.markdown("---")

st.header("Agora com o exemplo dos bancos")
st.markdown("Abaixo estão 7 pagamentos pendentes entre 6 bancos. Alguns formam ciclos fechados (podem ser cancelados), outros não — veja se você consegue identificar algum antes de ler a análise.")

transactions = get_transactions()
st.subheader("1. Quem deve o quê")
st.table(
    pd.DataFrame(transactions).rename(columns={"from": "Deve (de)", "to": "Para", "amount": "Valor ($M)"})
)

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

st.subheader("2. O mesmo, em forma de grafo")
st.caption("Cada seta é uma dívida: o banco na base da seta deve para o banco na ponta.")
st.graphviz_chart(dot)

st.subheader("3. Quais ciclos podem ser cancelados?")
found_cycles = find_cycles(adjacency_list)

if not found_cycles:
    st.info("Nenhum ciclo foi encontrado — ou seja, nenhuma dívida pode ser cancelada aqui, todas precisam ser pagas em dinheiro real.")
else:
    st.write(f"O algoritmo encontrou **{len(found_cycles)}** ciclo(s) de dívida no grafo acima:")
    for i, cycle in enumerate(found_cycles):
        cycle_nodes = set(cycle)
        cycle_path = " → ".join(cycle + [cycle[0]])
        st.markdown(f"#### Ciclo {i+1}: `{cycle_path}`")

        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Quanto cada um deve e vai receber neste ciclo:**")
                cycle_transactions = [tx for tx in transactions if tx["from"] in cycle_nodes and tx["to"] in cycle_nodes]

                net_flows = defaultdict(float)
                total_liquidity_in_cycle = 0
                for tx in cycle_transactions:
                    if tx["from"] in cycle and tx["to"] in cycle:
                        net_flows[tx["from"]] -= tx["amount"]
                        net_flows[tx["to"]] += tx["amount"]
                        total_liquidity_in_cycle += tx["amount"]

                is_optimizable = all(abs(net_flows.get(node, 0)) < 0.001 for node in cycle_nodes) and net_flows

                flow_rows = [
                    {"Participante": node, "Saldo líquido ($M)": f"{v:+.2f}"} for node, v in net_flows.items()
                ]
                st.dataframe(pd.DataFrame(flow_rows), hide_index=True, width="stretch")
                st.caption("Positivo = tem a receber no fim das contas. Negativo = ainda deve. Zero = a conta fecha sozinha.")

            with col2:
                if is_optimizable:
                    st.success("Este ciclo se cancela sozinho")
                    st.markdown(f"Ninguém precisa transferir dinheiro de verdade. Um total de **${total_liquidity_in_cycle}M** em pagamentos pode ser liberado só por compensação — como no exemplo da Ana, Bruno e Carla.")
                else:
                    st.error("Este ciclo não se cancela por completo")
                    st.markdown("As dívidas não se anulam perfeitamente — sobra uma diferença que só se resolve com dinheiro real (veja quem ficou com saldo positivo ou negativo na tabela ao lado).")
st.markdown("---")

st.header("Análise dos Resultados e Implicações")
st.markdown("""
A simulação demonstra de forma clara os dois cenários que uma câmara de compensação ("clearing house") pode encontrar.

-   **No Ciclo 1 (`Banco A -> Banco B -> Banco C -> Banco A`):** As obrigações se anulam perfeitamente, permitindo a compensação.
    -   **Análise para o Participante A:** A transação `C -> A` representa um **crédito** de $10M (a receber), enquanto a transação `A -> B` representa um **débito** de $10M (a pagar). O balanço é zero. O mesmo se aplica aos participantes B e C.
    -   **Resultado:** O sistema liquida $30M em valor total com uma necessidade de liquidez real de **zero**.

-   **No Ciclo 2 (`Banco X -> Banco Y -> Banco Z -> Banco X`):** As obrigações não são simétricas.
    -   **Análise para o Participante Z:** O **crédito** recebido de `Y -> Z` é de $8M, mas o **débito** devido em `Z -> X` é de apenas $7M. Isso resulta em um saldo positivo de +$1M para Z.
    -   **Resultado:** O ciclo não pode ser completamente compensado. A liquidação exigirá o uso de fundos reais para cobrir as diferenças.
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