import subprocess

scripts = [
    "get_roaming_data.py",
    "aggregate_roaming_data.py"
    "merge_with_vintage.py",
    "get_driver_vintage.py",
    "latest_intel_driver.py"

]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script], check=True)  # Runs each script sequentially
print("All scripts executed successfully!")
