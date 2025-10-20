#!/usr/bin/env python3
"""
Convert SQLite placeholder (?) to PostgreSQL placeholder (%s) in backend.py
"""

import re

# Read the file
with open('backend.py', 'r') as f:
    content = f.read()

# Replace ? with %s in execute_query calls, but only within the SQL strings
# This regex looks for execute_query with single or triple quotes and replaces ? inside them

def replace_placeholders(match):
    """Replace ? with %s in SQL query strings"""
    query = match.group(1)
    query = query.replace('?', '%s')
    return f"execute_query('''{query}'''"

def replace_single_quote(match):
    """Replace ? with %s in single-quoted SQL strings"""
    query = match.group(1)
    query = query.replace('?', '%s')
    return f"execute_query('{query}'"

# Handle triple-quoted strings
content = re.sub(
    r"execute_query\('''([^']+?)'''",
    replace_placeholders,
    content,
    flags=re.DOTALL
)

# Handle single-quoted strings
content = re.sub(
    r"execute_query\('([^']+?)'",
    replace_single_quote,
    content
)

# Write back
with open('backend.py', 'w') as f:
    f.write(content)

print("✅ Converted SQL placeholders from ? to %s")

