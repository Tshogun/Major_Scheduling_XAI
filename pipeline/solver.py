# pipeline/solver.py

from ortools.sat.python import cp_model
from pipeline.input_generator import TimetableInput

def solve_timetable(input_data: TimetableInput):
    model = cp_model.CpModel()

    # Extract input parameters
    num_classes = input_data.num_classes
    num_subjects = input_data.num_subjects
    num_teachers = input_data.num_teachers
    num_days = input_data.num_days
    slots_per_day = input_data.slots_per_day

    class_subjects = input_data.class_subjects
    subject_sessions = input_data.subject_sessions_per_week
    teacher_subjects = input_data.teacher_subjects

    # === VARIABLES ===
    # subject_vars[c, d, s]: int var for subject assigned to class c, day d, slot s
    # teacher_vars[c, d, s]: int var for teacher assigned to class c, day d, slot s
    subject_vars = {}
    teacher_vars = {}

    for c in range(num_classes):
        for d in range(num_days):
            for s in range(slots_per_day):
                subject_vars[c, d, s] = model.NewIntVar(-1, num_subjects - 1, f"sub_c{c}_d{d}_s{s}")
                teacher_vars[c, d, s] = model.NewIntVar(-1, num_teachers - 1, f"teach_c{c}_d{d}_s{s}")

    # === CONSTRAINTS ===

    # HC1: Subject Session Requirement
    for (cls, subj), required_sessions in subject_sessions.items():
        matches = []
        for d in range(num_days):
            for s in range(slots_per_day):
                match = model.NewBoolVar(f"cls{cls}_subj{subj}_d{d}_s{s}")
                model.Add(subject_vars[cls, d, s] == subj).OnlyEnforceIf(match)
                model.Add(subject_vars[cls, d, s] != subj).OnlyEnforceIf(match.Not())
                matches.append(match)
        model.Add(sum(matches) == required_sessions)

    # HC2: Teacher Qualification
    for c in range(num_classes):
        for d in range(num_days):
            for s in range(slots_per_day):
                subj_var = subject_vars[c, d, s]
                teach_var = teacher_vars[c, d, s]

                for subj in range(num_subjects):
                    for t in range(num_teachers):
                        if subj not in teacher_subjects.get(t, []):
                            is_subj_selected = model.NewBoolVar(f"is_subj_{subj}_at_c{c}_d{d}_s{s}")
                            model.Add(subj_var == subj).OnlyEnforceIf(is_subj_selected)
                            model.Add(subj_var != subj).OnlyEnforceIf(is_subj_selected.Not())
                            model.Add(teach_var != t).OnlyEnforceIf(is_subj_selected)

    # HC3: Class Exclusivity - only one subject and teacher per class slot
    for c in range(num_classes):
        for d in range(num_days):
            for s in range(slots_per_day):
                # Allowed assignments are either free (-1,-1) or valid subject-teacher pairs
                allowed_pairs = [(-1, -1)]
                for subj in class_subjects.get(c, []):
                    for t in teacher_subjects.get(t, []):
                        # We will filter further down, but it's safe here to check teacher qualification again
                        allowed_pairs.append((subj, t))
                # To cover teacher qualification, we instead allow all subject-teacher combos where teacher qualified
                allowed_pairs = [(-1, -1)]
                for subj in range(num_subjects):
                    if subj in class_subjects.get(c, []):
                        for t in range(num_teachers):
                            if subj in teacher_subjects.get(t, []):
                                allowed_pairs.append((subj, t))
                model.AddAllowedAssignments([subject_vars[c, d, s], teacher_vars[c, d, s]], allowed_pairs)

    # HC4: Teacher Exclusivity - a teacher teaches at most one class per slot
    for t in range(num_teachers):
        for d in range(num_days):
            for s in range(slots_per_day):
                assigned = []
                for c in range(num_classes):
                    assigned_bool = model.NewBoolVar(f"teach{t}_c{c}_d{d}_s{s}")
                    model.Add(teacher_vars[c, d, s] == t).OnlyEnforceIf(assigned_bool)
                    model.Add(teacher_vars[c, d, s] != t).OnlyEnforceIf(assigned_bool.Not())
                    assigned.append(assigned_bool)
                model.Add(sum(assigned) <= 1)

    # HC5: Unique Assignments - teacher assigned iff subject assigned
    for c in range(num_classes):
        for d in range(num_days):
            for s in range(slots_per_day):
                subject_assigned = model.NewBoolVar(f"subject_assigned_c{c}_d{d}_s{s}")
                model.Add(subject_vars[c, d, s] >= 0).OnlyEnforceIf(subject_assigned)
                model.Add(subject_vars[c, d, s] < 0).OnlyEnforceIf(subject_assigned.Not())

                model.Add(teacher_vars[c, d, s] >= 0).OnlyEnforceIf(subject_assigned)
                model.Add(teacher_vars[c, d, s] == -1).OnlyEnforceIf(subject_assigned.Not())

    # === SOLVE ===
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        timetable = {}
        for c in range(num_classes):
            timetable[c] = []
            for d in range(num_days):
                row = []
                for s in range(slots_per_day):
                    subj = solver.Value(subject_vars[c, d, s])
                    teach = solver.Value(teacher_vars[c, d, s])
                    row.append((subj, teach))
                timetable[c].append(row)
        return timetable
    else:
        return None
