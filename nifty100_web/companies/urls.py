from django.urls import path
from . import views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Company endpoints
    path('companies/',
         views.CompanyListView.as_view(),
         name='company-list'),

    path('companies/<str:symbol>/',
         views.CompanyDetailView.as_view(),
         name='company-detail'),

    path('companies/<str:symbol>/overview/',
         views.company_overview,
         name='company-overview'),

    path('companies/<str:symbol>/financials/profit-loss/',
         views.ProfitLossView.as_view(),
         name='profit-loss'),

    path('companies/<str:symbol>/financials/balance-sheet/',
         views.BalanceSheetView.as_view(),
         name='balance-sheet'),

    path('companies/<str:symbol>/financials/cash-flow/',
         views.CashFlowView.as_view(),
         name='cash-flow'),

    # Health scores
    path('health-scores/',
         views.HealthScoresView.as_view(),
         name='health-scores'),

    path('health-scores/<str:symbol>/',
         views.CompanyHealthView.as_view(),
         name='company-health'),

    # Sectors
    path('sectors/',
         views.sector_summary,
         name='sectors'),

    # API Documentation
    path('schema/',
         SpectacularAPIView.as_view(),
         name='schema'),

    path('docs/',
         SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
]