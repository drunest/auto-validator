# Generated by Django 4.2.15 on 2024-09-24 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_validatorinstance_server_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uploadedfile',
            name='user',
        ),
    ]
