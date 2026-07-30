"""Definição centralizada das páginas do app.

Mantido separado do app.py para que outras páginas possam importar e
referenciar as mesmas instâncias de Page (via st.page_link), em vez de
apontar para slugs de URL "adivinhados" a partir do nome do arquivo.
"""

import streamlit as st

# Nota: não passamos `url_path` customizado de propósito. Sem ele, o Page usa
# o nome inferido do arquivo (mesma lógica de streamlit.source_util.page_icon_and_name),
# que é o que AppTest.switch_page() também usa para achar a página nos testes.
# Um url_path customizado quebraria essa correspondência silenciosamente.

pg_inicio = st.Page("views/0_Inicio.py", title="Início", default=True)

pg_pessimista = st.Page(
    "views/1_A_Pessimistic_Locking.py",
    title="1. Controle Pessimista",
)
pg_otimista = st.Page(
    "views/2_Controle_de_Concorrencia_Otimista.py",
    title="2. Controle Otimista",
)
pg_sharding = st.Page(
    "views/3_Escalabilidade_com_Sharding.py",
    title="3. Write Sharding",
)
pg_netting = st.Page(
    "views/4_Netting_com_Grafos.py",
    title="4. Netting com Grafos",
)
pg_interbancaria = st.Page(
    "views/5_Estrategia_Interbancaria.py",
    title="5. Arquitetura Agregadora",
)

pg_matriz = st.Page(
    "views/6_Matriz_de_Decisao_Estrategica.py",
    title="6. Matriz de Decisão",
)

NAVIGATION = {
    "": [pg_inicio],
    "Estudos de Caso (Nível Micro/Macro)": [
        pg_pessimista,
        pg_otimista,
        pg_sharding,
        pg_netting,
        pg_interbancaria,
    ],
    "Síntese": [pg_matriz],
}
