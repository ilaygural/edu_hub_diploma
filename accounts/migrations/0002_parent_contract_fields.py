from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Домашний адрес'),
        ),
        migrations.AddField(
            model_name='parent',
            name='passport',
            field=models.TextField(blank=True, verbose_name='Паспортные данные'),
        ),
    ]
