import json
from ortools.sat.python import cp_model

def load_instance(filename):
    with open(filename) as f:
        return json.load(f)

def solve_mrcpsp(instance):
    model = cp_model.CpModel()

    activities = instance["activities"]
    renewable_caps = instance["resources"]["renewable"]
    nonrenewable_caps = instance["resources"]["nonrenewable"]

    num_activities = len(activities)
    num_renewable = len(renewable_caps)
    num_nonrenewable = len(nonrenewable_caps)

    horizon = sum(max(mode["duration"] for mode in act["modes"]) for act in activities) * 2

    start_vars = []
    end_vars = []
    mode_vars = []

    all_intervals = []
    presence_literals = []
    start_mode_vars_all = []
    end_mode_vars_all = []

    for i, act in enumerate(activities):
        start_var = model.NewIntVar(0, horizon, f'start_{i}')
        end_var = model.NewIntVar(0, horizon, f'end_{i}')
        start_vars.append(start_var)
        end_vars.append(end_var)
        mode_var = model.NewIntVar(0, len(act["modes"]) - 1, f'mode_{i}')
        mode_vars.append(mode_var)

        act_presences = []
        act_intervals = []
        start_mode_vars = []
        end_mode_vars = []

        for m_idx, mode in enumerate(act["modes"]):
            presence = model.NewBoolVar(f"presence_{i}_{m_idx}")
            start_mode = model.NewIntVar(0, horizon, f"start_{i}_{m_idx}")
            end_mode = model.NewIntVar(0, horizon, f"end_{i}_{m_idx}")

            interval = model.NewOptionalIntervalVar(start_mode, mode["duration"], end_mode, presence, f"interval_{i}_{m_idx}")

            model.Add(end_mode == start_mode + mode["duration"]).OnlyEnforceIf(presence)
            model.Add(start_mode == 0).OnlyEnforceIf(presence.Not())
            model.Add(end_mode == 0).OnlyEnforceIf(presence.Not())

            act_presences.append(presence)
            act_intervals.append(interval)
            start_mode_vars.append(start_mode)
            end_mode_vars.append(end_mode)

        model.AddExactlyOne(act_presences)

        for m_idx in range(len(act["modes"])):
            model.Add(start_vars[i] == start_mode_vars[m_idx]).OnlyEnforceIf(act_presences[m_idx])
            model.Add(end_vars[i] == end_mode_vars[m_idx]).OnlyEnforceIf(act_presences[m_idx])

        all_intervals.append(act_intervals)
        presence_literals.append(act_presences)
        start_mode_vars_all.append(start_mode_vars)
        end_mode_vars_all.append(end_mode_vars)

    for act in activities:
        i = act["id"]
        for succ in act["successors"]:
            model.Add(start_vars[succ] >= end_vars[i])

    for r in range(num_renewable):
        intervals_for_r = []
        demands_for_r = []
        for i, act in enumerate(activities):
            for m_idx, mode in enumerate(act["modes"]):
                demand = mode["renewable"][r]
                if demand > 0:
                    intervals_for_r.append(all_intervals[i][m_idx])
                    demands_for_r.append(demand)
        if intervals_for_r:
            model.AddCumulative(intervals_for_r, demands_for_r, renewable_caps[r])

    for r in range(num_nonrenewable):
        total_consumption = []
        for i, act in enumerate(activities):
            for m_idx, mode in enumerate(act["modes"]):
                demand = mode["nonrenewable"][r]
                if demand > 0:
                    total_consumption.append(demand * presence_literals[i][m_idx])
        if total_consumption:
            model.Add(sum(total_consumption) <= nonrenewable_caps[r])

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, end_vars)
    model.Minimize(makespan)

    solver = cp_model.CpSolver()
    
    # Solver tuning parameters
    solver.parameters.num_search_workers = 8          # Use 8 CPU threads (adjust if needed)
    solver.parameters.max_time_in_seconds = 60.0      # 60 seconds time limit per instance
    solver.parameters.log_search_progress = True      # Show solver progress logs
    solver.parameters.cp_model_presolve = True        # Enable presolve
    
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solution = {
            "makespan": solver.Value(makespan),
            "activities": []
        }
        for i, act in enumerate(activities):
            chosen_mode = None
            for m_idx, presence in enumerate(presence_literals[i]):
                if solver.Value(presence):
                    chosen_mode = m_idx
                    break
            start_time = solver.Value(start_vars[i])
            dur = act["modes"][chosen_mode]["duration"]
            solution["activities"].append({
                "id": act["id"],
                "mode": chosen_mode,
                "start": start_time,
                "duration": dur,
                "end": start_time + dur
            })
        return solution
    else:
        return None
