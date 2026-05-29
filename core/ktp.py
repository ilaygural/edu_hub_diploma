"""Генерация дат занятий и документа КТП (календарно-тематическое планирование)."""
import json
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from openpyxl.styles import Alignment

WEEKDAY_TO_NUM = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}

WEEKDAY_LABELS = {
    'monday': 'Понедельник',
    'tuesday': 'Вторник',
    'wednesday': 'Среда',
    'thursday': 'Четверг',
    'friday': 'Пятница',
    'saturday': 'Суббота',
}

KTP_DATA_DIR = Path(__file__).resolve().parent.parent / 'reports' / 'vkr' / 'data'
KTP_TEMPLATE_PATH = KTP_DATA_DIR / 'КТП Информатика группа 1 за 2025-2026 год.xlsx'

KTP_LEFT_START_ROW = 7
KTP_RIGHT_START_ROW = 7
KTP_DEFAULT_TOTALS_ROW = 25
KTP_DEFAULT_LAST_LESSON_ROW = 24

KTP_DATE_FORMAT = 'dd.mm.yyyy'

DEFAULT_WEEKDAY_SLOT_1 = 'Понедельник (10:30 - 12:00)'
DEFAULT_WEEKDAY_SLOT_2 = 'Четверг (10:00 - 11:30)'

# Запасной набор праздников, если JSON-календарь недоступен
RU_HOLIDAYS: set[date] = {
    date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 4),
    date(2025, 1, 5), date(2025, 1, 6), date(2025, 1, 7), date(2025, 1, 8),
    date(2025, 2, 23), date(2025, 3, 8),
    date(2025, 5, 1), date(2025, 5, 2), date(2025, 5, 8), date(2025, 5, 9),
    date(2025, 6, 12), date(2025, 6, 13),
    date(2025, 11, 2), date(2025, 11, 3), date(2025, 11, 4),
    date(2025, 12, 31),
    date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4),
    date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8),
    date(2026, 2, 23), date(2026, 3, 8), date(2026, 3, 9),
    date(2026, 5, 1), date(2026, 5, 9), date(2026, 5, 11),
    date(2026, 6, 12),
    date(2026, 11, 4),
    date(2026, 12, 31),
}


def load_nonworking_days_from_json(path: Path) -> set[date]:
    """Парсит calendar_YYYY.json с xmlcalendar.ru."""
    data = json.loads(path.read_text(encoding='utf-8'))
    year = data['year']
    result: set[date] = set()
    for month_data in data['months']:
        month = month_data['month']
        for part in month_data['days'].split(','):
            day_text = part.strip().rstrip('*+')
            if not day_text:
                continue
            result.add(date(year, month, int(day_text)))
    return result


def get_holidays_for_period(date_from: date, date_to: date) -> set[date]:
    """Нерабочие дни за период из локальных JSON; иначе — RU_HOLIDAYS."""
    holidays: set[date] = set()
    for year in range(date_from.year, date_to.year + 1):
        path = KTP_DATA_DIR / f'calendar_{year}.json'
        if path.exists():
            holidays |= load_nonworking_days_from_json(path)

    if holidays:
        return {day for day in holidays if date_from <= day <= date_to}
    return {day for day in RU_HOLIDAYS if date_from <= day <= date_to}


def generate_lesson_dates_for_weekday(
    date_from: date,
    date_to: date,
    weekday: str,
    *,
    skip_holidays: bool = True,
    holidays: set[date] | None = None,
) -> list[date]:
    weekday_num = WEEKDAY_TO_NUM.get(weekday)
    if weekday_num is None:
        return []

    if skip_holidays and holidays is None:
        holidays = get_holidays_for_period(date_from, date_to)
    elif not skip_holidays:
        holidays = set()

    result: list[date] = []
    current = date_from
    while current <= date_to:
        if current.weekday() == weekday_num and current not in holidays:
            result.append(current)
        current += timedelta(days=1)
    return result


