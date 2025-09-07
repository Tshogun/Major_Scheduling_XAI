import random
from typing import Dict, List, Tuple
from pydantic import BaseModel

class TimetableInput(BaseModel):
    num_classes: int
    num_subjects: int
    num_teachers: int
    num_days: int
    slots_per_day: int
    class_subjects: Dict[int, List[int]]
    subject_sessions_per_week: Dict[Tuple[int, int], int]
    teacher_subjects: Dict[int, List[int]]

def generate_input(
    num_classes: int = None,
    num_subjects: int = None,
    num_teachers: int = None,
    num_days: int = None,
    slots_per_day: int = None,
) -> TimetableInput:
    # Vary parameters within reasonable ranges if not provided
    num_classes = num_classes or random.randint(3, 8)
    num_subjects = num_subjects or random.randint(5, 12)
    num_teachers = num_teachers or random.randint(4, 10)
    num_days = num_days or random.randint(4, 6)
    slots_per_day = slots_per_day or random.randint(4, 8)

    # Generate class_subjects: each class has between 1 and all subjects
    class_subjects = {}
    for cls in range(num_classes):
        num_cls_subjects = random.randint(1, num_subjects)
        class_subjects[cls] = random.sample(range(num_subjects), num_cls_subjects)

    # Generate subject_sessions_per_week ensuring total sessions per class fit in schedule
    subject_sessions_per_week = {}
    for cls, subjects in class_subjects.items():
        max_sessions = num_days * slots_per_day
        # randomly allocate sessions to subjects but sum must not exceed max_sessions
        remaining_sessions = max_sessions
        # shuffle subjects to randomize distribution order
        shuffled_subjects = subjects.copy()
        random.shuffle(shuffled_subjects)

        for i, subj in enumerate(shuffled_subjects):
            # For the last subject, assign all remaining sessions
            if i == len(shuffled_subjects) - 1:
                sessions = remaining_sessions
            else:
                # Assign between 1 and remaining_sessions/(remaining_subjects)
                max_for_subject = max(1, remaining_sessions - (len(shuffled_subjects) - i - 1))
                sessions = random.randint(1, max_for_subject)
            sessions = min(sessions, 6)  # max 6 sessions/week per subject for realism
            subject_sessions_per_week[(cls, subj)] = sessions
            remaining_sessions -= sessions
            if remaining_sessions <= 0:
                # Assign 0 sessions to remaining subjects if any
                for rem_subj in shuffled_subjects[i+1:]:
                    subject_sessions_per_week[(cls, rem_subj)] = 0
                break

    # Generate teacher_subjects: distribute qualifications unevenly for diversity
    teacher_subjects = {}
    for t in range(num_teachers):
        # Teacher qualified for 1 to half of subjects, or possibly all for some
        max_qualifications = max(1, num_subjects // 2)
        if random.random() < 0.2:  # 20% teachers qualified for all subjects
            qualified = list(range(num_subjects))
        else:
            num_qual = random.randint(1, max_qualifications)
            qualified = random.sample(range(num_subjects), num_qual)
        teacher_subjects[t] = qualified

    return TimetableInput(
        num_classes=num_classes,
        num_subjects=num_subjects,
        num_teachers=num_teachers,
        num_days=num_days,
        slots_per_day=slots_per_day,
        class_subjects=class_subjects,
        subject_sessions_per_week=subject_sessions_per_week,
        teacher_subjects=teacher_subjects,
    )
