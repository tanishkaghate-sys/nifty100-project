from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import (DimCompany, FactProfitLoss, FactBalanceSheet,
                     FactCashFlow, FactMLScores, FactProsCons)
from .serializers import (CompanySerializer, ProfitLossSerializer,
                          BalanceSheetSerializer, CashFlowSerializer,
                          MLScoreSerializer, ProsConsSerializer)

# ── Company Endpoints ──────────────────────────────────────

class CompanyListView(generics.ListAPIView):
    """List all 92 Nifty 100 companies"""
    queryset = DimCompany.objects.all().order_by('symbol')
    serializer_class = CompanySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['company_name', 'sector', 'symbol']

class CompanyDetailView(generics.RetrieveAPIView):
    """Get single company by symbol"""
    queryset = DimCompany.objects.all()
    serializer_class = CompanySerializer
    lookup_field = 'symbol'

# ── Financial Data Endpoints ───────────────────────────────

class ProfitLossView(generics.ListAPIView):
    """Get P&L data for a company"""
    serializer_class = ProfitLossSerializer

    def get_queryset(self):
        symbol = self.kwargs['symbol']
        return FactProfitLoss.objects.filter(symbol=symbol)

class BalanceSheetView(generics.ListAPIView):
    """Get Balance Sheet data for a company"""
    serializer_class = BalanceSheetSerializer

    def get_queryset(self):
        symbol = self.kwargs['symbol']
        return FactBalanceSheet.objects.filter(symbol=symbol)

class CashFlowView(generics.ListAPIView):
    """Get Cash Flow data for a company"""
    serializer_class = CashFlowSerializer

    def get_queryset(self):
        symbol = self.kwargs['symbol']
        return FactCashFlow.objects.filter(symbol=symbol)

# ── ML Score Endpoints ─────────────────────────────────────

class HealthScoresView(generics.ListAPIView):
    """Get ML health scores for all companies"""
    queryset = FactMLScores.objects.all().order_by('-overall_score')
    serializer_class = MLScoreSerializer

class CompanyHealthView(generics.ListAPIView):
    """Get health score for a specific company"""
    serializer_class = MLScoreSerializer

    def get_queryset(self):
        symbol = self.kwargs['symbol']
        return FactMLScores.objects.filter(symbol=symbol)

# ── Sector Endpoints ───────────────────────────────────────

@api_view(['GET'])
def sector_summary(request):
    """Get list of all sectors with company count"""
    from django.db.models import Count
    sectors = DimCompany.objects.values('sector').annotate(
        company_count=Count('symbol')
    ).order_by('sector')
    return Response(list(sectors))

@api_view(['GET'])
def company_overview(request, symbol):
    """Get complete overview for a company"""
    try:
        company = DimCompany.objects.get(symbol=symbol)
        pl = FactProfitLoss.objects.filter(symbol=symbol).order_by('-year_id').first()
        bs = FactBalanceSheet.objects.filter(symbol=symbol).order_by('-year_id').first()
        cf = FactCashFlow.objects.filter(symbol=symbol).order_by('-year_id').first()
        ml = FactMLScores.objects.filter(symbol=symbol).first()
        pc = FactProsCons.objects.filter(symbol=symbol).first()

        return Response({
            'company': CompanySerializer(company).data,
            'latest_financials': {
                'profit_loss': ProfitLossSerializer(pl).data if pl else None,
                'balance_sheet': BalanceSheetSerializer(bs).data if bs else None,
                'cash_flow': CashFlowSerializer(cf).data if cf else None,
            },
            'health_score': MLScoreSerializer(ml).data if ml else None,
            'pros_cons': ProsConsSerializer(pc).data if pc else None,
        })
    except DimCompany.DoesNotExist:
        return Response({'error': f'Company {symbol} not found'}, status=404)