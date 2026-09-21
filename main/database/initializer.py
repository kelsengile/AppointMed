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
    # Nullable on purpose: a doctor can book an appointment for
    # themselves, in which case no nurse is involved.
    "nurse_id": "ADD COLUMN nurse_id INT NULL",
    "room_id": "ADD COLUMN room_id INT NULL",
    "source": "ADD COLUMN source ENUM('Notification', 'Walk-in') NOT NULL DEFAULT 'Walk-in'",
    # Stamped when a patient is checked in. The dashboards order their
    # waiting queue by it (first in, first served). NULL for anything
    # checked in before this column existed.
    "checked_in_at": "ADD COLUMN checked_in_at DATETIME NULL",
}

# The full list of values appointments.status must accept, per schema.sql.
# 'Consulting' was added after the table first shipped, and CREATE TABLE IF
# NOT EXISTS never revisits a table that already exists - so an older
# database would reject the Consulting button with "Data truncated for
# column 'status'" unless the ENUM itself is widened. See
# _migrate_appointments_table().
APPOINTMENT_STATUS_ENUM = (
    "ENUM('Scheduled', 'Checked-in', 'Consulting', 'Examined', 'Completed', 'Cancelled')"
)

# Columns that exist on older tables but were created with a stricter
# constraint than schema.sql now uses. This patches the constraint itself,
# not just whether the column exists.
#   * patient_id used to be NOT NULL, back when every appointment needed a
#     patient record up front. Now a walk-in/new appointee is booked with
#     patient_id=NULL and only gets linked to a patient once a doctor
#     examines them - so the old NOT NULL made every new appointment fail
#     with "Column 'patient_id' cannot be null".
#   * nurse_id used to be NOT NULL, back when only nurses could book. A
#     doctor can now book an appointment for themselves (nurse_id=NULL),
#     which the old constraint would reject the same way.
APPOINTMENTS_COLUMNS_TO_RELAX = {
    "patient_id": "MODIFY COLUMN patient_id INT NULL",
    "nurse_id": "MODIFY COLUMN nurse_id INT NULL",
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

    statements = _split_statements(schema_sql)

    try:
        with DBConnector(include_database=False) as db:
            for statement in statements:
                db.execute(statement)
            # The schema's last statement seeds the default admin account.
            # Commit explicitly rather than trusting execute() to have
            # spotted it - without this, a fresh install ends up with all
            # the tables but no account to log in with, because the row is
            # thrown away the moment this connection closes.
            db.commit()
        _migrate_appointments_table()
    except DatabaseConnectionError as e:
        raise DatabaseConnectionError(
            "Could not set up the database automatically. Make sure MySQL "
            "Server is installed and running, and that config/settings.py "
            "has the correct host/user/password. Original error: " + str(e)
        )


def _split_statements(schema_sql):
    """schema.sql as a list of single statements, comments removed.

    The mysql-connector library can only run one statement per call, so
    the file has to be split on ";". Dropping the comment lines first
    matters more than it looks: a chunk that still carries its "-- ..."
    banner starts with a comment rather than its own keyword, which
    hides what the statement actually is from anything downstream that
    inspects it.

    This is a deliberately simple splitter - it assumes no ";" or "--"
    ever appears inside a quoted string in schema.sql, which holds for
    this project's schema. (Full-line comments are dropped, so the
    "-- ..." text inside the CREATE TABLE lines is only ever trailing
    text and is passed through to MySQL, which understands it.)"""
    kept_lines = []
    for line in schema_sql.splitlines():
        stripped = line.strip()
        if stripped == "" or stripped.startswith("--") or stripped.startswith("#"):
            continue
        kept_lines.append(line)

    statements = []
    for chunk in "\n".join(kept_lines).split(";"):
        chunk = chunk.strip()
        if chunk != "":
            statements.append(chunk)
    return statements


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

    It also loosens columns that used to be NOT NULL (see
    APPOINTMENTS_COLUMNS_TO_RELAX) and widens the status ENUM.
    """
    with DBConnector() as db:
        db.execute(
            "SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_TYPE FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = 'appointments'"
        )
        column_rows = db.fetchall()
        existing_columns = {row["COLUMN_NAME"] for row in column_rows}
        nullability = {row["COLUMN_NAME"]: row["IS_NULLABLE"] for row in column_rows}
        column_types = {row["COLUMN_NAME"]: row["COLUMN_TYPE"] for row in column_rows}

        for column_name, add_clause in APPOINTMENTS_REQUIRED_COLUMNS.items():
            if column_name not in existing_columns:
                db.execute("ALTER TABLE appointments " + add_clause)

        # Only issue the MODIFY for columns that actually still have the
        # old, stricter constraint - if it's already nullable this is a
        # harmless no-op we can skip.
        for column_name, modify_clause in APPOINTMENTS_COLUMNS_TO_RELAX.items():
            if column_name in existing_columns and nullability.get(column_name) == "NO":
                db.execute("ALTER TABLE appointments " + modify_clause)

        # Widen the status ENUM if it doesn't know 'Consulting' yet. Some
        # connector versions hand COLUMN_TYPE back as bytes, so decode first.
        status_type = column_types.get("status")
        if isinstance(status_type, (bytes, bytearray)):
            status_type = status_type.decode()
        if status_type is not None and "'Consulting'" not in status_type:
            db.execute(
                "ALTER TABLE appointments MODIFY COLUMN status "
                + APPOINTMENT_STATUS_ENUM + " NOT NULL DEFAULT 'Scheduled'"
            )