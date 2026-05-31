from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_contract_template_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='patronymic',
            field=models.CharField(blank=True, max_length=100, verbose_name='Отчество'),
        ),
    ]
