import re

with open('C:/Users/abhishek/Downloads/ai-based soc/frontend/src/pages/DashboardPage.jsx', 'r') as f:
    content = f.read()

# Fix 1: critical percentage - wrap with Number()
old1 = "percentage: ((counts.critical / total) * 100).toFixed(1),\\n      }"
new1 = "percentage: Number((counts.critical / total) * 100).toFixed(1),\\n      }"
content = content.replace(old1, new1)

# Fix 2: high percentage  
old2 = "percentage: ((counts.high / total) * 100).toFixed(1),\\n      }"
new2 = "percentage: Number((counts.high / total) * 100).toFixed(1),\\n      }"
content = content.replace(old2, new2)

# Fix 3: medium percentage
old3 = "percentage: ((counts.medium / total) * 100).toFixed(1),\\n      }"
new3 = "percentage: Number((counts.medium / total) * 100).toFixed(1),\\n      }"
content = content.replace(old3, new3)

# Fix 4: low percentage
old4 = "percentage: ((counts.low / total) * 100).toFixed(1),\\n      }"
new4 = "percentage: Number((counts.low / total) * 100).toFixed(1),\\n      }"
content = content.replace(old4, new4)

with open('C:/Users/abhishek/Downloads/ai-based soc/frontend/src/pages/DashboardPage.jsx', 'w') as f:
    f.write(content)

print('Fixed 4 toFixed calls')