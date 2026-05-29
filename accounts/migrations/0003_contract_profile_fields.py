from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_parent_contract_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='patronymic',
            field=models.CharField(blank=True, max_length=100, verbose_name='Отчество'),
        ),
        migrations.AddField(
            model_name='parent',
            name='passport_issued_by',
            field=models.CharField(blank=True, max_length=255, verbose_name='Кем выдан паспорт'),
        ),
        migrations.AddField(
            model_name='parent',
            name='passport_issued_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата выдачи паспорта'),
        ),
        migrations.AddField(
            model_name='parent',
            name='passport_number',
            field=models.CharField(blank=True, max_length=10, verbose_name='Номер паспорта'),
        ),
        migrations.AddField(
            model_name='parent',
            name='passport_series',
            field=models.CharField(blank=True, max_length=10, verbose_name='Серия паспорта'),
        ),
        migrations.AddField(
            model_name='parent',
            name='snils',
            field=models.CharField(blank=True, max_length=14, verbose_name='СНИЛС'),
        ),
        migrations.AddField(
            model_name='pupil',
            name='birth_certificate',
            field=models.TextField(
                blank=True,
                help_text='Серия, номер, кем и когда выдано',
                verbose_name='Свидетельство о рождении',
            ),
        ),
        migrations.AddField(
            model_name='pupil',
            name='patronymic',
            field=models.CharField(blank=True, max_length=100, verbose_name='Отчество'),
        ),
        migrations.AddField(
            model_name='pupil',
            name='snils',
            field=models.CharField(blank=True, max_length=14, verbose_name='СНИЛС'),
        ),
        migrations.AlterField(
            model_name='parent',
            name='address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Адрес регистрации'),
        ),
        migrations.AlterField(
            model_name='parent',
            name='passport',
            field=models.TextField(
                blank=True,
                help_text='Необязательно, если заполнены поля выше',
                verbose_name='Прочие паспортные данные',
            ),
        ),
    ]
