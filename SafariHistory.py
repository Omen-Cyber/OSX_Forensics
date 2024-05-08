import sqlite3
from datetime import datetime

# Ask for the path to the SQLite database file
db_file = input("Enter the path to the SQLite database file: ")

# Connect to the SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Execute the SQL query
cursor.execute("""
    SELECT datetime(v.visit_time + 978307200, 'unixepoch', 'localtime') as date,
           i.domain_expansion, i.url, i.visit_count
    FROM history_items i 
    LEFT JOIN history_visits v ON i.id = v.history_item
    ORDER BY i.id DESC
    LIMIT 100000;
""")

# Fetch all results
results = cursor.fetchall()

# Close the database connection
conn.close()

# Define a function to format each row as desired
def format_row(row):
    formatted_date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    return f"Date:            {formatted_date}\nDomain_expansion: {row[1]}\nURL:             {row[2]}\nVisit_count:     {row[3]}\n\n"

# Print the formatted results
for row in results:
    print(format_row(row))
