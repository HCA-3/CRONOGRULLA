import json

file_path = "craneflow_data.json"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Successfully loaded craneflow_data.json!")
    measurements = data.get("measurements", [])
    print("Total measurements:", len(measurements))
    if measurements:
        first_m = measurements[0]
        print("\n--- First Measurement keys ---")
        print(first_m.keys())
        splits = first_m.get("splits", [])
        print("Total splits in first measurement:", len(splits))
        if splits:
            print("\n--- First split keys and content ---")
            print(splits[0])
            # Check how many have a 'therblig' key
            therbligs = [s.get("therblig") for m in measurements for s in m.get("splits", [])]
            unique_t = set(therbligs)
            print("\nUnique therblig values found:", unique_t)
            print("Total therblig records:", len(therbligs))
except Exception as e:
    print("Error:", e)
