import sqlite3
import json
from argparse import ArgumentParser
import os
import re


def parse_arguments():
    parser = ArgumentParser(description="A tool to extract artifacts from a knowledgeC.db file")
    parser.add_argument("-f", "--file", dest="database_path", required=True, help="Path to the knowledgeC.db file")
    parser.add_argument("-o", "--output-dir", dest="output_dir", help="Path to the output directory")
    return parser.parse_args()


def extract_readable_text(input_str):
    # Regular expression to match readable text
    readable_pattern = re.compile(r'[ -~]+')  # Matches ASCII printable characters (space to tilde)

    # Find all matches of readable text
    matches = readable_pattern.findall(input_str)

    # Join the matches into a single string
    readable_text = ' '.join(matches)

    return readable_text


def run_sqlite_query(database_path, output_dir):
    try:
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        # A list of streams to iterate through
        stream_names = [
            "/portrait/topic",
            "/portrait/entity",
            "/notification/usage",
            "/app/intents",
            "/app/mediaUsage",
            "/app/usage",
            "/app/webUsage",
            "/device/isLocked",
            "/discoverability/signals",
            "/display/isBacklit",
            "/event/tombstone"
        ]

        for stream_name in stream_names:
            query = f"""
                SELECT
                    datetime(ZOBJECT.ZCREATIONDATE + 978307200, 'UNIXEPOCH', 'LOCALTIME') as "ENTRY CREATION", 
                    CASE ZOBJECT.ZSTARTDAYOFWEEK 
                        WHEN "1" THEN "Sunday"
                        WHEN "2" THEN "Monday"
                        WHEN "3" THEN "Tuesday"
                        WHEN "4" THEN "Wednesday"
                        WHEN "5" THEN "Thursday"
                        WHEN "6" THEN "Friday"
                        WHEN "7" THEN "Saturday"
                    END as "DAY OF WEEK",
                    datetime(ZOBJECT.ZSTARTDATE + 978307200, 'UNIXEPOCH', 'LOCALTIME') as "START", 
                    datetime(ZOBJECT.ZENDDATE + 978307200, 'UNIXEPOCH', 'LOCALTIME') as "END", 
                    (ZOBJECT.ZENDDATE - ZOBJECT.ZSTARTDATE) as "USAGE IN SECONDS",
                    ZOBJECT.ZSTREAMNAME, 
                    ZOBJECT.ZVALUESTRING,
                    ZSTRUCTUREDMETADATA.Z_DKAPPLICATIONACTIVITYMETADATAKEY__ACTIVITYTYPE AS "ACTIVITY TYPE",  
                    ZSTRUCTUREDMETADATA.Z_DKAPPLICATIONACTIVITYMETADATAKEY__TITLE as "TITLE", 
                    ZSTRUCTUREDMETADATA.Z_DKAPPLICATIONACTIVITYMETADATAKEY__USERACTIVITYREQUIREDSTRING as "ACTIVITY STRING", 
                    datetime(ZSTRUCTUREDMETADATA.Z_DKAPPLICATIONACTIVITYMETADATAKEY__EXPIRATIONDATE + 978307200, 'UNIXEPOCH', 'LOCALTIME') as "EXPIRATION DATE",
                    ZSTRUCTUREDMETADATA.Z_CDENTITYMETADATAKEY__NAME as "ENTITY NAME",
                    ZSTRUCTUREDMETADATA.Z_DKINTENTMETADATAKEY__INTENTCLASS as "INTENT CLASS", 
                    ZSTRUCTUREDMETADATA.Z_DKINTENTMETADATAKEY__INTENTVERB as "INTENT VERB", 
                    ZSTRUCTUREDMETADATA.Z_DKINTENTMETADATAKEY__SERIALIZEDINTERACTION as "SERIALIZED INTERACTION",
                    ZSTRUCTUREDMETADATA.Z_DKDIGITALHEALTHMETADATAKEY__WEBPAGEURL as "WEB URL",
                    ZSOURCE.ZBUNDLEID,
                    ZSOURCE.ZGROUPID,
                    ZSOURCE.ZITEMID
                FROM ZOBJECT
                LEFT JOIN ZSTRUCTUREDMETADATA on ZOBJECT.ZSTRUCTUREDMETADATA = ZSTRUCTUREDMETADATA.Z_PK
                LEFT JOIN ZSOURCE on ZOBJECT.ZSOURCE = ZSOURCE.Z_PK 
                WHERE ZSTREAMNAME = ?
                ORDER BY "START"
            """

            cursor.execute(query, (stream_name,))

            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]

            result_list = []
            for row in rows:
                result_dict = {}
                has_null = False
                for i in range(len(columns)):
                    value = row[i]
                    if value is None:
                        has_null = True
                        continue
                    # This will extract any blob values decode them and extract the strings
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='replace')
                    if isinstance(value, str):
                        value = extract_readable_text(value)
                    result_dict[columns[i]] = value
                result_list.append(result_dict)

            output_file = f"output_{stream_name.replace('/', '_').replace(' ', '_').lower()}.json"
            if output_dir:
                output_file = os.path.join(output_dir, output_file)

            # Dump the list into a JSON file
            with open(output_file, "w") as json_file:
                json.dump(result_list, json_file, indent=4)

            print(f"Query results for stream '{stream_name}' have been saved to:", output_file)

    except sqlite3.Error as e:
        print("SQLite error:", e)
    except Exception as e:
        print("General error:", e)
    finally:
        if connection:
            connection.close()


# Main function
def main():
    args = parse_arguments()

    run_sqlite_query(args.database_path, args.output_dir)


if __name__ == "__main__":
    main()
