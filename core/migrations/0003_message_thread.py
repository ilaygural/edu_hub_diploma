import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_contract_template_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0002_course_direction'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_threads', to='accounts.parent', verbose_name='Родитель')),
                ('pupil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_threads', to='accounts.pupil', verbose_name='Ученик')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_threads', to='accounts.teacher', verbose_name='Педагог')),
            ],
            options={
                'verbose_name': 'Переписка',
                'verbose_name_plural': 'Переписки',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(verbose_name='Текст')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')),
                ('read_by_parent', models.BooleanField(default=False, verbose_name='Прочитано родителем')),
                ('read_by_teacher', models.BooleanField(default=False, verbose_name='Прочитано педагогом')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authored_messages', to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.messagethread', verbose_name='Переписка')),
            ],
            options={
                'verbose_name': 'Сообщение',
                'verbose_name_plural': 'Сообщения',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='messagethread',
            constraint=models.UniqueConstraint(fields=('pupil', 'parent', 'teacher'), name='unique_message_thread'),
        ),
    ]
