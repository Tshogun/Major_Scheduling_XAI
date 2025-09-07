from prefect import flow, task
from pipeline.input_generator import generate_input
from pipeline.solver import solve_timetable
from pipeline.data_saver import save_instance

@task(retries=1, retry_delay_seconds=1)
def generate_task():
    return generate_input()

@task
def solve_task(timetable_input):
    return solve_timetable(timetable_input)

@task
def save_task(index, input_data, solution):
    save_instance(index, input_data, solution)
    return True

@flow(name="Dataset Generation Pipeline")
def generate_dataset(n: int = 200, max_attempts_factor: int = 3):
    saved = 0
    attempts = 0
    max_attempts = n * max_attempts_factor

    while saved < n and attempts < max_attempts:
        attempts += 1
        print(f"🌀 Generating instance {attempts}...")

        problem_input = generate_task()  # <-- no .result()
        solution = solve_task(problem_input)  # <-- no .result()

        if solution:
            save_task(saved + 1, problem_input, solution)
            print(f"✅ Instance {saved + 1} saved.")
            saved += 1
        else:
            print(f"❌ No valid solution found.")

    print(f"\n🎉 Dataset generation complete: {saved} valid instances saved.")

if __name__ == "__main__":
    generate_dataset(1000)
