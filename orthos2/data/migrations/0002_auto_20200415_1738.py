# Generated by Django 2.2.11 on 2020-04-15 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='domain',
            name='dhcp_server',
        ),
        migrations.AddField(
            model_name='domain',
            name='cobbler_server',
            field=models.ManyToManyField(blank=True, limit_choices_to={'administrative': True}, related_name='cobbler_server_for', to='data.Machine', verbose_name='Cobbler server'),
        ),
    ]
