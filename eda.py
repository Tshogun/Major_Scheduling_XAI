import os
import json
import pandas as pd
import streamlit as st
import plotly.figure_factory as ff
import plotly.express as px
import numpy as np

DATASET_DIR = "dataset"

# Load all dataset JSON files
@st.cache_data(show_spinner=False)
def load_data():
    files = [f for f in os.listdir(DATASET_DIR) if f.endswith(".json")]
    data = []
    for file in files:
        path = os.path.join(DATASET_DIR, file)
        with open(path) as f:
            js = json.load(f)
            js["_file"] = file
            data.append(js)
    return data

def extract_features(instance_sol):
    instance = instance_sol["input"]
    solution = instance_sol["solution"]

    activities = instance["activities"]
    resources = instance["resources"]

    num_activities = len(activities)

    modes_per_activity = [len(act["modes"]) for act in activities]
    avg_modes = sum(modes_per_activity) / num_activities if num_activities > 0 else 0
    min_modes = min(modes_per_activity) if num_activities > 0 else 0
    max_modes = max(modes_per_activity) if num_activities > 0 else 0

    renewable_caps = resources.get("renewable", [])
    nonrenewable_caps = resources.get("nonrenewable", [])

    total_precedence = sum(len(act.get("successors", [])) for act in activities)

    makespan = solution.get("makespan", None)

    durations = [mode["duration"] for act in activities for mode in act["modes"]]
    avg_duration = sum(durations) / len(durations) if durations else None
    min_duration = min(durations) if durations else None
    max_duration = max(durations) if durations else None

    return {
        "file": instance_sol["_file"],
        "num_activities": num_activities,
        "avg_modes": avg_modes,
        "min_modes": min_modes,
        "max_modes": max_modes,
        "renewable_1_cap": renewable_caps[0] if len(renewable_caps) > 0 else None,
        "renewable_2_cap": renewable_caps[1] if len(renewable_caps) > 1 else None,
        "nonrenewable_1_cap": nonrenewable_caps[0] if len(nonrenewable_caps) > 0 else None,
        "total_precedence_edges": total_precedence,
        "makespan": makespan,
        "avg_duration": avg_duration,
        "min_duration": min_duration,
        "max_duration": max_duration
    }

def plot_gantt(instance_sol):
    solution = instance_sol["solution"]
    activities = solution["activities"]

    df = []
    for act in activities:
        df.append(dict(Task=f"Activity {act['id']}",
                       Start=act["start"],
                       Finish=act["end"],
                       Mode=act["mode"]))
    fig = ff.create_gantt(df, index_col='Mode', show_colorbar=True, group_tasks=True)
    fig.update_layout(title="Gantt Chart of Scheduled Activities",
                      xaxis_title="Time",
                      yaxis_title="Activities")
    return fig

def show_instance_details(instance_sol):
    st.subheader(f"Instance: {instance_sol['_file']}")

    input_data = instance_sol["input"]
    solution = instance_sol["solution"]

    st.markdown("### Input Summary")
    st.write(f"Number of activities: {len(input_data['activities'])}")
    st.write(f"Renewable resources capacities: {input_data['resources'].get('renewable', [])}")
    st.write(f"Nonrenewable resources capacities: {input_data['resources'].get('nonrenewable', [])}")

    # Table of activities modes summary
    mode_summary = []
    for act in input_data["activities"]:
        mode_summary.append({
            "Activity ID": act["id"],
            "Num Modes": len(act["modes"]),
            "Successors": act.get("successors", [])
        })
    st.write(pd.DataFrame(mode_summary))

    # Show Gantt Chart for solution
    st.markdown("### Solution Summary")
    st.write(f"Overall makespan: {solution.get('makespan', 'N/A')}")
    st.plotly_chart(plot_gantt(instance_sol), use_container_width=True)

    # Activity schedule table
    st.markdown("### Activity Schedule")
    st.write(pd.DataFrame(solution["activities"]))

def main():
    st.title("MRCPSP Dataset Explorer & Visualization")

    data = load_data()
    st.sidebar.header("Filters & Selection")

    # Dataset summary & filters
    df_features = pd.DataFrame([extract_features(d) for d in data])

    # Filters for number of activities and makespan
    min_act = int(df_features["num_activities"].min())
    max_act = int(df_features["num_activities"].max())
    act_filter = st.sidebar.slider("Number of Activities", min_act, max_act, (min_act, max_act))

    min_makespan = int(df_features["makespan"].min())
    max_makespan = int(df_features["makespan"].max())
    makespan_filter = st.sidebar.slider("Makespan", min_makespan, max_makespan, (min_makespan, max_makespan))

    filtered_df = df_features[
        (df_features["num_activities"] >= act_filter[0]) &
        (df_features["num_activities"] <= act_filter[1]) &
        (df_features["makespan"] >= makespan_filter[0]) &
        (df_features["makespan"] <= makespan_filter[1])
    ]

    st.sidebar.markdown(f"### Filtered Instances: {len(filtered_df)}")

    # Show dataset summary stats
    st.header("Dataset Summary Statistics")
    st.write(filtered_df.describe())

    # Show correlations heatmap
    st.subheader("Feature Correlation Heatmap")
    corr = filtered_df.select_dtypes(include=['number']).corr()
    st.write(px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r'))

    # Select instance to explore details
    st.sidebar.markdown("---")
    selected_file = st.sidebar.selectbox("Select Instance File", options=filtered_df["file"].tolist())

    selected_instance = next((x for x in data if x["_file"] == selected_file), None)
    if selected_instance:
        show_instance_details(selected_instance)
    else:
        st.warning("Selected instance not found!")

if __name__ == "__main__":
    main()
