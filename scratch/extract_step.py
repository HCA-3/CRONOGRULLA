import json
import os

p = os.path.expanduser("~/.gemini/antigravity/brain/4903879f-82ad-4c93-ab27-8a9d5d3b00b0/.system_generated/logs/transcript_full.jsonl")
with open(p, encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i in [701, 703, 705]:
            data = json.loads(line)
            print(f"=== STEP {i} ===")
            print(data.get("content", ""))

