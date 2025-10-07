import os

home_dir = os.path.expanduser("~")
targets = [
    os.path.join("OneDrive", "Desktop"),
    os.path.join("OneDrive", "Documents"),
    os.path.join('OneDrive', "Downloads")
]

for folder in targets:
    target_path = os.path.join(home_dir, folder)
    print(f"Checking: {target_path} -> {'Exists' if os.path.exists(target_path) else 'Missing'}")