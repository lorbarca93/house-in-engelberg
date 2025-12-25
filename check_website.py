import json
import os

# Check cases_index.json
with open('website/data/cases_index.json', 'r') as f:
    cases_index = json.load(f)

cases = cases_index['cases']
print('=== WEBSITE CASES VALIDATION ===')
print(f'Found {len(cases)} cases in index:')
print()

all_valid = True
for case in cases:
    case_name = case['case_name']
    display_name = case['display_name']
    status = case.get('status', 'unknown')

    # Check if data files exist
    data_files = case.get('data_files', {})
    required_files = [
        f'website/data/{data_files.get("base_case_analysis", "")}',
        f'website/data/{data_files.get("sensitivity", "")}',
        f'website/data/{data_files.get("sensitivity_coc", "")}',
        f'website/data/{data_files.get("sensitivity_ncf", "")}',
        f'website/data/{data_files.get("monte_carlo", "")}',
        f'website/{case_name}_monte_carlo_report.html'
    ]

    files_exist = all(os.path.exists(f) and f != 'website/data/' for f in required_files)

    status_icon = '[OK]' if status == 'success' and files_exist else '[ISSUE]'

    print(f'{status_icon} {case_name} ({display_name}) - Status: {status}')
    if not files_exist:
        missing = [f for f in required_files if not os.path.exists(f) and f != 'website/data/']
        if missing:
            print(f'    Missing files: {missing}')
    print()

successful_cases = sum(1 for case in cases if case.get('status') == 'success')
total_cases = len(cases)
print(f'Successful cases: {successful_cases}/{total_cases}')

if successful_cases == total_cases:
    print('SUCCESS: All cases are configured correctly!')
else:
    print('WARNING: Some cases have issues!')

# Check main website files
print()
print('=== WEBSITE FILES CHECK ===')
main_files = ['website/index.html', 'website/data/cases_index.json']
for file in main_files:
    exists = os.path.exists(file)
    status = '[OK]' if exists else '[MISSING]'
    print(f'{status} {file}')

if all(os.path.exists(f) for f in main_files):
    print('SUCCESS: Main website files are present!')
else:
    print('WARNING: Some main website files are missing!')
