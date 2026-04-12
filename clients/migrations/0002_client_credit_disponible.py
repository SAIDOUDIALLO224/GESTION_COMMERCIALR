from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='credit_disponible',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='Crédit disponible'),
        ),
    ]
