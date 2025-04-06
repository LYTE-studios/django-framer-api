from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0014_client_billing_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='completed_onboarding',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]