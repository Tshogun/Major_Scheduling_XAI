import os
import json
from input_generator import generate_single_instance_dict
from solver import solve_mrcpsp

def save_instance_solution_pair(instance, solution, saved_id, output_dir="dataset"):
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"instance_{saved_id:04d}.json")
    full_data = {
        "input": instance,
        "solution": solution
    }
    with open(filename, "w") as f:
        json.dump(full_data, f, indent=2)

def main(target_count=100):
    saved_count = 0
    instance_id = 0

    while saved_count < target_count:
        instance = generate_single_instance_dict()
        solution = solve_mrcpsp(instance)

        if solution is not None:
            save_instance_solution_pair(instance, solution, saved_count)  # Use saved_count for naming!
            saved_count += 1
            print(f"[{saved_count}] Saved instance+solution #{saved_count:04d}")
        else:
            print(f"[SKIP] No solution for instance #{instance_id:04d}")

        instance_id += 1

if __name__ == "__main__":
    main()
