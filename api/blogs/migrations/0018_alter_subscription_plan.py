# Generated by Django 5.2rc1 on 2025-04-19 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0017_remove_client_gpt_prompt_client_business_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='plan',
            field=models.CharField(choices=[('monthly', 'Monthly'), ('annual', 'Annual')], default='basic', max_length=20),
        ),
    ]
