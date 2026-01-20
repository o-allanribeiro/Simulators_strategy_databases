# Simulators Strategy Visualizations

This project provides interactive visualizations of data architecture strategies, specifically focusing on sharding and versioning. It is built using Python and Streamlit.

## Setup

1.  **Install Graphviz:**
    The visualizations depend on Graphviz. Please install it on your system first.
    - **Windows:** `choco install graphviz` or download from the official website.
    - **macOS:** `brew install graphviz`
    - **Linux (Ubuntu/Debian):** `sudo apt-get install graphviz`

2.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Simulators_strategy_visualizations
    ```

3.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Generate placeholder image:**
    The architecture page uses a placeholder image. To generate it, run the following command:
    ```bash
    python create_image.py
    ```

## Running the Application

To run the Streamlit application, execute the following command:

```bash
streamlit run app.py
```

This will open the application in your web browser.

## Project Structure

- **app.py**: The main Streamlit application entry point.
- **requirements.txt**: A list of Python packages required for the project.
- **pages/**: Contains the different pages of the Streamlit application.
  - **1_Sharding.py**: The page for sharding visualization.
  - **2_Versioning.py**: The page for versioning visualization.
  - **3_Architecture.py**: An overview of the architecture concepts.
- **visualizations/**: Contains the logic for creating the visualizations.
  - **sharding.py**: Logic for the sharding visualization.
  - **versioning.py**: Logic for the versioning visualization.
  - **utils.py**: Utility functions.
- **data/**: Contains data files for the visualizations.
  - **sharding-strategies.json**: Data about sharding strategies.
  - **versioning-strategies.json**: Data about versioning strategies.
- **assets/diagrams/**: Contains diagrams and images.
- **docs/**: Contains additional documentation.
- **README.md**: This file.
