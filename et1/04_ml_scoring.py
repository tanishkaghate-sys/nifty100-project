import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://admin:password123@localhost:5432/nifty100_dw')

print("Loading data from warehouse...")

# Load latest year data for each company
pl = pd.read_sql("""
    SELECT f.symbol, f.sales, f.net_profit, f.operating_profit,
           f.interest, f.net_profit_margin_pct, f.opm_percentage,
           f.interest_coverage, f.eps, f.dividend_payout
    FROM fact_profit_loss f
    INNER JOIN dim_year y ON f.year_id = y.year_id
    WHERE y.is_ttm = true
       OR y.sort_order = (
           SELECT MAX(sort_order) FROM dim_year WHERE is_ttm = false
       )
""", engine)

bs = pd.read_sql("""
    SELECT f.symbol, f.debt_to_equity, f.equity_ratio,
           f.total_assets, f.borrowings, f.reserves
    FROM fact_balance_sheet f
    INNER JOIN dim_year y ON f.year_id = y.year_id
    WHERE y.sort_order = (SELECT MAX(sort_order) FROM dim_year)
""", engine)

cf = pd.read_sql("""
    SELECT f.symbol, f.free_cash_flow, f.operating_activity,
           f.net_cash_flow
    FROM fact_cash_flow f
    INNER JOIN dim_year y ON f.year_id = y.year_id
    WHERE y.sort_order = (SELECT MAX(sort_order) FROM dim_year)
""", engine)

# Merge all data
data = pl.merge(bs, on='symbol', how='left')
data = data.merge(cf, on='symbol', how='left')
print(f"Loaded {len(data)} companies for scoring")

# ============================================================
# SCORING FUNCTIONS (0-20 points each = 100 total)
# ============================================================

def score_profitability(row):
    """Score based on net profit margin (0-20)"""
    margin = row.get('net_profit_margin_pct', 0) or 0
    if margin >= 20:   return 20
    elif margin >= 15: return 17
    elif margin >= 10: return 14
    elif margin >= 5:  return 10
    elif margin >= 0:  return 6
    else:              return 2

def score_leverage(row):
    """Score based on debt to equity (0-20) — lower is better"""
    dte = row.get('debt_to_equity', 0) or 0
    if dte <= 0:    return 20  # debt free
    elif dte <= 0.5: return 18
    elif dte <= 1:   return 15
    elif dte <= 2:   return 10
    elif dte <= 3:   return 6
    else:            return 2

def score_cashflow(row):
    """Score based on free cash flow (0-20)"""
    fcf = row.get('free_cash_flow', 0) or 0
    ops = row.get('operating_activity', 1) or 1
    if fcf > 0 and ops > 0:    return 20
    elif fcf > 0:               return 15
    elif fcf > -1000:           return 10
    else:                       return 4

def score_efficiency(row):
    """Score based on OPM% (0-20)"""
    opm = row.get('opm_percentage', 0) or 0
    if opm >= 30:   return 20
    elif opm >= 20: return 17
    elif opm >= 15: return 14
    elif opm >= 10: return 10
    elif opm >= 5:  return 6
    else:           return 2

def score_interest_coverage(row):
    """Score based on interest coverage (0-20)"""
    ic = row.get('interest_coverage', 0) or 0
    if ic >= 10:   return 20
    elif ic >= 5:  return 16
    elif ic >= 3:  return 12
    elif ic >= 1:  return 8
    elif ic >= 0:  return 4
    else:          return 1

def get_health_label(score):
    """Convert score to health label"""
    if score >= 80:   return 'EXCELLENT', '#2ecc71'
    elif score >= 65: return 'GOOD',      '#27ae60'
    elif score >= 50: return 'AVERAGE',   '#f39c12'
    elif score >= 35: return 'WEAK',      '#e67e22'
    else:             return 'POOR',      '#e74c3c'

# ============================================================
# COMPUTE SCORES
# ============================================================
print("Computing health scores...")

results = []
for _, row in data.iterrows():
    prof  = score_profitability(row)
    lev   = score_leverage(row)
    cf_s  = score_cashflow(row)
    eff   = score_efficiency(row)
    ic    = score_interest_coverage(row)

    total = prof + lev + cf_s + eff + ic
    label, color = get_health_label(total)

    results.append({
        'symbol':               row['symbol'],
        'profitability_score':  prof,
        'leverage_score':       lev,
        'cashflow_score':       cf_s,
        'efficiency_score':     eff,
        'interest_cov_score':   ic,
        'overall_score':        total,
        'health_label':         label,
        'color_hex':            color,
        'computed_at':          pd.Timestamp.now()
    })

scores_df = pd.DataFrame(results)

# ============================================================
# SAVE TO WAREHOUSE
# ============================================================
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS fact_ml_scores CASCADE"))
    conn.execute(text("""
        CREATE TABLE fact_ml_scores (
            symbol VARCHAR(20),
            profitability_score INT,
            leverage_score INT,
            cashflow_score INT,
            efficiency_score INT,
            interest_cov_score INT,
            overall_score INT,
            health_label VARCHAR(20),
            color_hex VARCHAR(10),
            computed_at TIMESTAMP
        )
    """))
    conn.commit()

scores_df.to_sql('fact_ml_scores', engine, if_exists='append', index=False)
print(f"Scores saved for {len(scores_df)} companies")

# ============================================================
# PRINT RESULTS
# ============================================================
print("\nHealth Score Summary:")
print(scores_df['health_label'].value_counts().to_string())
print()
print("Top 10 Healthiest Companies:")
top10 = scores_df.nlargest(10, 'overall_score')[
    ['symbol', 'overall_score', 'health_label']
]
print(top10.to_string(index=False))
print()
print("Bottom 10 Companies:")
bottom10 = scores_df.nsmallest(10, 'overall_score')[
    ['symbol', 'overall_score', 'health_label']
]
print(bottom10.to_string(index=False))