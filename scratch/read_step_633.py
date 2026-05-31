import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\dsant\.gemini\antigravity-ide\brain\416bb32a-5076-455d-85d0-7415cb0f5dcd\.system_generated\logs\transcript.jsonl"

print("Reading steps around 633...")
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            idx = data.get("step_index")
            if 630 <= idx <= 655:
                # print summary of the step
                print(f"Step {idx} ({data.get('source')}, {data.get('type')}):")
                content = data.get('content', '')
                if content:
                    print("  Content:", content[:200] + ("..." if len(content) > 200 else ""))
                tool_calls = data.get('tool_calls')
                if tool_calls:
                    print("  Tool Calls:", tool_calls)
        except Exception as e:
            pass
