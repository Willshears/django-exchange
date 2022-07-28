from django.urls import path
from . import views
urlpatterns = [
    path('btc-usdt', views.home, name='exchange-btc-usdt'),
    path('eth-usdt', views.ethusdt, name='exchange-eth-usdt'),
    path('xrp-usdt', views.xrpusdt, name='exchange-xrp-usdt'),
    path('trx-usdt', views.trxusdt, name='exchange-trx-usdt'),
    path('ltc-usdt', views.ltcusdt, name='exchange-ltc-usdt'),
    path('xlm-usdt', views.xlmusdt, name='exchange-xlm-usdt'),
    path('uni-usdt', views.uniusdt, name='exchange-uni-usdt'), #
    path('sol-usdt', views.solusdt, name='exchange-sol-usdt'), #
    path('doge-usdt', views.dogeusdt, name='exchange-doge-usdt'), #
    path('dot-usdt', views.dotusdt, name='exchange-dot-usdt'), #
    path('avax-usdt', views.avaxusdt, name='exchange-avax-usdt'),
    path('', views.markets, name='exchange-markets'),
    path('wallet', views.wallet, name='exchange-wallet'),
    path('recruiterform', views.recruit, name='exchange-recruiterform')
]