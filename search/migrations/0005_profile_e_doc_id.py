# Generated by Django 3.1.2 on 2020-11-13 23:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0004_auto_20201028_1837'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='e_doc_id',
            field=models.CharField(default=None, max_length=100),
        ),
    ]
