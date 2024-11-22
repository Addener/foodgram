# Generated by Django 3.2.3 on 2024-11-20 15:56

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_follow_user_is_not_author'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodgramuser',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='Имя'),
        ),
        migrations.AlterField(
            model_name='foodgramuser',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='Никнейм'),
        ),
    ]