from celery import shared_task
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


@shared_task
def run_etl_pipeline():
    """Daily 1:00 AM — Run ETL scripts 2 and 3"""
    try:
        script2 = os.path.join(BASE_DIR, 'et1', '02_clean_and_transform.py')
        script3 = os.path.join(BASE_DIR, 'et1', '03_load_to_warehouse.py')
        subprocess.run([sys.executable, script2], check=True)
        subprocess.run([sys.executable, script3], check=True)
        return "ETL pipeline completed"
    except Exception as e:
        return f"ETL failed: {str(e)}"


@shared_task
def score_all_companies():
    """Daily 2:00 AM — Recalculate health scores"""
    try:
        script = os.path.join(BASE_DIR, 'et1', '04_ml_scoring.py')
        subprocess.run([sys.executable, script], check=True)
        return "Scoring completed"
    except Exception as e:
        return f"Scoring failed: {str(e)}"


@shared_task
def generate_pros_cons():
    """Daily 2:30 AM — Generate pros and cons"""
    try:
        script = os.path.join(BASE_DIR, 'et1', '05_generate_pros_cons.py')
        subprocess.run([sys.executable, script], check=True)
        return "Pros cons generated"
    except Exception as e:
        return f"Pros cons failed: {str(e)}"


@shared_task
def detect_anomalies():
    """Weekly Sunday — Z-score anomaly detection"""
    try:
        from sqlalchemy import create_engine
        import pandas as pd
        import numpy as np
        from scipy import stats
        engine = create_engine(
            'postgresql://admin:password123@localhost:5432/nifty100_dw'
        )
        pl = pd.read_sql(
            "SELECT symbol, sales FROM fact_profit_loss", engine
        )
        pl['zscore'] = stats.zscore(pl['sales'].fillna(0))
        anomalies = pl[abs(pl['zscore']) > 2.5]
        return f"Detected {len(anomalies)} anomalies"
    except Exception as e:
        return f"Anomaly detection failed: {str(e)}"


@shared_task
def detect_trends():
    """Weekly Sunday — Linear regression trend analysis"""
    try:
        from sqlalchemy import create_engine
        import pandas as pd
        import numpy as np
        engine = create_engine(
            'postgresql://admin:password123@localhost:5432/nifty100_dw'
        )
        pl = pd.read_sql("""
            SELECT f.symbol, f.sales, y.sort_order
            FROM fact_profit_loss f
            JOIN dim_year y ON f.year_id = y.year_id
            WHERE y.is_ttm = false
            ORDER BY f.symbol, y.sort_order
        """, engine)
        trends = []
        for symbol in pl['symbol'].unique():
            comp = pl[pl['symbol'] == symbol].tail(5)
            if len(comp) >= 2:
                x = np.arange(len(comp))
                y_vals = comp['sales'].fillna(0).values
                slope = np.polyfit(x, y_vals, 1)[0]
                trend = 'UP' if slope > 0 else 'DOWN'
                trends.append({'symbol': symbol, 'trend': trend})
        return f"Trends detected for {len(trends)} companies"
    except Exception as e:
        return f"Trend detection failed: {str(e)}"


@shared_task
def invalidate_cache():
    """After score tasks — Clear Redis cache"""
    try:
        from django.core.cache import cache
        cache.clear()
        return "Cache cleared"
    except Exception as e:
        return f"Cache clear failed: {str(e)}"