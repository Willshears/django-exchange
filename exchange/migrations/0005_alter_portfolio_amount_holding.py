# Generated by Django 4.0.5 on 2022-07-08 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0004_alter_portfolio_amount_holding_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='amount_holding',
            field=models.FloatField(default=0, null=True),
        ),
    ]
