import django_filters

from .models import *

class TradeFilter(django_filters.FilterSet):
    class Meta:
        model = Trade
        fields = ['token_name', 'token_symbol']


