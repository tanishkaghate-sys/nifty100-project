import pandas as pd
import os

os.makedirs("data/raw", exist_ok=True)

tables = [
    "analysis",
    "balancesheet",
    "cashflow",
    "companies",
    "documents",
    "profitandloss",
    "prosandcons"
]

for table in tables:
    input_path = f"data/raw/{table}.xlsx"
    output_path = f"data/raw/{table}.csv"
    
    try:
        # skiprows=1 skips the title row "Bluestock Fintech — Nifty 100 | ..."
        df = pd.read_excel(input_path, engine='openpyxl', skiprows=1)
        
        # Drop completely empty rows and columns
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        # Save as CSV
        df.to_csv(output_path, index=False)
        
        print(f" {table}: {len(df)} rows, {len(df.columns)} columns")
        print(f"   Columns: {list(df.columns)}\n")
        
    except FileNotFoundError:
        print(f" {table}: File not found at {input_path}")
    except Exception as e:
        print(f" {table}: Error — {e}")

print("\n Extraction complete! Check data/raw/ for CSV files.")