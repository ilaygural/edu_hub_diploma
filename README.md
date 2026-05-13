# EduHub

Веб‑приложение на **Django** для учебного заведения дополнительного образования: роли (администратор, педагог, родитель, ученик), заявки, зачисления, расписание, журнал посещаемости.

**ВКР (защита):** июнь 2026.

## Документация в репозитории

| Файл | Назначение |
|------|------------|
| [WORKLOG.md](WORKLOG.md) | Текущий этап, ветка, что сделать дальше (начинать отсюда для работы в чате) |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Структура кода, модели, URL — справочник по проекту |
| [REFACTORING.md](REFACTORING.md) | Отложенный техдолг (после ВКР / стабилизации), на функциональность не опираться |

Материалы практик и черновик ВКР: каталог **`reports/`** (подпапки `tech/`, `prediploma/`, `vkr/`, общие `assets/`, `guidelines/`).

## Установка и запуск

```bash
git clone <url-репозитория>
cd django_edu_hub
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

На Linux/macOS активация: `source .venv/bin/activate`.

После `git pull` при появлении ошибок по колонкам БД выполнить `python manage.py migrate`.
