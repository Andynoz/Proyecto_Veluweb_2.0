# Generated by Django 5.2.2 on 2025-06-06 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0003_passwordresettoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('imagen', models.ImageField(blank=True, null=True, upload_to='productos/')),
                ('creado', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
