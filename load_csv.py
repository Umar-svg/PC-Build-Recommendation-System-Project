# load_csv.py — Load the 5 CSV files into MySQL
# Run this once after running generate.py and truncating the tables.

import csv
import os
import mysql.connector
from config import Config

# CSVs live in a folder called csv_data/ next to this script.
# If your CSVs are somewhere else, change this path.
CSV_DIR = os.path.join(os.path.dirname(__file__), "csv_data")

if not os.path.exists(CSV_DIR):
    print(f"❌ CSV folder not found: {CSV_DIR}")
    print("Create a 'csv_data' folder next to this script and put the 5 CSV files in it.")
    exit(1)

conn = mysql.connector.connect(
    host=Config.MYSQL_HOST,
    user=Config.MYSQL_USER,
    password=Config.MYSQL_PASSWORD,
    database=Config.MYSQL_DB,
    port=Config.MYSQL_PORT,
)
cur = conn.cursor()


def load(table, filename, columns):
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        print(f"❌ Missing file: {path}")
        return
    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [tuple(row[c] for c in columns) for row in reader]
    cur.executemany(sql, rows)
    conn.commit()
    print(f"✅ {table}: {len(rows)} rows loaded")


# Load in FK-safe order: parents before children
print("Loading data into MySQL...\n")

load("User", "User.csv",
     ["user_id", "full_name", "email", "password", "role"])

load("Component", "Component.csv",
     ["component_id", "component_name", "component_type", "brand",
      "price", "specifications", "compatibility_info"])

load("Build_Request", "Build_Request.csv",
     ["request_id", "budget", "purpose", "request_date", "user_id"])

load("Recommended_Build", "Recommended_Build.csv",
     ["build_id", "total_cost", "recommendation_date", "request_id"])

load("Build_Component", "Build_Component.csv",
     ["build_component_id", "quantity", "build_id", "component_id"])

cur.close()
conn.close()
print("\n🎉 All CSVs loaded successfully")
