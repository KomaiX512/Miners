#!/usr/bin/env python3
print("Fixing field name mismatch in main.py and indentation in vector_database.py...")

# Fix main.py - change "strategies" to "recommended_counter_strategies"
import re

# Fix main.py
with open('main.py', 'r') as f:
    content = f.read()

# Replace strategies with recommended_counter_strategies in _extract_detailed_competitor_insights
content = re.sub(r'competitor_insights\["strategies"\]', 'competitor_insights["recommended_counter_strategies"]', content)
content = re.sub(r'if not competitor_insights\["strategies"\]', 'if not competitor_insights["recommended_counter_strategies"]', content)
content = re.sub(r'"strategies": \[f"Positioning', '"recommended_counter_strategies": [f"Positioning', content)

# Fix the _build_competitor_analysis_object method
content = re.sub(r'insights\.get\("strategies"', 'insights.get("recommended_counter_strategies"', content)

with open('main.py', 'w') as f:
    f.write(content)

print("Fixed field name mismatch in main.py")

# Fix vector_database.py - fix indentation in _initialize_collection
with open('vector_database.py', 'r') as f:
    lines = f.readlines()

# Find the problematic section and fix it
fixed_lines = []
in_init_collection = False

for line in lines:
    if 'def _initialize_collection' in line:
        in_init_collection = True
        fixed_lines.append(line)
    elif in_init_collection and 'try:' in line and 'First try to get collection' in line:
        # This is the problematic line
        fixed_lines.append('            try:\n')
        fixed_lines.append('                # First try to get collection if it exists\n')
    elif in_init_collection and line.strip() == 'try:':
        # Skip this line as we've already added it
        pass
    else:
        fixed_lines.append(line)

with open('vector_database.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed indentation in vector_database.py")
print("All fixes complete. Now the competitor analysis module should work properly.")
