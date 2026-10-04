import os
filepath = os.path.join('C:\\Users\\abhishek\\Downloads\\ai-based soc', 'PHASE_0_AUDIT_AND_PLAN.md')
with open(filepath, 'r') as f:
    content = f.read()
    print(content)
    f.close()