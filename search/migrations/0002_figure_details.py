# Generated by Django 3.1.2 on 2020-10-28 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Figure_Details',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patentID', models.CharField(max_length=50)),
                ('pid', models.CharField(max_length=50)),
                ('is_multiple', models.PositiveIntegerField()),
                ('origreftext', models.CharField(max_length=50)),
                ('figid', models.PositiveIntegerField()),
                ('subfig', models.CharField(max_length=50)),
                ('is_caption', models.PositiveIntegerField()),
                ('description', models.TextField()),
                ('aspect', models.CharField(max_length=50)),
                ('object', models.CharField(max_length=50)),
            ],
        ),
    ]