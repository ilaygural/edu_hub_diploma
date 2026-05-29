from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='direction',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, 'Естественно научная'),
                    (2, 'Научно техническая'),
                    (3, 'Социально гуманитарная'),
                    (4, 'Физкультурно спортивная'),
                    (5, 'Художественная'),
                ],
                null=True,
                verbose_name='Направленность',
            ),
        ),
    ]
