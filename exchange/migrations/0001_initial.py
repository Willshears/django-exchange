# Generated by Django 4.0.5 on 2022-07-08 18:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_name', models.CharField(max_length=100)),
                ('token_symbol', models.CharField(max_length=10)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.FloatField()),
                ('price', models.FloatField()),
                ('type', models.CharField(choices=[('Market Buy', 'Market Buy'), ('Market Sell', 'Market Sell')], max_length=15)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trader', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Portfolio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_name', models.CharField(default='United States Dollar', max_length=100)),
                ('token_symbol', models.CharField(default='USD', max_length=10)),
                ('amount_holding', models.FloatField(default='100000')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
