# run_pipeline.py

from prefect import flow, task
from pipeline.input_generator import generate_input
from pipeline.solver import solve_timetable

@task
def generate_task():
    return generate_input()

@task
def solve_task(timetable_input):
    return solve_timetable(timetable_input)

@flow(name="Timetable Generation Pipeline")
def timetable_pipeline():
    timetable_input = generate_task()
    schedule = solve_task(timetable_input)
    return schedule

if __name__ == "__main__":
    result = timetable_pipeline()
    print(result)
