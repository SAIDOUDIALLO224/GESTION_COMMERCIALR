from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_ajout_est_principal_magasin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entrepot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom')),
                ('magasin', models.ForeignKey(on_delete=models.deletion.CASCADE, to='core.magasin', verbose_name='Magasin')),
            ],
            options={
                'verbose_name': 'Entrepôt',
                'verbose_name_plural': 'Entrepôts',
                'ordering': ['nom'],
                'unique_together': {('nom', 'magasin')},
            },
        ),
    ]
