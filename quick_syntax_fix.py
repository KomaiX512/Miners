#!/usr/bin/env python3
"""Quick fix for syntax error in main.py"""

with open('main.py', 'r') as f:
    content = f.read()

# Fix the broken newline literal
content = content.replace('lines = text.split("\n")', 'lines = text.split("\\n")')

with open('main.py', 'w') as f:
    f.write(content)

print("✅ Fixed syntax error in main.py") 