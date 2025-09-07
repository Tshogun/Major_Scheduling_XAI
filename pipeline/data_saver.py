import json
import os
from pipeline.input_generator import TimetableInput

def convert_keys_to_strings(obj):
    """Recursively convert dictionary keys from tuples to strings."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            # Convert tuple keys to strings
            if isinstance(k, tuple):
                k = str(k)
            new_dict[k] = convert_keys_to_strings(v)
        return new_dict
    elif isinstance(obj, list):
        return [convert_keys_to_strings(i) for i in obj]
    else:
        return obj

def save_instance(index: int, input_data: TimetableInput, output_data: dict, folder: str = "./dataset"):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"instance_{index:03d}.json")

    # Convert input_data to a serializable format
    input_dict = input_data.dict()
    input_dict = convert_keys_to_strings(input_dict)

    data = {
        "input": input_dict,
        "output": convert_keys_to_strings(output_data)
    }

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
