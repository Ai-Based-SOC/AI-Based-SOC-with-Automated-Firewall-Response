import os

src = r'C:\Users\abhishek\Downloads\ai-based soc\frontend\src'
print('=== COMPREHENSIVE RUNTIME AUDIT ===')
print()

with open(os.path.join(src, 'pages', 'DashboardPage.jsx'), 'r', errors='replace') as f:
    content = f.read()

print('=== ALL 6 CRITICAL FIXES VERIFICATION ===')
print()

fixes = {
    'Fix 1: risk_score Number() normalization': 'const risk = Number(attack.risk_score) || 0' in content,
    'Fix 2: ipData const declaration': 'const ipData = {}' in content,
    'Fix 3: useMemo [attacks] dependency': '[attacks]);' in content,
    'Fix 4: severityData percentage reference': 'severityData[severity]?.percentage' in content,
    'Fix 5: Circle -> circle SVG fix': ('<circle' in content and '<Circle' not in content),
    'Fix 6: data outside map scope (line 745)': ('{count} events' in content and '{data?.count ?? 0' not in content),
}

for fix, status in fixes.items():
    print(f'  {"✓" if status else "✗"} {fix}')

print()
all_fixed = all(fixes.values())
print(f'Overall: {"ALL FIXES APPLIED ✓" if all_fixed else "SOME FIXES MISSING"}')