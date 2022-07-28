from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
logger = logging.getLogger(__name__)

class Trade(models.Model):
    token_name = models.CharField(max_length=100)
    token_symbol = models.CharField(max_length=10)
    date = models.DateTimeField(default=timezone.now)
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trader')
    amount = models.FloatField()
    price = models.FloatField()
    type = models.CharField(max_length=15,
                              choices=(
                                  ("Market Buy", "Market Buy"),
                                  ("Market Sell", "Market Sell")))

    def id(self):
        return id(self.id)

class Portfolio(models.Model,):
    unique_together = [['token_symbol', 'account']]
    token_name = models.CharField(max_length=100, default='United States Dollar')
    token_symbol = models.CharField(max_length=10, default='USD')
    account = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio')
    amount_holding = models.FloatField(default=10)

    def id(self):
        return id(self.id)

class Recruiter(models.Model):
    company = models.CharField(max_length=100)
    description = models.TextField()
    job_title = models.CharField(max_length=100)
    date_posted = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    salary = models.IntegerField()
    def __str__(self):
        return self.company


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    coin_symbol_list = ('USD', 'AVAX', 'BTC', 'DOGE', 'DOT', 'ETH', 'LTC', 'SOL', 'TRX', 'UNI', 'XLM', 'XRP')
    coin_name_list = (
        'United States Dollar', 'Avalanche', 'Bitcoin', 'Dogecoin', 'Polkadot', 'Ethereum', 'Litecoin', 'Solana',
        'TRON', 'Uniswap',
        'Stellar Lumen', 'Ripple')
    if created:
        for symbol, name in zip(coin_symbol_list, coin_name_list):
            username = instance.username
            user_id_filter = User.objects.filter(username=username).first()
            user_id = int(user_id_filter.id)
            load_balance = Portfolio.objects.get_or_create(
                account_id=user_id,
                token_name=name,
                token_symbol=symbol,
                amount_holding=10.0
            )
            logger.error(symbol)
