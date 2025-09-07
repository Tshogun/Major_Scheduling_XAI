import os
import json
import random
import streamlit as st
from typing import Dict, List, Tuple
from pydantic import BaseModel
import pandas as pd


class TimetableInput(BaseModel):
    num_classes: int
    num_subjects: int
    num_teachers: int
    num_days: int
    slots_per_day: int
    class_subjects: Dict[int, List[int]]
    subject_sessions_per_week: Dict[Tuple[int, int], int]
    teacher_subjects: Dict[int, List[int]]


def pretty_print_timetable(timetable, class_names=None, subject_names=None, teacher_names=None):
    # This function is no longer used but you can keep or remove
    pass


def timetable_to_dataframe(timetable, class_id, class_names, subject_names, teacher_names):
    """
    Convert timetable[class_id] into a pandas DataFrame with
    days as rows, slots as columns, and subject/teacher info as cell text.
    """
    days = len(timetable[str(class_id)])
    slots = len(timetable[str(class_id)][0])
    data = []

    for d in range(days):
        row = []
        for s in range(slots):
            subj, teacher = timetable[str(class_id)][d][s]
            if subj == -1 or teacher == -1:
                cell = "Free"
            else:
                subj_str = subject_names.get(subj, f"S{subj}")
                teacher_str = teacher_names.get(teacher, f"T{teacher}")
                cell = f"{subj_str}\n{teacher_str}"
            row.append(cell)
        data.append(row)

    # Columns as Slot 1, Slot 2, ...
    columns = [f"Slot {i+1}" for i in range(slots)]
    df = pd.DataFrame(data, columns=columns)
    df.index = [f"Day {i+1}" for i in range(days)]
    return df


def main():
    st.title("Timetable Viewer with Tables")

    dataset_folder = "./dataset"
    files = sorted([f for f in os.listdir(dataset_folder) if f.endswith(".json")])
    if not files:
        st.error(f"No JSON files found in `{dataset_folder}` folder.")
        return

    instance_file = st.selectbox("Select timetable instance", files)

    filepath = os.path.join(dataset_folder, instance_file)
    with open(filepath, "r") as f:
        data = json.load(f)

    timetable = data.get("output")
    if timetable is None:
        st.error("No timetable found in the selected file.")
        return

    num_classes = len(timetable)

    max_subject_id = -1
    max_teacher_id = -1
    for class_id in timetable:
        for day in timetable[class_id]:
            for subj, teacher in day:
                if subj > max_subject_id:
                    max_subject_id = subj
                if teacher > max_teacher_id:
                    max_teacher_id = teacher

    class_names = {i: f"Class {chr(65+i)}" for i in range(num_classes)}
    subject_names = {i: f"Subject {i}" for i in range(max_subject_id + 1)}
    teacher_names = {i: f"Teacher {i}" for i in range(max_teacher_id + 1)}

    st.subheader(f"Timetable for {instance_file}")

    for c in range(num_classes):
        st.markdown(f"### {class_names.get(c, f'Class {c}')}")
        df = timetable_to_dataframe(timetable, c, class_names, subject_names, teacher_names)
        st.table(df)

    with st.expander("Show raw timetable JSON"):
        st.json(timetable)


if __name__ == "__main__":
    main()
