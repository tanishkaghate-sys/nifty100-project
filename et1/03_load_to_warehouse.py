import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os

# ============================================================
# CONNECTION
# ============================================================
engine = create_engine('postgresql://admin:password123@localhost:5432/nifty100_dw')

def run_sql(sql):
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

def load_table(df, table_name, if_exists='replace'):
    # Drop table with CASCADE first to handle foreign key dependencies
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
        conn.commit()
    df.to_sql(table_name, engine, if_exists='append', index=False)
    print(f" {table_name}: {len(df)} rows loaded")
# ============================================================
# STEP 1 — CREATE SCHEMA (Drop and recreate cleanly)
# ============================================================
print("Creating schema...")

run_sql("""
    DROP TABLE IF EXISTS fact_analysis CASCADE;
    DROP TABLE IF EXISTS fact_cash_flow CASCADE;
    DROP TABLE IF EXISTS fact_balance_sheet CASCADE;
    DROP TABLE IF EXISTS fact_profit_loss CASCADE;
    DROP TABLE IF EXISTS fact_pros_cons CASCADE;
    DROP TABLE IF EXISTS fact_documents CASCADE;
    DROP TABLE IF EXISTS dim_company CASCADE;
    DROP TABLE IF EXISTS dim_year CASCADE;
    DROP TABLE IF EXISTS dim_sector CASCADE;
""")

# Also drop via pandas if tables exist
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS dim_company CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS dim_year CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS dim_sector CASCADE"))
    conn.commit()

run_sql("""
    CREATE TABLE dim_sector (
        sector_id SERIAL PRIMARY KEY,
        sector_name VARCHAR(100) UNIQUE
    );
""")

run_sql("""
    CREATE TABLE dim_company (
        symbol VARCHAR(20) PRIMARY KEY,
        company_name VARCHAR(200),
        sector VARCHAR(100),
        company_logo VARCHAR(500),
        website VARCHAR(500),
        nse_url VARCHAR(500),
        bse_url VARCHAR(500),
        face_value DECIMAL(10,2),
        book_value DECIMAL(15,2),
        roce_percentage DECIMAL(10,2),
        roe_percentage DECIMAL(10,2),
        about_company TEXT
    );
""")

run_sql("""
    CREATE TABLE dim_year (
        year_id SERIAL PRIMARY KEY,
        year_label VARCHAR(20) UNIQUE,
        fiscal_year INT,
        is_ttm BOOLEAN DEFAULT FALSE,
        sort_order INT
    );
""")

run_sql("""
    CREATE TABLE fact_profit_loss (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) REFERENCES dim_company(symbol),
        year_id INT REFERENCES dim_year(year_id),
        sales DECIMAL(20,2),
        expenses DECIMAL(20,2),
        operating_profit DECIMAL(20,2),
        opm_percentage DECIMAL(10,2),
        other_income DECIMAL(20,2),
        interest DECIMAL(20,2),
        depreciation DECIMAL(20,2),
        profit_before_tax DECIMAL(20,2),
        tax_percentage DECIMAL(10,2),
        net_profit DECIMAL(20,2),
        eps DECIMAL(10,2),
        dividend_payout DECIMAL(10,2),
        net_profit_margin_pct DECIMAL(10,2),
        expense_ratio_pct DECIMAL(10,2),
        interest_coverage DECIMAL(10,2),
        UNIQUE(symbol, year_id)
    );
""")

run_sql("""
    CREATE TABLE fact_balance_sheet (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) REFERENCES dim_company(symbol),
        year_id INT REFERENCES dim_year(year_id),
        equity_capital DECIMAL(20,2),
        reserves DECIMAL(20,2),
        borrowings DECIMAL(20,2),
        other_liabilities DECIMAL(20,2),
        total_liabilities DECIMAL(20,2),
        fixed_assets DECIMAL(20,2),
        cwip DECIMAL(20,2),
        investments DECIMAL(20,2),
        other_assets DECIMAL(20,2),
        total_assets DECIMAL(20,2),
        debt_to_equity DECIMAL(10,4),
        equity_ratio DECIMAL(10,4),
        UNIQUE(symbol, year_id)
    );
""")

