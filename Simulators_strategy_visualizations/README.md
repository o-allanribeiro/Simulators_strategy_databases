# Simuladores de Estratégias de Banco de Dados

Este projeto é um painel didático e interativo, construído com Python e Streamlit, para visualizar como diferentes arquiteturas de banco de dados lidam com problemas de concorrência e escalabilidade em sistemas de pagamento (PIX).

Ele explora cenários práticos como bloqueios pessimistas, otimistas, sharding de escrita e consistência distribuída.

## Setup

1.  **Instale o Graphviz:**
    As visualizações de grafos dependem do Graphviz. Por favor, instale-o no seu sistema.
    - **Windows:** `choco install graphviz` ou baixe do site oficial.
    - **macOS:** `brew install graphviz`
    - **Linux (Ubuntu/Debian):** `sudo apt-get install graphviz`

2.  **Clone o repositório e entre na pasta:**
    ```bash
    git clone <repository-url>
    cd Simulators_strategy_visualizations
    ```

3.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
    ```

4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

## Executando a Aplicação

Para iniciar o painel de simulação, execute o comando:

```bash
streamlit run app.py
```

Isso abrirá a aplicação no seu navegador.

## Estrutura do Projeto

- **`app.py`**: O ponto de entrada principal, que serve como a página de boas-vindas.
- **`requirements.txt`**: Lista as dependências Python (`streamlit`, `pandas`, `numpy`, `graphviz`).
- **`pages/`**: Contém todas as páginas da aplicação, que são renderizadas na barra lateral.
  - **`1_A_Pessimistic_Locking.py`**: Simula o bloqueio pessimista (fila) em um Mainframe ou PostgreSQL.
  - **`2_B_Optimistic_Locking.py`**: Simula o bloqueio otimista (Compare-and-Swap) com DynamoDB.
  - **`3_C_Write_Sharding.py`**: Simula o sharding de escrita para escalar PIX Crédito.
  - **`4_D_Distributed_Consistency.py`**: Simula o consenso (Raft) para consistência global.
  - **`5_Matriz_de_Decisao.py`**: Apresenta uma análise comparativa das estratégias e arquiteturas.
  - **`6_Sharding_Teoria.py`**: Página teórica explicando o conceito de Sharding.
  - **`7_Versioning_Teoria.py`**: Página teórica explicando o conceito de Versionamento de Dados.
- **`visualizations/`**: Módulos Python que foram usados anteriormente para gerar visualizações (atualmente obsoletos, pois a lógica de visualização foi movida para dentro de cada página de cenário).
- **`docs/`**: Documentação de suporte original.