"""
This file is the one place in the app that talks to the MySQL database.
Every other file that needs to read or write data goes through this
class instead of connecting to MySQL by itself.
"""

import mysql.connector
from mysql.connector import Error as MySQLError
from config.settings import DB_CONFIG
from utils.exceptions import DatabaseConnectionError


class DBConnector:
    """Small wrapper around a MySQL connection.

    Use it like this:

        with DBConnector() as db:
            db.execute("SELECT * FROM appointments")
            rows = db.fetchall()

    If include_database is False, it connects to the MySQL server only,
    without picking a specific database. This is used the very first
    time, before the appointmed_db database even exists yet.
    """

    def __init__(self, include_database=True):
        self.include_database = include_database
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            config = dict(DB_CONFIG)
            if self.include_database == False:
                config.pop("database", None)
            self.connection = mysql.connector.connect(**config)
            self.cursor = self.connection.cursor(dictionary=True)
        except MySQLError as e:
            raise DatabaseConnectionError("Could not connect to database: " + str(e))

    def execute(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            query_start = query.strip().lower()
            if query_start.startswith("insert") or query_start.startswith("update") or query_start.startswith("delete"):
                self.connection.commit()
        except MySQLError as e:
            raise DatabaseConnectionError("Query failed: " + str(e))

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
