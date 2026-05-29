"""Формирование отчёта «Комплектация» (Excel) и сводки для менеджера."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path

from django.db.models import Q
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter

from core.models import Course
from schedule.models import Enrollment, Group

KOMPLEKTOVANIE_DATA_DIR = Path(__file__).resolve().parent.parent / 'reports' / 'vkr' / 'data'
KOMPLEKTOVANIE_TEMPLATE_PATH = KOMPLEKTOVANIE_DATA_DIR / 'Комплектование  МЗ октябрь  2025.xlsx'
KOMPLEKTOVANIE_TEMPLATE_SHEET = '01.10.2025'

DATA_START_ROW = 11
HEADER_ROWS = 10
LAST_COL = 16

DIRECTION_ORDER = [
    Course.Direction.NATURAL_SCIENCE,
    Course.Direction.TECHNICAL,
    Course.Direction.SOCIAL_HUMANITIES,
    Course.Direction.SPORTS,
    Course.Direction.ARTISTIC,
]


@dataclass
class RowCounts:
    krugk_total: int = 0
    deti_total: int = 0
    preschool_k: int = 0
    preschool_d: int = 0
    elementary_k: int = 0
    elementary_d: int = 0
    basic_k: int = 0
    basic_d: int = 0
    secondary_k: int = 0
    secondary_d: int = 0
    adult_k: int = 0
    adult_d: int = 0

    def write_to_row(self, ws, row: int, groups_count: int | None = None) -> None:
        if groups_count is not None:
            ws.cell(row, 4, groups_count)
        values = [
            self.krugk_total,
            self.deti_total,
            self.preschool_k,
            self.preschool_d,
            self.elementary_k,
            self.elementary_d,
            self.basic_k,
            self.basic_d,
            self.secondary_k,
            self.secondary_d,
            self.adult_d if self.adult_d else None,
            None,
        ]
        for offset, value in enumerate(values, start=5):
            ws.cell(row, offset, value)


@dataclass
class CourseReportRow:
    index: int
    title: str
    teacher_name: str
    groups_count: int
    counts: RowCounts


@dataclass
class DirectionBlock:
    header: str
    courses: list[CourseReportRow]
    totals: RowCounts


@dataclass
class KomplektovanieReport:
    report_date: date
    directions: list[DirectionBlock]
    grand_totals: RowCounts
    warnings: list[str] = field(default_factory=list)


def pupil_age_on(birth_date: date | None, on_date: date) -> int | None:
    if not birth_date:
        return None
    years = on_date.year - birth_date.year
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def age_bracket(age: int | None) -> str | None:
    if age is None:
        return None
    if 5 <= age <= 7:
        return 'preschool'
    if 8 <= age <= 10:
        return 'elementary'
    if 11 <= age <= 14:
        return 'basic'
    if 15 <= age <= 17:
        return 'secondary'
    if age >= 18:
        return 'adult'
    return None


def _teacher_display(group: Group) -> str:
    if not group.teacher:
        return '—'
    user = group.teacher.user
    return user.get_full_name().strip() or user.username


def _active_groups_qs(report_date: date):
    return (
        Group.objects.filter(
            status=Group.Status.ACTIVE,
            start_date__lte=report_date,
            end_date__gte=report_date,
            course__isnull=False,
        )
        .select_related('course', 'teacher__user')
        .order_by('course__direction', 'course__title', 'name')
    )


def _active_enrollments_for_groups(group_ids: list[int], report_date: date):
    if not group_ids:
        return []
    return list(
        Enrollment.objects.filter(
            group_id__in=group_ids,
            date_from__lte=report_date,
        )
        .filter(Q(date_to__isnull=True) | Q(date_to__gte=report_date))
        .select_related('pupil__user')
    )


def _counts_from_enrollments(enrollments, report_date: date) -> RowCounts:
    counts = RowCounts()
    if not enrollments:
        return counts

    counts.krugk_total = len(enrollments)
    counts.deti_total = len({e.pupil_id for e in enrollments})

    by_bracket_k: dict[str, int] = defaultdict(int)
    by_bracket_pupils: dict[str, set[int]] = defaultdict(set)

    for enrollment in enrollments:
        bracket = age_bracket(pupil_age_on(enrollment.pupil.birth_date, report_date))
        if not bracket:
            continue
        by_bracket_k[bracket] += 1
        by_bracket_pupils[bracket].add(enrollment.pupil_id)

    counts.preschool_k = by_bracket_k['preschool']
    counts.preschool_d = len(by_bracket_pupils['preschool'])
    counts.elementary_k = by_bracket_k['elementary']
    counts.elementary_d = len(by_bracket_pupils['elementary'])
    counts.basic_k = by_bracket_k['basic']
    counts.basic_d = len(by_bracket_pupils['basic'])
    counts.secondary_k = by_bracket_k['secondary']
    counts.secondary_d = len(by_bracket_pupils['secondary'])
    counts.adult_k = by_bracket_k['adult']
    counts.adult_d = len(by_bracket_pupils['adult'])
    return counts


def _merge_direction_totals(blocks: list[DirectionBlock]) -> RowCounts:
    all_enrollment_ids = []
    grand = RowCounts()
    for block in blocks:
        grand.krugk_total += block.totals.krugk_total
        grand.preschool_k += block.totals.preschool_k
        grand.elementary_k += block.totals.elementary_k
        grand.basic_k += block.totals.basic_k
        grand.secondary_k += block.totals.secondary_k
        grand.adult_k += block.totals.adult_k
    return grand


def _direction_totals_from_enrollments(enrollments, report_date: date) -> RowCounts:
    return _counts_from_enrollments(enrollments, report_date)


def build_komplektovanie_report(report_date: date) -> KomplektovanieReport:
    warnings: list[str] = []
    groups = list(_active_groups_qs(report_date))

    groups_by_course: dict[int, list[Group]] = defaultdict(list)
    for group in groups:
        groups_by_course[group.course_id].append(group)

    courses_without_direction: list[str] = []
    for course_id, course_groups in groups_by_course.items():
        course = course_groups[0].course
        if course.direction is None:
            courses_without_direction.append(course.title)

    if courses_without_direction:
        warnings.append(
            'Курсы без направленности (не попали в отчёт): '
            + ', '.join(sorted(courses_without_direction))
        )

    all_enrollments = _active_enrollments_for_groups(
        [g.id for g in groups if g.course.direction is not None],
        report_date,
    )
    pupils_without_birth = {
        e.pupil_id for e in all_enrollments if not e.pupil.birth_date
    }
    if pupils_without_birth:
        warnings.append(
            f'У {len(pupils_without_birth)} зачислений нет даты рождения — '
            'возрастные колонки для этих детей не заполнены.'
        )

    direction_blocks: list[DirectionBlock] = []
    grand_enrollments: list = []

    for direction in DIRECTION_ORDER:
        header = Course.DIRECTION_HEADERS[direction]
        course_rows: list[CourseReportRow] = []
        direction_enrollments: list = []
        course_ids = sorted(
            {
                cid
                for cid, gs in groups_by_course.items()
                if gs[0].course.direction == direction
            },
            key=lambda cid: groups_by_course[cid][0].course.title,
        )
        for index, course_id in enumerate(course_ids, start=1):
            course_groups = groups_by_course[course_id]
            course = course_groups[0].course
            group_ids = [g.id for g in course_groups]
            enrollments = [e for e in all_enrollments if e.group_id in group_ids]
            direction_enrollments.extend(enrollments)
            counts = _counts_from_enrollments(enrollments, report_date)
            course_rows.append(
                CourseReportRow(
                    index=index,
                    title=course.title,
                    teacher_name=_teacher_display(course_groups[0]),
                    groups_count=len(course_groups),
                    counts=counts,
                )
            )

        if not course_rows:
            continue

        totals = _direction_totals_from_enrollments(direction_enrollments, report_date)
        direction_blocks.append(
            DirectionBlock(header=header, courses=course_rows, totals=totals)
        )
        grand_enrollments.extend(direction_enrollments)

    grand_totals = _direction_totals_from_enrollments(grand_enrollments, report_date)

    return KomplektovanieReport(
        report_date=report_date,
        directions=direction_blocks,
        grand_totals=grand_totals,
        warnings=warnings,
    )


def _unmerge_from_row(ws, start_row: int) -> None:
    to_remove = []
    for merged in ws.merged_cells.ranges:
        if merged.min_row >= start_row:
            to_remove.append(str(merged))
    for ref in to_remove:
        ws.unmerge_cells(ref)


def _write_sum_formulas(ws, row: int, first_data_row: int, last_data_row: int) -> None:
    for col in range(4, LAST_COL + 1):
        if col == 15:
            continue
        letter = get_column_letter(col)
        ws.cell(row, col, f'=SUM({letter}{first_data_row}:{letter}{last_data_row})')


def _write_course_row(ws, row: int, course_row: CourseReportRow) -> None:
    ws.cell(row, 1, course_row.index)
    ws.cell(row, 2, course_row.title)
    ws.cell(row, 3, course_row.teacher_name)
    course_row.counts.write_to_row(ws, row, groups_count=course_row.groups_count)


def _write_direction_header(ws, row: int, header: str) -> None:
    ws.cell(row, 1, header)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=LAST_COL)
    ws.cell(row, 1).alignment = Alignment(horizontal='left', vertical='center')


def _write_itogo_row(ws, row: int, totals: RowCounts, first_data_row: int, last_data_row: int) -> None:
    ws.cell(row, 2, 'Итого')
    _write_sum_formulas(ws, row, first_data_row, last_data_row)
    ws.cell(row, 6, totals.deti_total)
    ws.cell(row, 8, totals.preschool_d)
    ws.cell(row, 10, totals.elementary_d)
    ws.cell(row, 12, totals.basic_d)
    ws.cell(row, 14, totals.secondary_d)
    if totals.adult_d:
        ws.cell(row, 15, totals.adult_d)


def build_komplektovanie_xlsx(report_date: date) -> BytesIO:
    if not KOMPLEKTOVANIE_TEMPLATE_PATH.is_file():
        raise FileNotFoundError(
            f'Шаблон комплектации не найден: {KOMPLEKTOVANIE_TEMPLATE_PATH}'
        )

    report = build_komplektovanie_report(report_date)
    wb = load_workbook(KOMPLEKTOVANIE_TEMPLATE_PATH)
    if KOMPLEKTOVANIE_TEMPLATE_SHEET in wb.sheetnames:
        ws = wb[KOMPLEKTOVANIE_TEMPLATE_SHEET]
    else:
        ws = wb.active

    sheet_title = report_date.strftime('%d.%m.%Y')
    ws.title = sheet_title[:31]

    for name in list(wb.sheetnames):
        if name != ws.title:
            del wb[name]

    _unmerge_from_row(ws, DATA_START_ROW)
    if ws.max_row > HEADER_ROWS:
        ws.delete_rows(DATA_START_ROW, ws.max_row - HEADER_ROWS)

    current_row = DATA_START_ROW
    itogo_rows: list[int] = []

    for block in report.directions:
        _write_direction_header(ws, current_row, block.header)
        current_row += 1
        first_data_row = current_row
        for course_row in block.courses:
            _write_course_row(ws, current_row, course_row)
            current_row += 1
        last_data_row = current_row - 1
        _write_itogo_row(ws, current_row, block.totals, first_data_row, last_data_row)
        itogo_rows.append(current_row)
        current_row += 1

    ws.cell(current_row, 2, 'Итого')
    total_groups = sum(
        course_row.groups_count
        for block in report.directions
        for course_row in block.courses
    )
    ws.cell(current_row, 4, total_groups)
    for col in (5, 7, 9, 11, 13):
        letter = get_column_letter(col)
        parts = [f'{letter}{row}' for row in itogo_rows]
        if parts:
            ws.cell(current_row, col, '=' + '+'.join(parts))
    ws.cell(current_row, 5, report.grand_totals.krugk_total)
    ws.cell(current_row, 6, report.grand_totals.deti_total)
    ws.cell(current_row, 8, report.grand_totals.preschool_d)
    ws.cell(current_row, 10, report.grand_totals.elementary_d)
    ws.cell(current_row, 12, report.grand_totals.basic_d)
    ws.cell(current_row, 14, report.grand_totals.secondary_d)
    if report.grand_totals.adult_d:
        ws.cell(current_row, 15, report.grand_totals.adult_d)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
