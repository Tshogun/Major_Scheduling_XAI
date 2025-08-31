import random

def generate_single_instance_dict():
    # Number of activities: wider range (10-30)
    num_activities = random.randint(10, 30)

    # Resource definitions: more resource types and variable capacities
    num_renewable = random.randint(2, 5)
    num_nonrenewable = random.randint(1, 3)
    
    resources = {
        "renewable": [random.randint(5, 15) for _ in range(num_renewable)],
        "nonrenewable": [random.randint(50, 150) for _ in range(num_nonrenewable)]
    }

    activities = []

    # Predecessors data to help create a DAG
    predecessors = {i: set() for i in range(num_activities)}

    for i in range(num_activities):
        modes = []
        # Number of modes varies more (2-5)
        for _ in range(random.randint(2, 5)):
            duration = random.randint(1, 15)  # wider duration range
            renewable = [random.randint(0, 5) for _ in range(num_renewable)]
            nonrenewable = [random.randint(0, 20) for _ in range(num_nonrenewable)]
            modes.append({
                "duration": duration,
                "renewable": renewable,
                "nonrenewable": nonrenewable
            })

        # Randomly assign successors: each activity can have 0 to 3 successors later in order
        max_successors = 3
        possible_successors = list(range(i+1, num_activities))
        num_successors = random.randint(0, min(max_successors, len(possible_successors)))
        successors = random.sample(possible_successors, num_successors) if num_successors > 0 else []

        # Update predecessors map
        for succ in successors:
            predecessors[succ].add(i)

        activities.append({
            "id": i,
            "modes": modes,
            "successors": successors
        })

    # Optional: make sure there are no activities without predecessors or successors to ensure connectivity
    # Add artificial start (id=-1) and end (id=num_activities) if needed
    
    # Check for activities with no predecessors (start nodes)
    start_nodes = [i for i, preds in predecessors.items() if len(preds) == 0]
    if len(start_nodes) == 0:
        # randomly pick one activity to be start node by removing predecessors
        victim = random.randint(0, num_activities - 1)
        predecessors[victim] = set()
    # Similarly for end nodes (activities with no successors)
    end_nodes = [i for i, act in enumerate(activities) if len(act['successors']) == 0]
    if len(end_nodes) == 0:
        victim = random.randint(0, num_activities - 1)
        activities[victim]['successors'] = []

    instance = {
        "activities": activities,
        "resources": resources
    }
    return instance
