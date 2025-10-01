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

# Insert an expanded list of sample users
users_data = [
    ('Alice', 'alice@example.com', 'Backend'),      # ID 1
    ('Bob', 'bob@example.com', 'Frontend'),       # ID 2
    ('Charlie', 'charlie@example.com', 'Backend'),      # ID 3
    ('Diana', 'diana@example.com', 'QA'),           # ID 4
    ('Ethan', 'ethan@example.com', 'Frontend'),     # ID 5
    ('Fiona', 'fiona@example.com', 'Design'),       # ID 6
    ('George', 'george@example.com', 'Design'),     # ID 7
    ('Hannah', 'hannah@example.com', 'QA')          # ID 8
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

# Insert an expanded list of sample tasks, assigning to the new user IDs
tasks_data = [
    ('Setup CI/CD pipeline', 'Integrate GitHub Actions for automated testing', 'Done', 1),
    ('Design homepage UI', 'Create mockups in Figma for the new homepage', 'In Progress', 6),
    ('Fix login authentication bug', 'Users are unable to log in with valid credentials', 'In Progress', 3),
    ('Write API documentation', 'Document all endpoints for the v2 API', 'Done', 1),
    ('Develop splash screen', 'Implement the new splash screen animation', 'To Do', 5),
    ('Create user personas', 'Define key user archetypes for product development', 'Done', 7),
    ('Perform regression testing', 'Run full regression suite before the v2.1 release', 'To Do', 4),
    ('Refactor database connection module', 'Update the module to use connection pooling', 'To Do', 3),
    ('Test new checkout flow', 'End-to-end testing of the new payment and checkout process', 'In Progress', 8),
    ('Build reusable button component', 'Create a dynamic button component in React', 'Done', 2),
    ('Design mobile app icon', 'Create a new icon for the iOS and Android app', 'To Do', 6),
    ('Migrate user data to new schema', 'Write and test the migration script for user data', 'Blocked', None) # Unassigned task
]

cursor_tasks.executemany("INSERT INTO tasks (title, description, status, assigned_to) VALUES (?, ?, ?, ?)", tasks_data)

conn_tasks.commit()
conn_tasks.close()
print(f"Tasks database created with {len(tasks_data)} tasks.")
print("\nDatabase setup complete!")