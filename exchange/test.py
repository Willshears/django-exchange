from django.shortcuts import render
from django.http import HttpResponse
from .models import Trade
from .models import Portfolio
from django.contrib import messages
from .filters import TradeFilter
from .forms import BuyForm
from .forms import SellForm
from django.http import HttpResponseRedirect
import requests
import json
from bs4 import BeautifulSoup as bs


# def update_portfolios(user, btc_amount, usd_amount):
#     btc_portfolio, _ = Portfolio.objects.get_or_create(account=user, token_symbol='BTC', token_name='Bitcoin')
#     usd_portfolio, _ = Portfolio.objects.get_or_create(account=user, token_symbol='USD', token_name='United States Dollar')
#     btc_portfolio.amount_holding + btc_amount
#     usd_portfolio.amount_holding + usd_amount
#     btc_portfolio.save()
#     usd_portfolio.save()

def home(request):
    def get_current_price():
        url = "https://www.coindesk.com/price/bitcoin"
        r = requests.get(url)
        soup = bs(r.content, "html.parser")
        scraper = soup.find("div",{"class":"Box-sc-1hpkeeg-0 jwYVXk"})
        result = scraper.text
        return result
    current_eth_price = get_current_price()
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
        'current_btc_price': current_eth_price,
    }
    if request.method == 'GET':
        if request.user.is_authenticated == False:
            messages.info(request, 'You need to register and log in to use these features')
    if request.method == 'POST':
        market_price_remove_comma = current_eth_price.replace(",", "")
        market_price_remove_dollar = market_price_remove_comma.replace("$", "")
        market_price = float(market_price_remove_dollar)
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
                        token_name=instance.token_name,
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
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.error(request, 'Buy error: You are not logged in')
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
                        token_name=instance.token_name,
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
                        return HttpResponseRedirect(request.path_info)


            else:
                messages.warning(request, 'Sell error: You are not logged in')
    return render(request, 'exchange/btc-usdt.html', context)
