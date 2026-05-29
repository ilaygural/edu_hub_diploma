from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_contract_profile_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='parent',
            name='representative_relation',
            field=models.IntegerField(
                choices=[(1, 'Родитель'), (2, 'Законный представитель')],
                default=1,
                help_text='Как указано в договоре (родитель или законный представитель)',
                verbose_name='Статус',
            ),
        ),
        migrations.AddField(
            model_name='pupil',
            name='identity_document_type',
            field=models.IntegerField(
                choices=[(1, 'Свидетельство о рождении'), (2, 'Паспорт')],
                default=1,
                verbose_name='Документ ребёнка',
            ),
        ),
        migrations.AddField(
            model_name='pupil',
            name='passport_issued_by',
            field=models.CharField(blank=True, max_length=255, verbose_name='Кем выдан'),
        ),
        migrations.AddField(
            model_name='pupil',
            name='passport_issued_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата выдачи паспорта'),
        ),
        migrations.AddField(
            model_name='pupil',
            name='passport_number',
            field=models.CharField(blank=True, max_length=10, verbose_name='Номер паспорта'),
        ),
        migrations.AddField(
            model_name='pupil',
            name='passport_series',
            field=models.CharField(blank=True, max_length=10, verbose_name='Серия паспорта'),
        ),
        migrations.AddField(
            model_name='pupil',
            name='pfdo_certificate_number',
            field=models.CharField(
                blank=True,
                help_text='Если есть сертификат персонифицированного финансирования',
                max_length=50,
                verbose_name='Номер сертификата ПФДО',
            ),
        ),
        migrations.AddField(
            model_name='pupil',
            name='place_of_birth',
            field=models.CharField(blank=True, max_length=255, verbose_name='Место рождения'),
        ),
        migrations.AlterField(
            model_name='parent',
            name='address',
            field=models.CharField(blank=True, max_length=255, verbose_name='Домашний адрес'),
        ),
    ]
