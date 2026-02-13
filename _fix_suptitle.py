"""Fix remaining suptitle patterns with 'fontsize= 15' (space before 15)"""
import os

TARGET = os.path.join(os.path.dirname(__file__),
    'BatteryDataTool_260206_edit copy', 'BatteryDataTool_optRCD.py')

with open(TARGET, 'r', encoding='utf-8') as f:
    code = f.read()

# Only replace uncommented lines
old = "fontsize= 15, fontweight='bold'"
new = "fontsize=THEME['SUPTITLE_SIZE'], fontweight=THEME['SUPTITLE_WEIGHT']"

lines = code.split('\n')
count = 0
for i, line in enumerate(lines):
    if old in line and not line.lstrip().startswith('#'):
        lines[i] = line.replace(old, new)
        count += 1

code = '\n'.join(lines)

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"Replaced {count} uncommented 'fontsize= 15' suptitle patterns")
