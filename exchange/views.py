from django.shortcuts import render
from django.http import HttpResponse
from .models import Trade
from .models import Portfolio
from django.contrib import messages
from .filters import TradeFilter
from .forms import BuyForm
from .forms import SellForm
from .forms import RecruiterForm
from django.http import HttpResponseRedirect
import requests
import json
from django.contrib.auth.decorators import login_required
from bs4 import BeautifulSoup as bs
import ccxt
selector = 0


##############################
##### Binance connection logic (Replaces the old method demonstrated in the ETH view. That can be used but it has slower performance.
binance = ccxt.binance()
trading_pair = ''
def price_ticker(trading_pair):
    price_ticker = binance.fetch_ticker(trading_pair)
    # calculate the ticker price of crypto in terms of USD by taking the midpoint of the best bid and ask
    TokenPriceFull = (float(price_ticker['ask']) + float(price_ticker['bid'])) / 2
    TokenPriceUSDT = round(TokenPriceFull, 2)
    return TokenPriceUSDT
# # # # # # # # # # # # # # # #




# This was the old way to calculate portfolio updates
# def update_portfolios(user, btc_amount, usd_amount):
#     btc_portfolio, _ = Portfolio.objects.get_or_create(account=user, token_symbol='BTC', token_name='Bitcoin')
#     usd_portfolio, _ = Portfolio.objects.get_or_create(account=user, token_symbol='USD', token_name='United States Dollar')
#     btc_portfolio.amount_holding + btc_amount
#     usd_portfolio.amount_holding + usd_amount
#     btc_portfolio.save()
#     usd_portfolio.save()

# def new_user_usd(request):
#     if not Portfolio.objects.filter(token_symbol='USD').exists():
#         render_view, __ = Portfolio.objects.get_or_create(
#             account=request.user,
#             token_name='United States Dollar',
#             token_symbol='USD',
#             amount_holding=10.0
#         )
#         render_view.save()
#         messages.success(request, 'As a new user, you have been credited with 10 USD')


# def btclive(request):
#     current_btc_price = price_ticker(trading_pair='BTC/USDT')
#     context = {
#         'current_btc_price': current_btc_price,
#     }
#     return render(request, 'btclive.html', context)
# def avaxlive(request):
#     pass
# def dogelive(request):
#     pass
# def dotlive(request):
#     pass
# def ethlive(request):
#     pass
# def ltclive(request):
#     pass
# def sollive(request):
#     pass
# def trxlive(request):
#     pass
# def unilive(request):
#     pass
# def xlmlive(request):
#     pass
# def xrplive(request):
#     pass

