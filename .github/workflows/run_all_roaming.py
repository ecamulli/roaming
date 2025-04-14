name: Daily Roaming Script

on:
  schedule:
    - cron: '50 14 * * *'  # 11AM ET = 15:00 UTC

jobs:
  run-roaming-script:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run get_roaming_data_fast.py
      run: |
        python roaming/Scripts/get_roaming_data_fast.py
