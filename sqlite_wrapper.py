import sqlite3
import time
import sys
import re
import os

class SQLiteWrapper():
    def __init__(self, db_name=None):
        self.db_name = db_name
        self.connection = None
        self.cursor = None

    def get_max_index(self, table_name):
        query = f"SELECT MAX(id) FROM {table_name};"
        max_value = self.fetch_one(query)
        if not len(max_value):
            return None;
        return max_value[0]

    def get_primary_key(self, table_name, column_name, value):
        query = f"SELECT id FROM ? WHERE ? IS ?"
        parameters = (table_name, column_name, value)
        print(parameters)
        result = self.fetch_one(query, parameters)
        return result[0]


    def value_exists(self, table_name, column_name, value):
        query = f'SELECT 1 FROM {table_name} WHERE {column_name} = "{value}";'
        result = self.fetch_one(query)
        return result is not None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print("ERROR",f"Error connecting to SQLite database:{self.db_name}\n{e}")

    def execute_query(self, query, parameters=()):
        try:
            self.cursor.execute(query, parameters)
            self.connection.commit()
        except sqlite3.Error as e:
            print("ERROR",f"Error executing query{query}:{str(e)}")

    def execute_many(self, query, parameters_list):
        try:
            self.cursor.executemany(query, parameters_list)
            self.connection.commit()
        except sqlite3.Error as e:
            print("ERROR",f"Error executing query{query}:{str(e)}")
            self.connection.rollback()  # Rollback changes in case of error


    def fetch_all(self, query, parameters=()):
        start = time.time()
        try:
            self.cursor.execute(query, parameters)
            rows = self.cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            print("ERROR",f"Error fetching data:{str(e)}")
            return None

    def fetch_one(self, query, parameters=()):
        try:
            self.cursor.execute(query, parameters)
            row = self.cursor.fetchone()
            return row
        except sqlite3.Error as e:
            print("ERROR",f"Error fetching data:{str(e)}")
            return None

    def clear_table(self, table_name):
        delete_query = f"DELETE FROM {table_name}"
        reset_query = f"DELETE FROM sqlite_sequence WHERE name IS '{table_name}'"
        try:
            self.cursor.execute(delete_query)
            self.connection.commit()
            self.cursor.execute(reset_query)
            self.connection.commit()
            print("INFO", f"{table_name} cleared")
        except sqlite3.Error as e:
            print("ERROR",f"Error clearing_table:{str(e)}")

    def close(self):
        if self.connection:
            self.connection.close()
            print("INFO","Connection to SQLite database closed")


