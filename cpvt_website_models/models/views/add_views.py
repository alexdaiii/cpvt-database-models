import time

import sqlparse
import psycopg


def get_sql_files():
    """
    Sql files should be located in the ./sql directory relative to this file
    """
    import os

    sql_files = []

    for root, _, files in os.walk(
            os.path.join(os.path.dirname(__file__), "sql")):
        for file in files:
            if file.endswith(".sql"):
                sql_files.append(os.path.join(root, file))

    return sql_files


def add_views_pg():
    print("Adding views")

    with psycopg.connect("") as conn:
        sql_files = get_sql_files()

        for sql_file in sql_files:
            print(f"Executing {sql_file}")
            execute_file(conn, sql_file)


def execute_file(conn, sql_file):
    # start a timer
    start_time = time.time()

    with conn.cursor():
        with open(sql_file, "r") as f:
            sql = f.read()

            for stmt in sqlparse.split(sql):
                print(f"Executing: \n{stmt}")
                conn.execute(stmt)

        conn.commit()

    # end the timer
    end_time = time.time()

    print(f"Time taken: {end_time - start_time:.2f} seconds")


def main():
    add_views_pg()


if __name__ == "__main__":
    main()

__all__ = ["add_views_pg"]
