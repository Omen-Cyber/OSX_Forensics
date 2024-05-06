import sqlite3

def run_sqlite_query(database_path):
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        # Define the SQL query
        query = """
            SELECT 
                m.rowid,
                COALESCE(m.cache_roomnames, h.id) AS ThreadId,
                m.is_from_me AS IsFromMe,
                CASE WHEN m.is_from_me = 1 THEN m.account ELSE h.id END AS FromPhoneNumber,
                CASE WHEN m.is_from_me = 0 THEN m.account ELSE COALESCE(h2.id, h.id) END AS ToPhoneNumber,
                m.service AS Service,
                DATETIME((m.date / 1000000000) + 978307200, 'unixepoch', 'localtime') AS TextDate,
                m.text AS MessageText,
                c.display_name AS RoomName
            FROM 
                message AS m
            LEFT JOIN 
                handle AS h ON m.handle_id = h.rowid
            LEFT JOIN 
                chat AS c ON m.cache_roomnames = c.room_name
            LEFT JOIN 
                chat_handle_join AS ch ON c.rowid = ch.chat_id
            LEFT JOIN 
                handle AS h2 ON ch.handle_id = h2.rowid
            WHERE
                (h2.service IS NULL OR m.service = h2.service)
            ORDER BY
                2, m.date;
        """

        # Execute the query
        cursor.execute(query)

        # Fetch all rows from the result set
        rows = cursor.fetchall()

        # Print the results with specified format
        for row in rows:
            print("From:     ", row[3])  # From
            print("To:       ", row[4])  # To
            print("Service:  ", row[5])  # Service
            print("Date:     ", row[6])  # TextDate
            print("Message:  ", row[7])  # MessageText
            print()  # Empty line for separation

    except sqlite3.Error as e:
        print("SQLite error:", e)

    finally:
        # Close the database connection
        if connection:
            connection.close()

# Main function
def main():
    # Get user input for the path to the SQLite database file
    database_path = input("Enter the path to the SQLite database file: ")

    # Run the SQLite query
    run_sqlite_query(database_path)

if __name__ == "__main__":
    main()
