import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paiement',
            name='montant_surplus',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Surplus'),
        ),
    ]