def home(request):
    current_btc_price = price_ticker(trading_pair='BTC/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    btc_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'btc_bals': btc_bals,
        'current_btc_price': current_btc_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='BTC/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Bitcoin'
                    instance.token_symbol = 'BTC'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_btc, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='BTC'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_btc.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_btc.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_btc.amount_holding += instance.amount
                        add_btc.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request, f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Bitcoin'
                    instance.token_symbol = 'BTC'
                    remove_btc, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='BTC'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_btc.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_btc.amount_holding = remove_btc.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_btc.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/btc-price.html', context)
    else:
        return render(request, 'exchange/btc-usdt.html', context)

def ethusdt(request):
    # This is the old method using BeautifulSoup.
    # def get_eth_price():
    #     url = "https://www.coindesk.com/price/ethereum"
    #     r = requests.get(url)
    #     soup = bs(r.content, "html.parser")
    #     scraper = soup.find("div",{"class":"Box-sc-1hpkeeg-0 jwYVXk"})
    #     result = scraper.text
    #     return result
    current_eth_price = price_ticker(trading_pair='ETH/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    eth_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'eth_bals': eth_bals,
        'current_eth_price': current_eth_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='ETH/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Ethereum'
                    instance.token_symbol = 'ETH'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_eth, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='ETH'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_eth.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_eth.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_eth.amount_holding += instance.amount
                        add_eth.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Ethereum'
                    instance.token_symbol = 'ETH'
                    remove_eth, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='ETH'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_eth.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_eth.amount_holding = remove_eth.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_eth.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/eth-price.html', context)
    else:
        return render(request, 'exchange/eth-usdt.html', context)


def xrpusdt(request):
    current_xrp_price = price_ticker(trading_pair='XRP/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    xrp_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'xrp_bals': xrp_bals,
        'current_xrp_price': current_xrp_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='XRP/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Ripple'
                    instance.token_symbol = 'XRP'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_xrp, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='XRP'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_xrp.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_xrp.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_xrp.amount_holding += instance.amount
                        add_xrp.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request, f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Ripple'
                    instance.token_symbol = 'XRP'
                    remove_xrp, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='XRP'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_xrp.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_xrp.amount_holding = remove_xrp.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_xrp.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/xrp-price.html', context)
    else:
        return render(request, 'exchange/xrp-usdt.html', context)


def trxusdt(request):
    current_trx_price = price_ticker(trading_pair='TRX/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    trx_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'trx_bals': trx_bals,
        'current_trx_price': current_trx_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='TRX/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'TRON'
                    instance.token_symbol = 'TRX'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_trx, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='TRX'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_trx.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_trx.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_trx.amount_holding += instance.amount
                        add_trx.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'TRON'
                    instance.token_symbol = 'TRX'
                    remove_trx, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='TRX'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_trx.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_trx.amount_holding = remove_trx.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_trx.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/trx-price.html', context)
    else:
        return render(request, 'exchange/trx-usdt.html', context)


def ltcusdt(request):
    current_ltc_price = price_ticker(trading_pair='LTC/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    ltc_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'ltc_bals': ltc_bals,
        'current_ltc_price': current_ltc_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='LTC/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Litecoin'
                    instance.token_symbol = 'LTC'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_ltc, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='LTC'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_ltc.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_ltc.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_ltc.amount_holding += instance.amount
                        add_ltc.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Litecoin'
                    instance.token_symbol = 'LTC'
                    remove_ltc, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='LTC'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_ltc.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_ltc.amount_holding = remove_ltc.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_ltc.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/ltc-price.html', context)
    else:
        return render(request, 'exchange/ltc-usdt.html', context)


def xlmusdt(request):
    current_xlm_price = price_ticker(trading_pair='XLM/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    xlm_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'xlm_bals': xlm_bals,
        'current_xlm_price': current_xlm_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='XLM/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Stellar Lumen'
                    instance.token_symbol = 'XLM'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_xlm, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='XLM'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_xlm.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_xlm.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_xlm.amount_holding += instance.amount
                        add_xlm.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Stellar Lumen'
                    instance.token_symbol = 'XLM'
                    remove_xlm, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='XLM'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_xlm.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_xlm.amount_holding = remove_xlm.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_xlm.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/xlm-price.html', context)
    else:
        return render(request, 'exchange/xlm-usdt.html', context)


def uniusdt(request):
    current_uni_price = price_ticker(trading_pair='UNI/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    uni_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'uni_bals': uni_bals,
        'current_uni_price': current_uni_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='UNI/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'UNISWAP'
                    instance.token_symbol = 'UNI'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_uni, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='UNI'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_uni.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_uni.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_uni.amount_holding += instance.amount
                        add_uni.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'UNISWAP'
                    instance.token_symbol = 'UNI'
                    remove_uni, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='UNI'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_uni.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_uni.amount_holding = remove_uni.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_uni.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/uni-price.html', context)
    else:
        return render(request, 'exchange/uni-usdt.html', context)


def solusdt(request):
    current_sol_price = price_ticker(trading_pair='SOL/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    sol_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'sol_bals': sol_bals,
        'current_sol_price': current_sol_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='SOL/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Solana'
                    instance.token_symbol = 'SOL'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_sol, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='SOL'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_sol.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_sol.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_sol.amount_holding += instance.amount
                        add_sol.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Solana'
                    instance.token_symbol = 'SOL'
                    remove_sol, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='SOL'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_sol.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_sol.amount_holding = remove_sol.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_sol.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/sol-price.html', context)
    else:
        return render(request, 'exchange/sol-usdt.html', context)


def dogeusdt(request):
    current_doge_price = price_ticker(trading_pair='DOGE/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    doge_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'doge_bals': doge_bals,
        'current_doge_price': current_doge_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='DOGE/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Dogecoin'
                    instance.token_symbol = 'DOGE'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_doge, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='DOGE'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_doge.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_doge.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_doge.amount_holding += instance.amount
                        add_doge.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Dogecoin'
                    instance.token_symbol = 'DOGE'
                    remove_doge, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='DOGE'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_doge.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_doge.amount_holding = remove_doge.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_doge.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/doge-price.html', context)
    else:
        return render(request, 'exchange/doge-usdt.html', context)


def dotusdt(request):
    current_dot_price = price_ticker(trading_pair='DOT/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    dot_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'dot_bals': dot_bals,
        'current_dot_price': current_dot_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='DOT/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Polkadot'
                    instance.token_symbol = 'DOT'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_dot, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='DOT'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_dot.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_dot.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_dot.amount_holding += instance.amount
                        add_dot.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Polkadot'
                    instance.token_symbol = 'DOT'
                    remove_dot, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='DOT'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_dot.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_dot.amount_holding = remove_dot.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_dot.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/dot-price.html', context)
    else:
        return render(request, 'exchange/dot-usdt.html', context)


def avaxusdt(request):
    current_avax_price = price_ticker(trading_pair='AVAX/USDT')
    trades = Trade.objects.filter(account=request.user.id)
    myFilter = TradeFilter(request.GET, queryset=trades)
    avax_bals = Portfolio.objects.filter(account=request.user.id)
    trades = myFilter.qs
    buyform = BuyForm()
    sellform = SellForm()
    context = {
        'trades': trades,
        'myFilter':myFilter,
        'buyform': buyform,
        'sellform': sellform,
        'avax_bals': avax_bals,
        'current_avax_price': current_avax_price,
    }
    if request.method == 'POST':
        market_price = price_ticker(trading_pair='AVAX/USDT')
        if request.POST.get("form_type") == 'BuyForm':
            if request.user.is_authenticated:
                buyform = BuyForm(request.POST)
                if buyform.is_valid():
                    instance = buyform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Avalanche'
                    instance.token_symbol = 'AVAX'
                    remove_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    add_avax, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='AVAX'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_remove_funds = market_price * instance.amount
                    instance.price = -abs(calculate_remove_funds)
                    instance.type = 'Market Buy'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    # current_token_balance = add_avax.amount_holding
                    current_usd_balance = remove_funds.amount_holding
                    if calculate_remove_funds > current_usd_balance:
                        messages.warning(request, 'You do not have enough funds for this transaction')
                        # remove_funds.amount_holding = current_usd_balance
                        # add_avax.amount_holding = current_token_balance
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_funds.amount_holding += instance.price
                        add_avax.amount_holding += instance.amount
                        add_avax.save()
                        remove_funds.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_remove_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
        elif request.POST.get("form_type") == 'SellForm':
            if request.user.is_authenticated:
                sellform = SellForm(request.POST)
                if sellform.is_valid():
                    instance = sellform.save(commit=False)
                    instance.account = request.user
                    instance.token_name = 'Avalanche'
                    instance.token_symbol = 'AVAX'
                    remove_avax, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name=instance.token_name,
                        token_symbol='AVAX'
                    )
                    add_funds, __ = Portfolio.objects.get_or_create(
                        account=instance.account,
                        token_name='United States Dollar',
                        token_symbol='USD'
                    )
                    ################################################
                    # Calculating the price
                    ################################################
                    calculate_add_funds = market_price * instance.amount
                    instance.price = calculate_add_funds
                    instance.type = 'Market Sell'


                    #################################################
                    # This piece of code validates whether the user has enough funds. Otherwise, it immediatly resets the balance back to before
                    #################################################
                    current_token_balance = remove_avax.amount_holding
                    if instance.amount > current_token_balance:
                        messages.warning(request, 'You do not have enough tokens for this transaction')
                    else:
                        #################################################
                        # Here we save the order and calculate how many funds have been removed or added
                        #################################################
                        remove_avax.amount_holding = remove_avax.amount_holding - instance.amount
                        add_funds.amount_holding = add_funds.amount_holding + instance.price
                        add_funds.save()
                        remove_avax.save()
                        instance.save()
                        messages.success(request,
                                         f'Your transaction for ${calculate_add_funds} was successful!')
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    if request.htmx:
        return render(request, 'exchange/partials/avax-price.html', context)
    else:
        return render(request, 'exchange/avax-usdt.html', context)

def markets(request):
    current_btc_price = price_ticker(trading_pair='BTC/USDT')
    current_avax_price = price_ticker(trading_pair='AVAX/USDT')
    current_doge_price = price_ticker(trading_pair='DOGE/USDT')
    current_dot_price = price_ticker(trading_pair='DOT/USDT')
    current_eth_price = price_ticker(trading_pair='ETH/USDT')
    current_ltc_price = price_ticker(trading_pair='LTC/USDT')
    current_sol_price = price_ticker(trading_pair='SOL/USDT')
    current_trx_price = price_ticker(trading_pair='TRX/USDT')
    current_uni_price = price_ticker(trading_pair='UNI/USDT')
    current_xlm_price = price_ticker(trading_pair='XLM/USDT')
    current_xrp_price = price_ticker(trading_pair='XRP/USDT')
    context = {
        'current_btc_price': current_btc_price,
        'current_avax_price': current_avax_price,
        'current_doge_price': current_doge_price,
        'current_dot_price': current_dot_price,
        'current_eth_price': current_eth_price,
        'current_ltc_price': current_ltc_price,
        'current_sol_price': current_sol_price,
        'current_trx_price': current_trx_price,
        'current_uni_price': current_uni_price,
        'current_xlm_price': current_xlm_price,
        'current_xrp_price': current_xrp_price,
    }
    return render(request, 'exchange/markets.html', context)

@login_required
def wallet(request):
    total_value = 0
    current_usd_price = 1
    current_avax_price = price_ticker(trading_pair='AVAX/USDT')
    current_btc_price = price_ticker(trading_pair='BTC/USDT')
    current_doge_price = price_ticker(trading_pair='DOGE/USDT')
    current_dot_price = price_ticker(trading_pair='DOT/USDT')
    current_eth_price = price_ticker(trading_pair='ETH/USDT')
    current_ltc_price = price_ticker(trading_pair='LTC/USDT')
    current_sol_price = price_ticker(trading_pair='SOL/USDT')
    current_trx_price = price_ticker(trading_pair='TRX/USDT')
    current_uni_price = price_ticker(trading_pair='UNI/USDT')
    current_xlm_price = price_ticker(trading_pair='XLM/USDT')
    current_xrp_price = price_ticker(trading_pair='XRP/USDT')
    price = ()
    price=[current_eth_price, current_usd_price, current_avax_price, current_doge_price, current_dot_price, current_ltc_price, current_sol_price, current_trx_price, current_uni_price, current_xlm_price, current_xrp_price, current_btc_price]
    portfolios = Portfolio.objects.filter(account=request.user.id)
    amount = Portfolio.objects.filter(account=request.user.id)
    for amount, price in zip(amount, price):
        current_token_value = price * amount.amount_holding
        total_value = round(total_value + current_token_value,2)


    context = {
        'portfolios': portfolios,
        'total_value': total_value
    }
    return render(request, 'exchange/wallet.html', context)

def recruit(request):
    recruiterform = RecruiterForm()
    context = {
        'recruiterform': recruiterform,
    }
    if request.method == 'POST':
        if request.POST.get("form_type") == 'RecruiterForm':
            recruiterform = RecruiterForm(request.POST)
            if recruiterform.is_valid():
                recruiterform.save()
    return render(request, 'exchange/recruiterform.html', context)