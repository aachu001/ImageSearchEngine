# Generated by Django 3.1.2 on 2020-11-17 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0006_auto_20201114_2301'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='search_query',
            field=models.TextField(default=None),
        ),
    ]
