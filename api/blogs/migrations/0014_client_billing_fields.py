from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0013_client_completed_onboarding'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='company_name',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='client',
            name='vat_number',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='client',
            name='billing_address_line1',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='client',
            name='billing_address_line2',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='client',
            name='billing_city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='client',
            name='billing_state',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='client',
            name='billing_postal_code',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='client',
            name='billing_country',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]