# AI-Powered Mobile Sales Dashboard

A professional Streamlit dashboard for mobile sales, revenue, and 5G analytics. Designed to run in **PyCharm** or from the command line.

## Dataset

The app expects a CSV file named **`sales_data.csv`** in the project root with these columns:

| Column | Description |
|--------|-------------|
| Year | Calendar year |
| Quarter | 1–4 |
| Product Model | Model name |
| 5G Capability | Yes/No |
| Units Sold | Integer |
| Revenue ($) | Currency |
| Market Share (%) | Percentage |
| Regional 5G Coverage (%) | Percentage |
| 5G Subscribers (in Avg 5G Speed (Mbps)) | Numeric |
| Preference for 5G (%) | Percentage |
| Region | Region name |

If **`sales_data.csv`** does not exist, the app will **generate synthetic data** automatically and optionally save it for future runs.

## Setup & Run

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The dashboard will open in your browser (usually `http://localhost:8501`).

## Running in PyCharm

1. Open the project folder in PyCharm.
2. Set the project interpreter to the venv that has `streamlit` and `pandas` installed.
3. Open **Run** → **Edit Configurations**.
4. Add a new **Python** configuration:
   - **Script path**: leave empty or point to `streamlit`.
   - **Parameters**: `run app.py`
   - **Working directory**: project root (where `app.py` and `sales_data.csv` are).

   **Or** use a single command in **Parameters**:  
   `run app.py`  
   with **Script path** set to your `streamlit` executable (e.g. `C:\...\venv\Scripts\streamlit.exe`).

5. Run the configuration; the dashboard will start and open in the browser.

## Features

- **Sidebar filters**: Year, Product Model, Region (all work together).
- **Key metrics**: Total Units Sold, Total Revenue, Average Market Share.
- **Filtered data table**: Updates with selected filters.
- **Charts**: Line chart (Units Sold by Quarter), Bar chart (Revenue by Quarter).
- **5G insights**: Average Regional 5G Coverage and Average Preference for 5G with progress bars.

All metrics, table, and charts update automatically when you change any filter.
