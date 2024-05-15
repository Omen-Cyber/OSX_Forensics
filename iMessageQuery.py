import sqlite3
import json
from argparse import ArgumentParser
import os


def parse_arguments():
    parser = ArgumentParser(description="A tool to extract data from the chat.db file")
    parser.add_argument("-f", "--file", dest="database_path", required=True, help="Path to the chat.db file")
    parser.add_argument("-o", "--output", dest="output_dir", help="Path to the output directory")
    return parser.parse_args()


def run_sqlite_query(database_path, output_dir):
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
                c.display_name AS RoomName,
                a.filename AS att_path,
                a.mime_type AS att_mime_type,
                a.transfer_name AS att_name,
                a.total_bytes AS att_size
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
            LEFT JOIN
                message_attachment_join AS ma ON ma.message_id = m.rowid
            LEFT JOIN
                attachment AS a ON a.rowid = ma.attachment_id    
            WHERE
                (h2.service IS NULL OR m.service = h2.service)
            ORDER BY
                2, m.date;
        """

        # Execute the query
        cursor.execute(query)

        # Fetch all rows from the result set
        rows = cursor.fetchall()

        # Construct a list of dictionaries representing each row
        result_list = []
        for row in rows:
            result_dict = {
                "From": row[3],
                "To": row[4],
                "Service": row[5],
                "Date": row[6],
                "Message": row[7],
                "Attachment": {
                    "Path": row[9],
                    "MimeType": row[10],
                    "Name": row[11],
                    "Size": row[12]
                } if row[9] else None
            }
            result_list.append(result_dict)

        # Determine the output file path
        output_file = "output.json"
        if output_dir:
            output_file = output_dir

        # Dump the list into a JSON file
        with open(output_file, "w") as json_file:
            json.dump(result_list, json_file, indent=4)

        print("Query results have been saved to:", output_file)

    except sqlite3.Error as e:
        print("SQLite error:", e)

    finally:
        # Close the database connection
        if connection:
            connection.close()


# Main function
def main():
    # Parse command line arguments
    args = parse_arguments()

    # Run the SQLite query
    run_sqlite_query(args.database_path, args.output_dir)


if __name__ == "__main__":
    main()