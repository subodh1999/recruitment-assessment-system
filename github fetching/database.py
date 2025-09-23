import logging
import psycopg2
from psycopg2 import sql, extras
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_params: dict):
        if not all(db_params.values()):
            raise ValueError("All database parameters are required in the .env file.")
        self.db_params = db_params

    def initialize_tables(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            username VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            profile_url VARCHAR(255),
            followers INTEGER,
            public_repos INTEGER,
            total_stars_received INTEGER,
            total_forks_received INTEGER,
            organizations_count INTEGER,
            account_age_days INTEGER,
            primary_languages TEXT,
            hireable BOOLEAN,
            location VARCHAR(255),
            issues_opened INTEGER,
            issues_closed INTEGER,
            prs_opened INTEGER,
            prs_closed INTEGER,
            prs_merged INTEGER,
            total_contributions INTEGER
        );
        """
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    query_for_github_users = sql.SQL(create_table_query).format(
                        table_name=sql.Identifier("github_users")
                    )
                    cur.execute(query_for_github_users)

                    query_for_unknown_users = sql.SQL(create_table_query).format(
                        table_name=sql.Identifier("unknown_github_users")
                    )
                    cur.execute(query_for_unknown_users)
            logging.info("Database tables 'github_users' and 'unknown_github_users' are ready.")
        except psycopg2.Error as e:
            logging.critical(f"Database initialization failed: {e}")
            raise

    def persist_candidates(self, candidates: List[Dict[str, Any]], table_name: str):
        if not candidates:
            return

        cols = candidates[0].keys()
        insert_query = sql.SQL("""
            INSERT INTO {table} ({columns})
            VALUES %s ON CONFLICT (username) DO NOTHING;
        """).format(
            table=sql.Identifier(table_name),
            columns=sql.SQL(', ').join(map(sql.Identifier, cols))
        )

        values_to_insert = [[candidate.get(col) for col in cols] for candidate in candidates]

        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    extras.execute_values(cur, insert_query, values_to_insert)
            logging.info(f"Successfully processed {len(candidates)} candidates for table '{table_name}'.")
        except psycopg2.Error as e:
            logging.error(f"Failed to write to table '{table_name}': {e}")

    def truncate_data_table(self, table_name: str):
        try:
            with psycopg2.connect(**self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("TRUNCATE TABLE {table};").format(table=sql.Identifier(table_name)))
                    logging.info(f"Truncated database table: {table_name}")
        except psycopg2.Error as e:
            logging.error(f"Failed to truncate table '{table_name}': {e}")