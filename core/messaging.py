"""Переписка родитель — педагог."""
from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from accounts.models import Parent, Pupil, Teacher
from schedule.models import Enrollment

from .models import Message, MessageThread

User = get_user_model()


def pupils_for_teacher(teacher: Teacher):
    """Ученики из активных групп педагога."""
    pupil_ids = (
        Enrollment.objects.filter(
            date_to__isnull=True,
            group__teacher=teacher,
        )
        .values_list('pupil_id', flat=True)
        .distinct()
    )
    return Pupil.objects.filter(pk__in=pupil_ids).select_related('user').order_by(
        'user__last_name', 'user__first_name',
    )


def parents_for_teacher_pupil(teacher: Teacher, pupil: Pupil) -> list[Parent]:
    """Родители ребёнка, если педагог ведёт его активную группу."""
    if not pupils_for_teacher(teacher).filter(pk=pupil.pk).exists():
        return []
    return list(pupil.parents.select_related('user').all())


def teachers_for_parent_pupil(parent: Parent, pupil: Pupil) -> list[Teacher]:
    """Педагоги активных групп ребёнка, доступные этому родителю."""
    if not parent.children.filter(pk=pupil.pk).exists():
        return []
    teacher_ids = (
        Enrollment.objects.filter(
            pupil=pupil,
            date_to__isnull=True,
            group__teacher__isnull=False,
        )
        .values_list('group__teacher_id', flat=True)
        .distinct()
    )
    return list(Teacher.objects.filter(pk__in=teacher_ids).select_related('user'))


def get_or_create_thread(pupil: Pupil, parent: Parent, teacher: Teacher) -> MessageThread:
    thread, _ = MessageThread.objects.get_or_create(
        pupil=pupil,
        parent=parent,
        teacher=teacher,
    )
    return thread


def post_message(thread: MessageThread, author: User, body: str) -> Message:
    is_parent = hasattr(author, 'parent_profile')
    is_teacher = hasattr(author, 'teacher_profile')
    message = Message.objects.create(
        thread=thread,
        author=author,
        body=body.strip(),
        read_by_parent=is_parent,
        read_by_teacher=is_teacher,
    )
    MessageThread.objects.filter(pk=thread.pk).update(updated_at=message.created_at)
    return message


def mark_thread_read(thread: MessageThread, reader: User) -> None:
    qs = Message.objects.filter(thread=thread).exclude(author=reader)
    if hasattr(reader, 'parent_profile'):
        qs.update(read_by_parent=True)
    elif hasattr(reader, 'teacher_profile'):
        qs.update(read_by_teacher=True)


def unread_count_for_parent(parent: Parent) -> int:
    return Message.objects.filter(
        thread__parent=parent,
        read_by_parent=False,
    ).exclude(author=parent.user).count()


def unread_count_for_teacher(teacher: Teacher) -> int:
    return Message.objects.filter(
        thread__teacher=teacher,
        read_by_teacher=False,
    ).exclude(author=teacher.user).count()


def _messages_prefetch():
    return Prefetch('messages', queryset=Message.objects.select_related('author').order_by('created_at'))


def parent_threads(parent: Parent):
    return (
        MessageThread.objects.filter(parent=parent)
        .select_related('pupil__user', 'teacher__user')
        .prefetch_related(_messages_prefetch())
        .order_by('-updated_at')
    )


def teacher_threads(teacher: Teacher):
    return (
        MessageThread.objects.filter(teacher=teacher)
        .select_related('pupil__user', 'parent__user')
        .prefetch_related(_messages_prefetch())
        .order_by('-updated_at')
    )


def thread_unread_for_parent(thread: MessageThread, parent: Parent) -> int:
    return thread.messages.filter(read_by_parent=False).exclude(author=parent.user).count()


def thread_unread_for_teacher(thread: MessageThread, teacher: Teacher) -> int:
    return thread.messages.filter(read_by_teacher=False).exclude(author=teacher.user).count()
