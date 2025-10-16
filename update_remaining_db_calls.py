"""
Script to update remaining database calls in backend.py
This will replace all remaining sqlite3.connect calls with our database abstraction
"""

import re

def update_remaining_database_calls():
    """Update all remaining database calls in backend.py"""
    
    backend_file = '/Users/dile/labs/nosuvo/backend.py'
    
    # Read the current file
    with open(backend_file, 'r') as f:
        content = f.read()
    
    # Find all remaining sqlite3.connect patterns
    sqlite_patterns = [
        (r'conn = sqlite3\.connect\([^)]+\)', 'with get_db_connection() as conn:'),
        (r'cursor = conn\.cursor\(\)', 'cursor = conn.cursor()'),
        (r'conn\.commit\(\)', 'conn.commit()'),
        (r'conn\.close\(\)', '# conn.close() - handled by context manager'),
    ]
    
    # Apply replacements
    for pattern, replacement in sqlite_patterns:
        content = re.sub(pattern, replacement, content)
    
    # Update specific patterns that need special handling
    content = update_specific_patterns(content)
    
    # Write the updated content
    with open(backend_file, 'w') as f:
        f.write(content)
    
    print("✅ Updated remaining database calls in backend.py")

def update_specific_patterns(content):
    """Update specific patterns that need special handling"""
    
    # Update cursor.execute patterns to use execute_query
    # This is a complex pattern, so we'll do it manually for key functions
    
    # Pattern for simple SELECT queries
    select_pattern = r'cursor\.execute\(([^)]+)\)\s*cursor\.fetchone\(\)'
    
    def replace_select(match):
        query = match.group(1)
        return f"execute_query({query}, fetch=True)"
    
    content = re.sub(select_pattern, replace_select, content)
    
    # Pattern for simple INSERT/UPDATE/DELETE queries
    modify_pattern = r'cursor\.execute\(([^)]+)\)\s*conn\.commit\(\)'
    
    def replace_modify(match):
        query = match.group(1)
        return f"execute_query({query})"
    
    content = re.sub(modify_pattern, replace_modify, content)
    
    return content

if __name__ == "__main__":
    update_remaining_database_calls()
