import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\dsant\.gemini\antigravity-ide\brain\416bb32a-5076-455d-85d0-7415cb0f5dcd\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get("source") == "USER_EXPLICIT" and data.get("type") == "USER_INPUT":
                print(f"Step {data.get('step_index')}: {data.get('content')}")
        except Exception as e:
            pass
