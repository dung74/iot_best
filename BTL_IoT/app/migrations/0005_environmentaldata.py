# Generated by Django 3.2.25 on 2024-08-19 04:01

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_shippingaddress_customer_alter_order_customer_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvironmentalData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('temperature', models.FloatField()),
                ('humidity', models.FloatField()),
                ('dust_level', models.FloatField()),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]