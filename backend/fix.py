import os

main_py_path = r'C:\Users\abhishek\Downloads\ai-based soc\backend\app\main.py'

with open(main_py_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and replace the DOCS_ENABLED references
new_lines = []
for i, line in enumerate(lines):
    if i < 98:  # Lines 99-101 (0-indexed 98-100)
        # Skip the old DOCS_ENABLED and add new with settings.DOCS_ENABLED
        if 'DOCS_ENABLED' in line and i >= 98:
            # This is one of the three lines we need to replace
            # We'll handle this specially
            new_lines.append(line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Now replace lines 99-101 (0-indexed 98-100) which contain DOCS_ENABLED
# Let's find the exact indices
for i, line in enumerate(new_lines):
    if 'DOCS_ENABLED' in line and i >= 95 and i <= 101:
        # Replace DOCS_ENABLED with settings.DOCS_ENABLED
        new_lines[i] = line.replace('DOCS_ENABLED', 'settings.DOCS_ENABLED')

# Write back
with open(main_py_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done fixing main.py')