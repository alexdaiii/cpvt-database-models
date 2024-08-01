from contextlib import contextmanager

import age
import psycopg2

from app.settings import get_settings


def setup_apache_age():
    conn = psycopg2.connect(
        host=get_settings().postgresql_host,
        port=get_settings().postgresql_port,
        user=get_settings().postgresql_username,
        password=get_settings().postgresql_password,
        database=get_settings().postgresql_database,
    )
    print(
        f"Creating a graph, {get_settings().graph_database} to store the"
        f" projected sequence variants graph."
    )
    age.setUpAge(conn, get_settings().graph_database)

    return conn


def reset_graph_database():
    conn = setup_apache_age()

    print(f"DROPPING GRAPH TABLES")

    age.deleteGraph(conn, get_settings().graph_database)
    conn.close()

    return setup_apache_age()


@contextmanager
def age_session(conn):
    with conn.cursor() as session:
        try:
            yield session
            # When data inserted or updated, You must commit.
            conn.commit()
        except Exception as ex:
            print(type(ex), ex)
            # if exception occurs, you must rollback all transaction.
            conn.rollback()


__all__ = ["setup_apache_age", "reset_graph_database", "age_session"]
