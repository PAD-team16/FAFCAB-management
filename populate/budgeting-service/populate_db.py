import os
import random
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env
load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST")

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cursor = conn.cursor()

# Helper functions to generate fake data
def random_string(length=8):
    letters = "abcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(letters) for _ in range(length))

def random_amount(min_value=10, max_value=1000):
    return random.randint(min_value, max_value)

# Populate budget table
for _ in range(10):  # insert 10 rows
    entity = random_string()
    affiliation = random_string()
    amount = random_amount()
    created_by = random_string()
    cursor.execute(
        """
        INSERT INTO budget (entity, affiliation, amount, created_by, inserted_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (entity, affiliation, amount, created_by, datetime.utcnow(), datetime.utcnow())
    )

# Populate debts table
for _ in range(10):  # insert 10 rows
    responsable = random_string()
    created_by = random_string()
    amount = random_amount()
    cursor.execute(
        """
        INSERT INTO debts (responsable, created_by, amount, inserted_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (responsable, created_by, amount, datetime.utcnow(), datetime.utcnow())
    )

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()

print("Database populated successfully!")