run_sql("""
    CREATE TABLE fact_cash_flow (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) REFERENCES dim_company(symbol),
        year_id INT REFERENCES dim_year(year_id),
        operating_activity DECIMAL(20,2),
        investing_activity DECIMAL(20,2),
        financing_activity DECIMAL(20,2),
        net_cash_flow DECIMAL(20,2),
        free_cash_flow DECIMAL(20,2),
        UNIQUE(symbol, year_id)
    );
""")

run_sql("""
    CREATE TABLE fact_analysis (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) REFERENCES dim_company(symbol),
        period VARCHAR(10),
        sales_growth_pct DECIMAL(10,2),
        profit_growth_pct DECIMAL(10,2),
        stock_cagr_pct DECIMAL(10,2),
        roe_pct DECIMAL(10,2),
        UNIQUE(symbol, period)
    );
""")

run_sql("""
    CREATE TABLE fact_pros_cons (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) REFERENCES dim_company(symbol),
        pros TEXT,
        cons TEXT
    );
""")

run_sql("""
    CREATE TABLE fact_documents (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) REFERENCES dim_company(symbol),
        year VARCHAR(20),
        annual_report VARCHAR(1000)
    );
""")

print(" Schema created\n")

# ============================================================
# STEP 2 — LOAD DIMENSION TABLES FIRST
# ============================================================
print("Loading dimension tables...")

# dim_sector
sectors = pd.read_csv("data/sector_mapping.csv")
sector_names = pd.DataFrame({'sector_name': sectors['sector'].unique()})
load_table(sector_names, 'dim_sector')

# dim_company
companies = pd.read_csv("data/clean/companies.csv")
sector_map = pd.read_csv("data/sector_mapping.csv")

# Rename id → symbol to match schema
companies = companies.rename(columns={
    'id': 'symbol',
    'company_logo': 'company_logo',
    'nse_profile': 'nse_url',
    'bse_profile': 'bse_url',
    'roce_percentage': 'roce_percentage',
    'roe_percentage': 'roe_percentage'
})

# Merge sector info
companies = companies.merge(
    sector_map.rename(columns={'company_id': 'symbol'}),
    on='symbol', how='left'
)

dim_company = companies[[
    'symbol', 'company_name', 'sector', 'company_logo',
    'website', 'nse_url', 'bse_url', 'face_value',
    'book_value', 'roce_percentage', 'roe_percentage', 'about_company'
]]
load_table(dim_company, 'dim_company')

# dim_year — collect all unique years across all fact tables
pl_years = pd.read_csv("data/clean/profitandloss.csv")[['year','fiscal_year','sort_order','is_ttm']]
bs_years = pd.read_csv("data/clean/balancesheet.csv")[['year','fiscal_year','sort_order','is_ttm']]
cf_years = pd.read_csv("data/clean/cashflow.csv")[['year','fiscal_year','sort_order','is_ttm']]

all_years = pd.concat([pl_years, bs_years, cf_years]).drop_duplicates(subset=['year'])
all_years = all_years.rename(columns={'year': 'year_label'})
all_years = all_years.dropna(subset=['year_label'])
all_years = all_years.sort_values('sort_order')

# Insert manually so SERIAL year_id is auto-generated by PostgreSQL
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS dim_year CASCADE"))
    conn.execute(text("""
        CREATE TABLE dim_year (
            year_id SERIAL PRIMARY KEY,
            year_label VARCHAR(20) UNIQUE,
            fiscal_year INT,
            is_ttm BOOLEAN DEFAULT FALSE,
            sort_order INT
        )
    """))
    for _, row in all_years.iterrows():
        conn.execute(text("""
            INSERT INTO dim_year (year_label, fiscal_year, is_ttm, sort_order)
            VALUES (:year_label, :fiscal_year, :is_ttm, :sort_order)
            ON CONFLICT (year_label) DO NOTHING
        """), {
            'year_label': row['year_label'],
            'fiscal_year': None if row['fiscal_year'] == 9999 else int(row['fiscal_year']),
            'is_ttm': bool(row['is_ttm']),
            'sort_order': int(row['sort_order'])
        })
    conn.commit()
print(f"dim_year: {len(all_years)} rows loaded")

print()

# ============================================================
# STEP 3 — LOAD FACT TABLES
# ============================================================
print(" Loading fact tables...")

# Get year_id lookup
years_lookup = pd.read_sql("SELECT year_id, year_label FROM dim_year", engine)

