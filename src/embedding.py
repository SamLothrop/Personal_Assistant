import os
from pathlib import Path

desktop = '../'

for root, dirs, files in os.walk(desktop):
    for file in files:
        _, ext = os.path.splitext(file)
        if ext.lower() in {'.pdf', '.txt', '.jpeg', '.jpg'}:
            full_path = os.path.join(root, file)
            print(f"Found: {Path(full_path).name}")