def generate_lesson_dates(
    date_from: date,
    date_to: date,
    weekdays: list[str],
    *,
    skip_holidays: bool = True,
    holidays: set[date] | None = None,
) -> list[date]:
    """Все даты занятий в хронологическом порядке."""
    if date_from > date_to:
        raise ValueError('Дата начала не может быть позже даты окончания')

    known_weekdays = [w for w in weekdays if w in WEEKDAY_TO_NUM]
    if not known_weekdays:
        return []

    if skip_holidays and holidays is None:
        holidays = get_holidays_for_period(date_from, date_to)
    elif not skip_holidays:
        holidays = set()

    weekday_nums = {WEEKDAY_TO_NUM[w] for w in known_weekdays}
    result: list[date] = []
    current = date_from
    while current <= date_to:
        if current.weekday() in weekday_nums and current not in holidays:
            result.append(current)
        current += timedelta(days=1)
    return result


def split_lessons_for_template(
    date_from: date,
    date_to: date,
    weekdays: list[str],
    *,
    skip_holidays: bool = True,
) -> tuple[list[date], list[date], list[str]]:
    """
    Считает все занятия за период в хронологическом порядке и делит пополам:
    первая половина — левый столбец, вторая — правый.
    """
    sorted_weekdays = sorted(
        [w for w in weekdays if w in WEEKDAY_TO_NUM],
        key=lambda w: WEEKDAY_TO_NUM[w],
    )
    if len(sorted_weekdays) != 2:
        raise ValueError('Для шаблона КТП нужно выбрать ровно два дня недели.')

    all_dates = generate_lesson_dates(
        date_from,
        date_to,
        sorted_weekdays,
        skip_holidays=skip_holidays,
    )
    left_count = (len(all_dates) + 1) // 2
    return all_dates[:left_count], all_dates[left_count:], sorted_weekdays


def default_weekday_slot(weekday: str, *, default_time: str) -> str:
    label = WEEKDAY_LABELS.get(weekday, weekday)
    return f'{label} ({default_time})'


def _ktp_sheet_name(half_year: int) -> str:
    if half_year not in (1, 2):
        raise ValueError('Полугодие должно быть 1 или 2')
    return f'полугодие {half_year}'


def _get_worksheet(wb, half_year: int):
    for candidate in (f'полугодие {half_year}', f'{half_year} полугодие'):
        if candidate in wb.sheetnames:
            return wb[candidate]
    raise ValueError(
        f'Лист для {half_year}-го полугодия не найден. '
        f'Ожидается «полугодие {half_year}».'
    )


def _build_ktp_header(
    *,
    group_name: str,
    half_year: int,
    weekday_slot_1: str,
    weekday_slot_2: str,
) -> str:
    group = group_name.strip() or '1'
    slot_1 = weekday_slot_1.strip() or DEFAULT_WEEKDAY_SLOT_1
    slot_2 = weekday_slot_2.strip() or DEFAULT_WEEKDAY_SLOT_2
    return (
        f'{half_year} полугодие Группа {group}. '
        f'{slot_1} - {slot_2}'
    )


def _set_lesson_date(ws, row: int, column: int, lesson_date: date) -> None:
    cell = ws.cell(row=row, column=column, value=lesson_date)
    cell.number_format = KTP_DATE_FORMAT


def _set_lesson_hours(ws, row: int, theory_col: int, practice_col: int, independent_col: int) -> None:
    ws.cell(row=row, column=theory_col, value=2)
    ws.cell(row=row, column=practice_col, value=1)
    ws.cell(row=row, column=independent_col, value=1)


def _find_footer_row(ws) -> int:
    return _find_totals_row(ws) + 1


def _unmerge_row(ws, row: int) -> None:
    for merged_range in list(ws.merged_cells.ranges):
        if merged_range.min_row <= row <= merged_range.max_row:
            try:
                ws.unmerge_cells(str(merged_range))
            except KeyError:
                pass


