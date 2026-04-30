import re
import pandas as pd
import numpy as np
import os

os.makedirs("data/clean", exist_ok=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def standardize_year(raw_year):
    """Convert any year format to 'Mar 2024' style"""
    if pd.isna(raw_year):
        return np.nan
    
    raw = str(raw_year).strip()
    
    if raw.upper() == 'TTM':
        return 'TTM'
    
    # Already correct: 'Mar 2024'
    if re.match(r'[A-Za-z]{3}\s\d{4}', raw):
        return raw
    
    # Short format: 'Mar-24' → 'Mar 2024'
    if re.match(r'[A-Za-z]{3}-\d{2}$', raw):
        month, yr = raw.split('-')
        full_year = '20' + yr if int(yr) <= 50 else '19' + yr
        return f"{month} {full_year}"
    
    return raw

def get_fiscal_year(year_label):
    """Extract integer year: 'Mar 2024' → 2024, TTM → 9999"""
    if pd.isna(year_label) or str(year_label).strip().upper() == 'TTM':
        return 9999
    match = re.search(r'\d{4}', str(year_label))
    return int(match.group()) if match else None

def get_sort_order(year_label):
    """Assign sort order for chronological sorting"""
    if pd.isna(year_label) or str(year_label).strip().upper() == 'TTM':
        return 99999
    fy = get_fiscal_year(year_label)
    month_order = {'Mar': 4, 'Sep': 10, 'Jun': 7, 'Dec': 1}
    month = str(year_label)[:3]
    return fy * 100 + month_order.get(month, 0) if fy else 0

def clean_numeric(df, columns):
    """Convert columns to numeric, replacing errors with NaN"""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def replace_nulls(df):
    """Replace string NULLs with actual NaN"""
    return df.replace(['NULL', 'Null', 'null', 'None', '', ' '], np.nan)

# ============================================================
# 1. COMPANIES TABLE
# ============================================================
print(" Cleaning companies...")
companies = pd.read_csv("data/raw/companies.csv")
companies = replace_nulls(companies)
companies.columns = companies.columns.str.strip()

# Clean company name
if 'company_name' in companies.columns:
    companies['company_name'] = companies['company_name'].str.strip()

numeric_cols = ['roce', 'roe', 'face_value', 'book_value']
companies = clean_numeric(companies, numeric_cols)

companies.to_csv("data/clean/companies.csv", index=False)
print(f" companies: {len(companies)} rows")
print(f"   Columns: {list(companies.columns)}\n")

# ============================================================
# 2. BALANCE SHEET
# ============================================================
print(" Cleaning balancesheet...")
bs = pd.read_csv("data/raw/balancesheet.csv")
bs = replace_nulls(bs)
bs.columns = bs.columns.str.strip().str.lower()

# Standardize year
bs['year'] = bs['year'].apply(standardize_year)
bs['fiscal_year'] = bs['year'].apply(get_fiscal_year)
bs['sort_order'] = bs['year'].apply(get_sort_order)
bs['is_ttm'] = bs['year'] == 'TTM'

# Clean numeric columns
numeric_cols = ['equity_capital', 'reserves', 'borrowings', 'other_liabilities',
                'total_liabilities', 'fixed_assets', 'cwip', 'investments',
                'other_assets', 'total_assets']
bs = clean_numeric(bs, numeric_cols)

# Compute debt_to_equity
bs['equity'] = bs['equity_capital'].fillna(0) + bs['reserves'].fillna(0)
bs['debt_to_equity'] = np.where(
    bs['equity'] != 0,
    bs['borrowings'] / bs['equity'],
    np.nan
)

# Compute equity_ratio
bs['equity_ratio'] = np.where(
    bs['total_assets'] != 0,
    bs['equity'] / bs['total_assets'],
    np.nan
)

bs.to_csv("data/clean/balancesheet.csv", index=False)
print(f" balancesheet: {len(bs)} rows")
print(f"   Columns: {list(bs.columns)}\n")

# ============================================================
# 3. PROFIT & LOSS
# ============================================================
print(" Cleaning profitandloss...")
pl = pd.read_csv("data/raw/profitandloss.csv")
pl = replace_nulls(pl)
pl.columns = pl.columns.str.strip().str.lower()

# Standardize year
pl['year'] = pl['year'].apply(standardize_year)
pl['fiscal_year'] = pl['year'].apply(get_fiscal_year)
pl['sort_order'] = pl['year'].apply(get_sort_order)
pl['is_ttm'] = pl['year'] == 'TTM'

# Clean numeric columns
numeric_cols = ['sales', 'expenses', 'operating_profit', 'opm_percentage',
                'other_income', 'interest', 'depreciation', 'profit_before_tax',
                'tax_percentage', 'net_profit', 'eps', 'dividend_payout']
pl = clean_numeric(pl, numeric_cols)

# Compute derived metrics
pl['net_profit_margin_pct'] = np.where(
    pl['sales'] != 0,
    (pl['net_profit'] / pl['sales']) * 100,
    np.nan
)
pl['expense_ratio_pct'] = np.where(
    pl['sales'] != 0,
    (pl['expenses'] / pl['sales']) * 100,
    np.nan
)
pl['interest_coverage'] = np.where(
    pl['interest'] != 0,
    pl['operating_profit'] / pl['interest'],
    np.nan
)

pl.to_csv("data/clean/profitandloss.csv", index=False)
print(f" profitandloss: {len(pl)} rows")
print(f"   Columns: {list(pl.columns)}\n")

# ============================================================
# 4. CASH FLOW
# ============================================================
print(" Cleaning cashflow...")
cf = pd.read_csv("data/raw/cashflow.csv")
cf = replace_nulls(cf)
cf.columns = cf.columns.str.strip().str.lower()

# Standardize year
cf['year'] = cf['year'].apply(standardize_year)
cf['fiscal_year'] = cf['year'].apply(get_fiscal_year)
cf['sort_order'] = cf['year'].apply(get_sort_order)
cf['is_ttm'] = cf['year'] == 'TTM'

# Identify cash flow columns dynamically
print(f"   Raw columns: {list(cf.columns)}")

# Clean numeric columns (adjust names based on actual columns)
numeric_cols = [col for col in cf.columns 
                if col not in ['company_id', 'year', 'fiscal_year', 
                               'sort_order', 'is_ttm', 'id']]
cf = clean_numeric(cf, numeric_cols)

# Compute free cash flow (operating + investing)
if 'operating_activity' in cf.columns and 'investing_activity' in cf.columns:
    cf['free_cash_flow'] = cf['operating_activity'] + cf['investing_activity']
elif 'cash_from_operating_activity' in cf.columns:
    cf['free_cash_flow'] = cf['cash_from_operating_activity'] + cf.get('cash_from_investing_activity', 0)

cf.to_csv("data/clean/cashflow.csv", index=False)
print(f" cashflow: {len(cf)} rows")
print(f"   Columns: {list(cf.columns)}\n")

# ============================================================
# 5. ANALYSIS (with period parsing)
# ============================================================
print("Cleaning analysis...")
an = pd.read_csv("data/raw/analysis.csv")
an = replace_nulls(an)
an.columns = an.columns.str.strip().str.lower()

def extract_period(text):
    """Extract period label from '10 Years: 21%' → '10Y'"""
    if pd.isna(text):
        return None
    text = str(text).strip()
    if '10' in text:   return '10Y'
    if '5' in text:    return '5Y'
    if '3' in text:    return '3Y'
    if 'TTM' in text or 'Last' in text or '1 Year' in text: return 'TTM'
    return None

def extract_value(text):
    """Extract number from '10 Years: 21%' → 21.0"""
    if pd.isna(text):
        return None
    match = re.search(r'-?\d+\.?\d*', str(text))
    return float(match.group()) if match else None

# Parse each row — period comes from any column (they all have same period per row)
an['period'] = an['compounded_sales_growth'].apply(extract_period)

# Extract numeric values from each column
an['sales_growth_pct']   = an['compounded_sales_growth'].apply(extract_value)
an['profit_growth_pct']  = an['compounded_profit_growth'].apply(extract_value)
an['stock_cagr_pct']     = an['stock_price_cagr'].apply(extract_value)
an['roe_pct']            = an['roe'].apply(extract_value)

# Keep only clean columns
an_clean = an[['company_id', 'period', 'sales_growth_pct', 
                'profit_growth_pct', 'stock_cagr_pct', 'roe_pct']].copy()

an_clean.dropna(subset=['period'], inplace=True)

an_clean.to_csv("data/clean/analysis.csv", index=False)
print(f"analysis: {len(an_clean)} rows")
print(f"   Columns: {list(an_clean.columns)}")
print(f"   Companies: {sorted(an_clean['company_id'].unique())}")
print(f"   Periods: {sorted(an_clean['period'].unique())}\n")

# ============================================================
# 6. PROS AND CONS
# ============================================================
print(" Cleaning prosandcons...")
pc = pd.read_csv("data/raw/prosandcons.csv")
pc = replace_nulls(pc)
pc.columns = pc.columns.str.strip().str.lower()

pc['pros'] = pc['pros'].str.strip() if 'pros' in pc.columns else pc['pros']
pc['cons'] = pc['cons'].str.strip() if 'cons' in pc.columns else pc['cons']

pc.to_csv("data/clean/prosandcons.csv", index=False)
print(f" prosandcons: {len(pc)} rows")
print(f"   Columns: {list(pc.columns)}\n")

# ============================================================
# 7. DOCUMENTS
# ============================================================
print(" Cleaning documents...")
docs = pd.read_csv("data/raw/documents.csv")
docs = replace_nulls(docs)
docs.columns = docs.columns.str.strip()

docs.to_csv("data/clean/documents.csv", index=False)
print(f" documents: {len(docs)} rows")
print(f"   Columns: {list(docs.columns)}\n")

# ============================================================
# 8. SECTOR MAPPING (Create manually)
# ============================================================
print(" Creating sector mapping...")
sector_data = {
    'company_id': [
        'TCS','INFY','WIPRO','HCLTECH','TECHM','LTIM','PERSISTENT','COFORGE','MPHASIS','OFSS',
        'HDFCBANK','ICICIBANK','KOTAKBANK','AXISBANK','SBIN','BANKBARODA','CANARABANK','FEDERALBNK','IDFCFIRSTB','INDUSINDBK',
        'BAJFINANCE','BAJAJFINSV','CHOLAFIN','MUTHOOTFIN','SHRIRAMFIN',
        'SBILIFE','HDFCLIFE','ICICIGI','SBICARD',
        'RELIANCE','ONGC','IOC','BPCL','HINDPETRO','GAIL',
        'ADANIGREEN','ADANIPOWER','ADANIENSOL','ATGL','TATAPOWER','NTPC','POWERGRID',
        'ADANIPORTS','ADANIENT',
        'AMBUJACEM','ULTRACEMCO','SHREECEM',
        'APOLLOHOSP','MAXHEALTH','FORTIS','CIPLA','SUNPHARMA','DRREDDY','DIVISLAB','AUROPHARMA',
        'ASIANPAINT','BERGEPAINT',
        'HINDUNILVR','NESTLEIND','BRITANNIA','DABUR','GODREJCP','MARICO','COLPAL','TATACONSUM',
        'MARUTI','TATAMOTORS','M&M','BAJAJ-AUTO','EICHERMOT','HEROMOTOCO','TVSMOTORS',
        'TITAN','TRENT','DMART','VEDL','HINDALCO','JSWSTEEL','TATASTEEL','SAIL',
        'LTTS','HDFCAMC','PIDILITIND','SIEMENS','ABB','HAVELLS','VOLTAS',
        'ZOMATO','PAYTM','NYKAA','POLICYBZR',
        'IRCTC','DLF','LODHA','OBEROIRLTY',
        'COALINDIA','NMDC',
        'JIO','BHARTIARTL','IDEA',
        'GRASIM','UPL','INDIGO'
    ],
    'sector': [
        'IT','IT','IT','IT','IT','IT','IT','IT','IT','IT',
        'Banking','Banking','Banking','Banking','Banking','Banking','Banking','Banking','Banking','Banking',
        'NBFC','NBFC','NBFC','NBFC','NBFC',
        'Insurance','Insurance','Insurance','Insurance',
        'Energy','Energy','Energy','Energy','Energy','Energy',
        'Power','Power','Power','Power','Power','Power','Power',
        'Ports','Conglomerate',
        'Cement','Cement','Cement',
        'Healthcare','Healthcare','Healthcare','Pharma','Pharma','Pharma','Pharma','Pharma',
        'Paint','Paint',
        'FMCG','FMCG','FMCG','FMCG','FMCG','FMCG','FMCG','FMCG',
        'Auto','Auto','Auto','Auto','Auto','Auto','Auto',
        'Consumer Goods','Consumer Goods','Retail','Metals','Metals','Metals','Metals','Metals',
        'IT Services','Finance','Chemicals','Capital Goods','Capital Goods','Capital Goods','Capital Goods',
        'New Age Tech','New Age Tech','New Age Tech','New Age Tech',
        'Travel & Tourism','Real Estate','Real Estate','Real Estate',
        'Mining','Mining',
        'Telecom','Telecom','Telecom',
        'Diversified','Agro Chemicals','Aviation'
    ]
}

sector_df = pd.DataFrame(sector_data)
sector_df.to_csv("data/sector_mapping.csv", index=False)
print(f" sector_mapping: {len(sector_df)} companies mapped\n")

print(" All cleaning complete! Check data/clean/ folder.")