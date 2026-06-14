import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_entrepot'),
        ('produits', '0008_produit_entrepot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='produit',
            name='entrepot',
        ),
        migrations.AddField(
            model_name='produit',
            name='entrepot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.entrepot', verbose_name='Entrepôt'),
        ),
    ]