def _apply_totals_formulas(ws, first_row: int, last_lesson_row: int) -> int:
    """Строка «Итого» с SUM по фактическому диапазону занятий (после insert_rows диапазон меняется)."""
    totals_row = last_lesson_row + 1
    for row in range(last_lesson_row, last_lesson_row + 3):
        value = ws.cell(row=row, column=3).value
        if isinstance(value, str) and 'итого' in value.lower():
            totals_row = row
            break

    _unmerge_row(ws, totals_row)
    ws.cell(row=totals_row, column=3, value='Итого')
    ws.cell(
        row=totals_row,
        column=4,
        value=f'=SUM(D{first_row}:D{last_lesson_row},J{first_row}:J{last_lesson_row})',
    )
    ws.cell(
        row=totals_row,
        column=5,
        value=f'=SUM(E{first_row}:E{last_lesson_row},K{first_row}:K{last_lesson_row})',
    )
    ws.cell(
        row=totals_row,
        column=6,
        value=f'=SUM(F{first_row}:F{last_lesson_row},L{first_row}:L{last_lesson_row})',
    )
    return totals_row


def _write_footer_row(ws, row: int, text: str) -> None:
    for merged_range in list(ws.merged_cells.ranges):
        if merged_range.min_row == row and merged_range.max_row == row:
            try:
                ws.unmerge_cells(str(merged_range))
            except KeyError:
                pass
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=13)
    cell = ws.cell(row=row, column=2, value=text)
    cell.alignment = Alignment(wrap_text=True, vertical='center', horizontal='left')


def _update_ktp_footer(ws, *, half_year: int, lesson_count: int) -> None:
    theory_hours = lesson_count * 2
    other_hours = lesson_count * 2
    footer_row = _find_footer_row(ws)
    _write_footer_row(
        ws,
        footer_row,
        (
            f'Всего {theory_hours + other_hours} часов за {half_year} полугодие, '
            f'{theory_hours} часов теории, {other_hours} часов практики'
        ),
    )


def _find_totals_row(ws) -> int:
    for row in range(20, 40):
        for col in (2, 3):
            value = ws.cell(row=row, column=col).value
            if isinstance(value, str) and 'итого' in value.lower():
                return row
    return KTP_DEFAULT_TOTALS_ROW


def _lesson_row_bounds(ws) -> tuple[int, int]:
    """Строки занятий: от 7-й до строки перед «Итого»."""
    totals_row = _find_totals_row(ws)
    last_row = max(KTP_LEFT_START_ROW, totals_row - 1)
    return KTP_LEFT_START_ROW, last_row


def _unmerge_rows_in_range(ws, first_row: int, last_row: int) -> None:
    to_remove = [
        str(merged_range)
        for merged_range in list(ws.merged_cells.ranges)
        if merged_range.min_row >= first_row and merged_range.max_row <= last_row
    ]
    for ref in to_remove:
        try:
            ws.unmerge_cells(ref)
        except KeyError:
            pass


def _ensure_lesson_capacity(ws, rows_needed: int) -> tuple[int, int]:
    first_row, last_row = _lesson_row_bounds(ws)
    capacity = last_row - first_row + 1
    if rows_needed > capacity:
        totals_row = _find_totals_row(ws)
        ws.insert_rows(totals_row, rows_needed - capacity)
        first_row, last_row = _lesson_row_bounds(ws)
    return first_row, last_row


def _clear_left_lesson_row(ws, row: int) -> None:
    for col in (2, 3, 4, 5, 6, 7):
        ws.cell(row=row, column=col, value='')


def _clear_right_lesson_row(ws, row: int) -> None:
    for col in (8, 9, 10, 11, 12, 13):
        ws.cell(row=row, column=col, value='')


def _clear_ktp_sheet_rows(ws) -> None:
    first_row, last_row = _lesson_row_bounds(ws)
    _unmerge_rows_in_range(ws, first_row, last_row)
    for row in range(first_row, last_row + 1):
        _clear_left_lesson_row(ws, row)
        _clear_right_lesson_row(ws, row)


def clear_ktp_sheet(
    ws,
    *,
    half_year: int,
    group_name: str = '',
    weekday_slot_1: str = DEFAULT_WEEKDAY_SLOT_1,
    weekday_slot_2: str = DEFAULT_WEEKDAY_SLOT_2,
) -> None:
    """Пустой лист по структуре шаблона (шапка без данных занятий)."""
    ws['B3'] = _build_ktp_header(
        group_name=group_name,
        half_year=half_year,
        weekday_slot_1=weekday_slot_1,
        weekday_slot_2=weekday_slot_2,
    )
    _clear_ktp_sheet_rows(ws)
    first_row, last_row = _lesson_row_bounds(ws)
    _apply_totals_formulas(ws, first_row, last_row)
    _write_footer_row(ws, _find_footer_row(ws), '')


