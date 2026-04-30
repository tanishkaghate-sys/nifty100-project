from rest_framework import serializers
from .models import (DimCompany, FactProfitLoss, FactBalanceSheet,
                     FactCashFlow, FactMLScores, FactProsCons)

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DimCompany
        fields = '__all__'

class ProfitLossSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactProfitLoss
        fields = '__all__'

class BalanceSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactBalanceSheet
        fields = '__all__'

class CashFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactCashFlow
        fields = '__all__'

class MLScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactMLScores
        fields = '__all__'

class ProsConsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FactProsCons
        fields = '__all__'