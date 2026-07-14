import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Running on Render
    conn = psycopg2.connect(DATABASE_URL)
else:
    # Running locally
    conn = psycopg2.connect(
        host="localhost",
        database="kmipps",
        user="postgres",
        password="1qaZ2ws$",
        port="5432"
    )

cursor = conn.cursor()

print("Database Connected Successfully!")