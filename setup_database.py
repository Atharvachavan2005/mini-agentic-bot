import sqlite3
import os

# --- PREPARATION ---
# Create the data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

users_db_path = "data/users.db"
tasks_db_path = "data/tasks.db"

# Delete old database files to start fresh
if os.path.exists(users_db_path):
    os.remove(users_db_path)
if os.path.exists(tasks_db_path):
    os.remove(tasks_db_path)

print("Old database files removed. Creating new ones.")


# --- USERS DATABASE ---
conn_users = sqlite3.connect(users_db_path)
cursor_users = conn_users.cursor()

# Create the users table
cursor_users.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    team TEXT COLLATE NOCASE
);
""")

# Insert an expanded list of sample users with Indian names
users_data = [
    ('Priya Sharma', 'priya.sharma@example.com', 'Backend'),      # ID 1
    ('Rohan Mehra', 'rohan.mehra@example.com', 'Frontend'),       # ID 2
    ('Anjali Desai', 'anjali.desai@example.com', 'Backend'),      # ID 3
    ('Vikram Singh', 'vikram.singh@example.com', 'QA'),           # ID 4
    ('Arjun Verma', 'arjun.verma@example.com', 'Mobile'),        # ID 5
    ('Meera Reddy', 'meera.reddy@example.com', 'Frontend'),     # ID 6
    ('Sameer Khan', 'sameer.khan@example.com', 'DevOps')         # ID 7
]

cursor_users.executemany("INSERT OR IGNORE INTO users (name, email, team) VALUES (?, ?, ?)", users_data)

conn_users.commit()
conn_users.close()
print(f"Users database created with {len(users_data)} users.")


# --- TASKS DATABASE ---
conn_tasks = sqlite3.connect(tasks_db_path)
cursor_tasks = conn_tasks.cursor()

# Create the tasks table
cursor_tasks.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'To Do',
    assigned_to INTEGER,
    FOREIGN KEY (assigned_to) REFERENCES users (user_id)
);
""")

# Insert a variety of tasks
tasks_data = [
    ('Deploy authentication service', 'Update the auth microservice to v1.2 on production', 'Done', 1),
    ('Build new settings page UI', 'Use the new design system components in React', 'In Progress', 2),
    ('Fix payment gateway bug', 'Investigate why some UPI transactions are failing', 'Blocked', 3),
    ('Write E2E tests for registration', 'Use Cypress to test the full user sign-up flow', 'To Do', 4),
    ('Implement push notifications for Android', 'Integrate Firebase Cloud Messaging', 'In Progress', 5),
    ('Optimize landing page load time', 'Reduce the Largest Contentful Paint (LCP) to under 2s', 'To Do', 6),
    ('Configure Kubernetes cluster monitoring', 'Set up Prometheus and Grafana for the new cluster', 'Done', 7),
    ('Setup staging environment database', 'Create a read replica of the production DB', 'To Do', 1),
    ('Release iOS app version 2.5 to TestFlight', 'Prepare the build and submit for review', 'To Do', 5),
    ('Audit third-party API usage', 'Check for unused or deprecated API calls', 'To Do', None) # Unassigned task
]

cursor_tasks.executemany("INSERT INTO tasks (title, description, status, assigned_to) VALUES (?, ?, ?, ?)", tasks_data)

conn_tasks.commit()
conn_tasks.close()
print(f"Tasks database created with {len(tasks_data)} tasks.")
print("\nDatabase setup complete!")