def fill_ktp_sheet(
    ws,
    left_dates: list[date],
    right_dates: list[date],
    *,
    half_year: int,
    group_name: str = '',
    weekday_slot_1: str = DEFAULT_WEEKDAY_SLOT_1,
    weekday_slot_2: str = DEFAULT_WEEKDAY_SLOT_2,
) -> None:
    lesson_count = len(left_dates) + len(right_dates)
    if lesson_count == 0:
        raise ValueError('Список дат занятий пуст')

    ws['B3'] = _build_ktp_header(
        group_name=group_name,
        half_year=half_year,
        weekday_slot_1=weekday_slot_1,
        weekday_slot_2=weekday_slot_2,
    )
    _clear_ktp_sheet_rows(ws)
    first_row, last_row = _ensure_lesson_capacity(ws, max(len(left_dates), len(right_dates)))
    _unmerge_rows_in_range(ws, first_row, last_row)

    for index, lesson_date in enumerate(left_dates):
        row = first_row + index
        ws.cell(row=row, column=2, value=index + 1)
        ws.cell(row=row, column=3, value='')
        _set_lesson_hours(ws, row, 4, 5, 6)
        _set_lesson_date(ws, row, 7, lesson_date)

    left_count = len(left_dates)
    for index, lesson_date in enumerate(right_dates):
        row = first_row + index
        lesson_number = left_count + index + 1
        ws.cell(row=row, column=8, value=lesson_number)
        ws.cell(row=row, column=9, value='')
        _set_lesson_hours(ws, row, 10, 11, 12)
        _set_lesson_date(ws, row, 13, lesson_date)

    last_lesson_row = first_row + max(len(left_dates), len(right_dates)) - 1
    _apply_totals_formulas(ws, first_row, last_lesson_row)
    _update_ktp_footer(ws, half_year=half_year, lesson_count=lesson_count)


def build_ktp_xlsx(
    periods: list[tuple[int, list[date], list[date]]],
    *,
    group_name: str = '',
    weekday_slot_1: str = DEFAULT_WEEKDAY_SLOT_1,
    weekday_slot_2: str = DEFAULT_WEEKDAY_SLOT_2,
    template_path: Path | None = None,
) -> BytesIO:
    if not periods:
        raise ValueError('Не указано ни одного полугодия для заполнения')

    path = template_path or KTP_TEMPLATE_PATH
    if not path.exists():
        raise FileNotFoundError(f'Шаблон КТП не найден: {path}')

    wb = load_workbook(path)
    filled_half_years = {half_year for half_year, _, _ in periods}
    metadata = {
        'group_name': group_name,
        'weekday_slot_1': weekday_slot_1,
        'weekday_slot_2': weekday_slot_2,
    }

    for half_year in (1, 2):
        ws = _get_worksheet(wb, half_year)
        if half_year in filled_half_years:
            left_dates, right_dates = next(
                (left, right) for hy, left, right in periods if hy == half_year
            )
            fill_ktp_sheet(
                ws,
                left_dates,
                right_dates,
                half_year=half_year,
                **metadata,
            )
        else:
            clear_ktp_sheet(ws, half_year=half_year, **metadata)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


def build_ktp_docx(
    lesson_dates: list[date],
    *,
    group_name: str = '',
    program_name: str = '',
) -> BytesIO:
    doc = Document()
    doc.add_heading('Календарно-тематическое планирование', level=1)
    if program_name:
        doc.add_paragraph(f'Направление: {program_name}')
    if group_name:
        doc.add_paragraph(f'Группа: {group_name}')

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    headers = table.rows[0].cells
    headers[0].text = '№'
    headers[1].text = 'Дата'
    headers[2].text = 'Тема занятия'

    for index, lesson_date in enumerate(lesson_dates, start=1):
        row = table.add_row().cells
        row[0].text = str(index)
        row[1].text = lesson_date.strftime('%d.%m.%Y')
        row[2].text = ''

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