def add_year_id(df, year_col='year'):
    return df.merge(years_lookup, left_on=year_col, right_on='year_label', how='left')

# fact_profit_loss
pl = pd.read_csv("data/clean/profitandloss.csv")
pl = add_year_id(pl)
pl = pl.rename(columns={'company_id': 'symbol'})
fact_pl = pl[[
    'symbol', 'year_id', 'sales', 'expenses', 'operating_profit',
    'opm_percentage', 'other_income', 'interest', 'depreciation',
    'profit_before_tax', 'tax_percentage', 'net_profit', 'eps',
    'dividend_payout', 'net_profit_margin_pct', 'expense_ratio_pct',
    'interest_coverage'
]].drop_duplicates(subset=['symbol', 'year_id'])
load_table(fact_pl, 'fact_profit_loss')

# fact_balance_sheet
bs = pd.read_csv("data/clean/balancesheet.csv")
bs = add_year_id(bs)
bs = bs.rename(columns={'company_id': 'symbol', 'other_asset': 'other_assets'})
fact_bs = bs[[
    'symbol', 'year_id', 'equity_capital', 'reserves', 'borrowings',
    'other_liabilities', 'total_liabilities', 'fixed_assets', 'cwip',
    'investments', 'other_assets', 'total_assets',
    'debt_to_equity', 'equity_ratio'
]].drop_duplicates(subset=['symbol', 'year_id'])
load_table(fact_bs, 'fact_balance_sheet')

# fact_cash_flow
cf = pd.read_csv("data/clean/cashflow.csv")
cf = add_year_id(cf)
cf = cf.rename(columns={'company_id': 'symbol'})
fact_cf = cf[[
    'symbol', 'year_id', 'operating_activity', 'investing_activity',
    'financing_activity', 'net_cash_flow', 'free_cash_flow'
]].drop_duplicates(subset=['symbol', 'year_id'])
load_table(fact_cf, 'fact_cash_flow')

# fact_analysis
an = pd.read_csv("data/clean/analysis.csv")
an = an.rename(columns={'company_id': 'symbol'})
load_table(an, 'fact_analysis')

# fact_pros_cons
pc = pd.read_csv("data/clean/prosandcons.csv")
pc = pc.rename(columns={'company_id': 'symbol'})
fact_pc = pc[['symbol', 'pros', 'cons']]
load_table(fact_pc, 'fact_pros_cons')

# fact_documents
docs = pd.read_csv("data/clean/documents.csv")
docs = docs.rename(columns={'company_id': 'symbol', 'Year': 'year', 'Annual_Report': 'annual_report'})
fact_docs = docs[['symbol', 'year', 'annual_report']]
load_table(fact_docs, 'fact_documents')

print()

# ============================================================
# STEP 4 — DATA QUALITY CHECKS
# ============================================================
print("Running data quality checks...")

checks = {
    "Total companies":        "SELECT COUNT(*) as count FROM dim_company",
    "Total years":            "SELECT COUNT(*) as count FROM dim_year",
    "Profit & Loss rows":     "SELECT COUNT(*) as count FROM fact_profit_loss",
    "Balance Sheet rows":     "SELECT COUNT(*) as count FROM fact_balance_sheet",
    "Cash Flow rows":         "SELECT COUNT(*) as count FROM fact_cash_flow",
    "Analysis rows":          "SELECT COUNT(*) as count FROM fact_analysis",
    "Pros & Cons rows":       "SELECT COUNT(*) as count FROM fact_pros_cons",
    "Documents rows":         "SELECT COUNT(*) as count FROM fact_documents",
    "Null profits":           "SELECT COUNT(*) as count FROM fact_profit_loss WHERE net_profit IS NULL",
    "Duplicate PL rows":      "SELECT COUNT(*) as count FROM (SELECT symbol, year_id, COUNT(*) FROM fact_profit_loss GROUP BY symbol, year_id HAVING COUNT(*) > 1) x",
}

print()
print(f"{'Check':<25} {'Result':>10}")
print("-" * 37)
with engine.connect() as conn:
    for check_name, sql in checks.items():
        result = conn.execute(text(sql)).fetchone()
        print(f"{check_name:<25} {result[0]:>10}")

print()
print(" Warehouse loaded successfully!")