import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="kmipps",
    user="postgres",
    password="1qaZ2ws$",
    port="5432"
)

cursor = conn.cursor()

print("Database Connected Successfully!")