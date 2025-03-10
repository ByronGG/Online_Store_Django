# Generated by Django 5.1.5 on 2025-02-14 01:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='card_cvv',
            field=models.CharField(blank=True, max_length=4),
        ),
        migrations.AddField(
            model_name='profile',
            name='card_expiry',
            field=models.CharField(blank=True, max_length=5),
        ),
        migrations.AddField(
            model_name='profile',
            name='card_holder',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='card_number',
            field=models.CharField(blank=True, max_length=16),
        ),
    ]
