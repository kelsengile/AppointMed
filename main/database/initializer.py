"""
This file sets up the database automatically the first time the app
connects, by running database/schema.sql. This means nobody has to open
MySQL Workbench by hand just to create the tables.

How it works, step by step:
  1. MySQL Server must already be installed and running on some
     computer that every device can reach over the network.
  2. This file connects to that server using the host/port/user/password
     from config/settings.py, but WITHOUT picking a database yet,
     since appointmed_db might not exist.
  3. It runs schema.sql, which starts with
     "CREATE DATABASE IF NOT EXISTS appointmed_db;" so the app creates
     its own database, tables, and a default admin account.
  4. After that, every normal connection (through DBConnector) picks
     appointmed_db like usual, since step 3 already created it.
  5. It then runs _migrate_appointments_table(), which patches up
     appointments tables that were created from an OLDER copy of
     schema.sql - see that function's docstring for why this is needed.

Call ensure_database_ready() once near the start of main.py, before the
login window opens.
"""

import os
from database.db_connector import DBConnector
from utils.exceptions import DatabaseConnectionError

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# Columns appointments must have, per schema.sql, mapped to the SQL used
# to add them if they're missing. Order matters: notification_id has no
# dependency on the others, so it's fine anywhere.
APPOINTMENTS_REQUIRED_COLUMNS = {
    "notification_id": "ADD COLUMN notification_id INT NULL",
    "full_name": "ADD COLUMN full_name VARCHAR(100) NOT NULL DEFAULT ''",
    # NOT NULL with no safe default to backfill from, unlike full_name -
    # nullable here is a deliberate compromise so this migration doesn't
    # fail (or delete data) on a table that already has rows.
    "nurse_id": "ADD COLUMN nurse_id INT NULL",
    "room_id": "ADD COLUMN room_id INT NULL",
    "source": "ADD COLUMN source ENUM('Notification', 'Walk-in') NOT NULL DEFAULT 'Walk-in'",
}

# Columns that exist on older tables but were created with a stricter
# constraint than schema.sql now uses. patient_id in particular used to
# be NOT NULL, back when every appointment needed a patient record up
# front. Now a walk-in/new appointee is booked with patient_id=NULL and
# only gets linked to a patient once a doctor examines them - so a table
# still carrying the old NOT NULL constraint makes every new appointment
# fail with "Column 'patient_id' cannot be null" even though the app
# code is correct. This patches the constraint itself, not just
# whether the column exists.
APPOINTMENTS_COLUMNS_TO_RELAX = {
    "patient_id": "MODIFY COLUMN patient_id INT NULL",
}


#   Connects to the MySQL server and runs schema.sql if the database
#    or tables are not there yet. It is safe to call this every time the
#    app starts, because the schema uses "IF NOT EXISTS" everywhere, so
#    running it again on an already set up database just does nothing.

def ensure_database_ready():
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError("schema.sql not found at " + SCHEMA_PATH)

    schema_file = open(SCHEMA_PATH, "r")
    schema_sql = schema_file.read()
    schema_file.close()

# Break the file into separate statements, since the mysql-connector
# library we're using can only run one SQL statement at a time.

    raw_statements = schema_sql.split(";")
    statements = []

    for statement in raw_statements:
        statement = statement.strip()
        if statement != "":
            statements.append(statement)

    try:
        with DBConnector(include_database=False) as db:
            for statement in statements:
                db.execute(statement)
        _migrate_appointments_table()
    except DatabaseConnectionError as e:
        raise DatabaseConnectionError(
            "Could not set up the database automatically. Make sure MySQL "
            "Server is installed and running, and that config/settings.py "
            "has the correct host/user/password. Original error: " + str(e)
        )


def _migrate_appointments_table():
    """CREATE TABLE IF NOT EXISTS only creates a table the very first
    time - it does nothing if the table already exists, even if
    schema.sql has since gained new columns. Anyone who set up their
    database before notification_id/full_name/nurse_id/room_id/source
    were added to the appointments table is stuck with the old, narrower
    table forever unless something patches it up. That's what this does:
    it looks at what columns the live table actually has and ALTERs in
    whichever of APPOINTMENTS_REQUIRED_COLUMNS are missing, so booking an
    appointment doesn't fail with "Unknown column ... in 'field list'".
    """
    with DBConnector() as db:
        db.execute(
            "SELECT COLUMN_NAME, IS_NULLABLE FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'appointments'"
        )
        column_rows = db.fetchall()
        existing_columns = {row["COLUMN_NAME"] for row in column_rows}
        nullability = {row["COLUMN_NAME"]: row["IS_NULLABLE"] for row in column_rows}

        for column_name, add_clause in APPOINTMENTS_REQUIRED_COLUMNS.items():
            if column_name not in existing_columns:
                db.execute("ALTER TABLE appointments " + add_clause)

        # Only issue the MODIFY for columns that actually still have the
        # old, stricter constraint - if it's already nullable this is a
        # harmless no-op we can skip.
        for column_name, modify_clause in APPOINTMENTS_COLUMNS_TO_RELAX.items():
            if column_name in existing_columns and nullability.get(column_name) == "NO":
                db.execute("ALTER TABLE appointments " + modify_clause)

