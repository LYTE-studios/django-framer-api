from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0012_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='completed_onboarding',
            field=models.BooleanField(default=False),
        ),
    ]