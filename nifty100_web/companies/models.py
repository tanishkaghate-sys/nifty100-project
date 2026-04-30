from django.db import models

class DimCompany(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True)
    company_name = models.TextField(blank=True, null=True)
    sector = models.TextField(blank=True, null=True)
    company_logo = models.TextField(blank=True, null=True)
    website = models.TextField(blank=True, null=True)
    nse_url = models.TextField(blank=True, null=True)
    bse_url = models.TextField(blank=True, null=True)
    face_value = models.FloatField(blank=True, null=True)
    book_value = models.FloatField(blank=True, null=True)
    roce_percentage = models.FloatField(blank=True, null=True)
    roe_percentage = models.FloatField(blank=True, null=True)
    about_company = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dim_company'

class DimYear(models.Model):
    year_id = models.AutoField(primary_key=True)
    year_label = models.CharField(unique=True, max_length=20, blank=True, null=True)
    fiscal_year = models.IntegerField(blank=True, null=True)
    is_ttm = models.BooleanField(blank=True, null=True)
    sort_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'dim_year'

class FactProfitLoss(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.TextField(blank=True, null=True)
    year_id = models.BigIntegerField(blank=True, null=True)
    sales = models.BigIntegerField(blank=True, null=True)
    expenses = models.BigIntegerField(blank=True, null=True)
    operating_profit = models.FloatField(blank=True, null=True)
    opm_percentage = models.FloatField(blank=True, null=True)
    other_income = models.BigIntegerField(blank=True, null=True)
    interest = models.BigIntegerField(blank=True, null=True)
    depreciation = models.BigIntegerField(blank=True, null=True)
    profit_before_tax = models.BigIntegerField(blank=True, null=True)
    tax_percentage = models.FloatField(blank=True, null=True)
    net_profit = models.BigIntegerField(blank=True, null=True)
    eps = models.FloatField(blank=True, null=True)
    dividend_payout = models.FloatField(blank=True, null=True)
    net_profit_margin_pct = models.FloatField(blank=True, null=True)
    expense_ratio_pct = models.FloatField(blank=True, null=True)
    interest_coverage = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fact_profit_loss'

class FactBalanceSheet(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.TextField(blank=True, null=True)
    year_id = models.BigIntegerField(blank=True, null=True)
    equity_capital = models.FloatField(blank=True, null=True)
    reserves = models.BigIntegerField(blank=True, null=True)
    borrowings = models.BigIntegerField(blank=True, null=True)
    other_liabilities = models.BigIntegerField(blank=True, null=True)
    total_liabilities = models.BigIntegerField(blank=True, null=True)
    fixed_assets = models.BigIntegerField(blank=True, null=True)
    cwip = models.BigIntegerField(blank=True, null=True)
    investments = models.BigIntegerField(blank=True, null=True)
    other_assets = models.BigIntegerField(blank=True, null=True)
    total_assets = models.BigIntegerField(blank=True, null=True)
    debt_to_equity = models.FloatField(blank=True, null=True)
    equity_ratio = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fact_balance_sheet'

class FactCashFlow(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.TextField(blank=True, null=True)
    year_id = models.BigIntegerField(blank=True, null=True)
    operating_activity = models.FloatField(blank=True, null=True)
    investing_activity = models.FloatField(blank=True, null=True)
    financing_activity = models.FloatField(blank=True, null=True)
    net_cash_flow = models.FloatField(blank=True, null=True)
    free_cash_flow = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fact_cash_flow'

class FactMLScores(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.CharField(max_length=20, blank=True, null=True)
    profitability_score = models.IntegerField(blank=True, null=True)
    leverage_score = models.IntegerField(blank=True, null=True)
    cashflow_score = models.IntegerField(blank=True, null=True)
    efficiency_score = models.IntegerField(blank=True, null=True)
    interest_cov_score = models.IntegerField(blank=True, null=True)
    overall_score = models.IntegerField(blank=True, null=True)
    health_label = models.CharField(max_length=20, blank=True, null=True)
    color_hex = models.CharField(max_length=10, blank=True, null=True)
    computed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fact_ml_scores'

class FactProsCons(models.Model):
    id = models.AutoField(primary_key=True)
    symbol = models.TextField(blank=True, null=True)
    pros = models.TextField(blank=True, null=True)
    cons = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fact_pros_cons'