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

# Helper functions
def random_string(length=8):
    letters = "abcdefghijklmnopqrstuvwxyz"
    return ''.join(random.choice(letters) for _ in range(length))

def random_status():
    return random.choice(["lost", "found"])

# Step 1: Populate posts table
post_ids = []
for _ in range(10):  # insert 10 posts
    user_id = random_string()
    status = random_status()
    description = random_string(20)
    cursor.execute(
        """
        INSERT INTO posts (user_id, status, description, inserted_at, updated_at)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
        """,
        (user_id, status, description, datetime.utcnow(), datetime.utcnow())
    )
    post_id = cursor.fetchone()[0]
    post_ids.append(post_id)

# Step 2: Populate comments table
for _ in range(20):  # insert 20 comments
    user_id = random_string()
    content = random_string(30)
    post_id = random.choice(post_ids)
    cursor.execute(
        """
        INSERT INTO comments (user_id, content, post_id, inserted_at, updated_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, content, post_id, datetime.utcnow(), datetime.utcnow())
    )

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()

print("Posts and comments populated successfully!")
