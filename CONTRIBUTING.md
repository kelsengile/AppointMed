# CONTRIBUTING GUIDELINES

AppointMed is a web-based clinic appointment and management system built with a Python (FastAPI) backend and a React + TypeScript web frontend. Clinic staff (Doctor, Nurse, and Admin users) work in a browser-based portal, and patients use a public booking page. Everything connects to one MySQL database, so all users work with the same live data. The project was developed as the final requirement for three courses at Laguna State Polytechnic University: CMSC 203 – Object-Oriented Programming, ITEC 104 – Data Structures and Algorithm, and ITEC 105 – Information Management.

The backend is layered (routes, services, repositories, MySQL) and the frontend is a single-page React app that talks to it through `/api`. These guidelines explain how to set the project up locally, where code belongs, and how to contribute changes in a way that keeps the system consistent.

**Course context**

**Courses:** CMSC 203 – Object-Oriented Programming, ITEC 104 – Data Structures and Algorithm, ITEC 105 – Information Management  
**Instructors:** Ms. Roxanne Garbo, Sir Rolan C. Sotomayor, Sir Jencel P. Sofer  
**Academic year:** 2026–2027

**Contents**

- [Initialization](#initialization): get the project running on your computer
- [Project Structure](#project-structure): what lives where
- [Contributing](#contributing): how we work together and write code
- [Final Project Instructions](#final-project-instructions): the CMSC 203 course requirements we are graded against

---

## Initialization

By the end of this section you will have three things running on your computer:

| Part | What it is | Address |
|---|---|---|
| MySQL | The shared database | `localhost:3306` |
| Backend | FastAPI (Python) | http://127.0.0.1:8000 |
| Frontend | React web app (Vite) | http://localhost:5173 |

Set aside about 30 minutes the first time. The quickest way is the [dev console](#quick-start-recommended-the-dev-console) (`python dev.py`), which does the setup for you. If you prefer to do it by hand, follow the steps in order and use the **Verify** line at the end of each step. If something fails, check [Troubleshooting](#troubleshooting).

### Prerequisites

Install these first, then confirm each one from a terminal.

| Tool | Version | Check with | Download |
|---|---|---|---|
| Git | any recent | `git --version` | [git-scm.com](https://git-scm.com/) |
| Python | 3.11 or newer | `python --version` (Windows: `py --version`) | [python.org](https://www.python.org/) |
| Node.js (includes npm) | 20 or newer | `node --version` and `npm --version` | [nodejs.org](https://nodejs.org/) |
| MySQL Server | 8.0 or newer | `mysql --version` | [dev.mysql.com](https://dev.mysql.com/downloads/mysql/) |

Notes:

- **Windows, Python:** tick **Add python.exe to PATH** in the installer.
- **Windows, MySQL:** if `mysql --version` is not recognized, add the MySQL `bin` folder to your PATH (usually `C:\Program Files\MySQL\MySQL Server 8.0\bin`), then open a new terminal.
- Commands below work in Git Bash, PowerShell, and Command Prompt unless a step says otherwise.
- Write down the MySQL `root` password you chose during installation. You need it in Steps 4 and 5.
- A code editor such as [VS Code](https://code.visualstudio.com/) is recommended.

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**Verify:** `git status` prints `On branch main` and `nothing to commit, working tree clean`.

### Quick start (recommended): the dev console

`dev.py` in the project root is a terminal menu that does Steps 2 to 7 for you. It uses only Python's standard library, so it runs before anything else is installed. Finish [Prerequisites](#prerequisites) and Step 1, then run this from the project root:

```bash
python dev.py        # Windows: py dev.py
```

Press **f** for **First-time setup**. It asks for three things:

1. **A database password** for the `appointmed_user` account. Press Enter to generate a random one. It is saved in `source/.env`.
2. **Whether to send real emails.** Answer **No** for development. Emails are then printed in the backend terminal.
3. **The MySQL `root` password**, used only to create the database and the app account. It is never saved.

When it finishes, it offers to start the project. If you used the dev console, skip to [Verify the setup](#verify-the-setup). Steps 2 to 7 are the same work done by hand.

| Option | What it does |
|---|---|
| `f` | First-time setup: runs options 1 to 4 in order, then offers to start the project |
| `1` | Checks Python (3.11+), Git, Node.js (20+), npm, and the MySQL client |
| `2` | Creates `source/.venv`, runs `pip install -r requirements.txt` and `npm install` |
| `3` | Creates `source/.env` from `.env.example` with your database password and a fresh random `JWT_SECRET` |
| `4` | Creates the database and app account, then loads `schema.sql` and `seed.sql` (only if the database is empty) |
| `5` | Reset database: drops and rebuilds it with `schema.sql` and `seed.sql` (you must type `RESET`) |
| `6`, `7` | Start the backend or the frontend in a new terminal window that stays open |
| `8` | Starts both, runs a health check, and opens the web app in your browser |
| `9` | Health check: API, database, and frontend status |
| `10` | Opens the web app, the status page, or the API docs in your browser |
| `11` | Runs `npm run build` (the TypeScript check required before a pull request) |
| `12` | Update from GitHub: `git pull`, reinstalls both sets of packages, and warns when the SQL files changed |

The top of the menu shows a live checklist (virtual environment, packages, `.env`, backend, database, frontend). Each option also works as a command:

```bash
python dev.py start       # backend + frontend in new windows, then the browser
python dev.py install     # reinstall dependencies
python dev.py reset-db    # fresh database
```

Other commands: `setup`, `check`, `env`, `db`, `backend`, `frontend`, `health`, `open`, `build`, `sync`. To stop the servers, close their terminal windows or press `Ctrl + C` in them.

### Step 2: Install backend dependencies

From the project root:

```bash
cd source
python -m venv .venv
```

Activate it. You must do this in every new terminal you use for the backend.

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (Command Prompt)
.venv\Scripts\activate.bat
# Windows (Git Bash)
source .venv/Scripts/activate
# macOS / Linux
source .venv/bin/activate
```

Then install the packages:

```bash
pip install -r requirements.txt
```

**Verify:** your prompt starts with `(.venv)`, and `pip list` shows `fastapi`, `uvicorn`, `pydantic`, `mysql-connector-python`, `python-dotenv`, `bcrypt`, and `PyJWT`.

> **PowerShell says "running scripts is disabled"?** Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt.

### Step 3: Install frontend dependencies

```bash
cd source/frontend
npm install
```

**Verify:** no `npm ERR!` lines, and `node_modules` exists inside `source/frontend` (it is gitignored: never commit it).

### Step 4: Create the database and the app user

```bash
mysql -u root -p
```

```sql
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'appointmed_user'@'localhost' IDENTIFIED BY 'change_this_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Replace `change_this_password` with a password of your own, and use the same one in Step 6. The app account can read and write data but cannot create or drop tables. Only `root` changes the structure. The web app connects as `appointmed_user`, never as `root`.

**Verify:** `mysql -u root -p`, then `SHOW DATABASES;` lists `appointmed`.

### Step 5: Load the schema and sample data

`schema.sql` creates all 15 tables (it starts with `USE appointmed;`, so create the database in Step 4 first). `seed.sql` fills them with fictional sample data: staff are SpongeBob SquarePants characters and patients are cartoon characters, including nine departments. Run both from the **project root**, in this order.

**Git Bash, Command Prompt, macOS, or Linux:**

```bash
mysql -u root -p appointmed < source/database/schema.sql
mysql -u root -p appointmed < source/database/seed.sql
```

**PowerShell** does not support `<`. Use:

```powershell
cmd /c "mysql -u root -p appointmed < source\database\schema.sql"
cmd /c "mysql -u root -p appointmed < source\database\seed.sql"
```

Load `seed.sql` **once**. Running it twice causes `Duplicate entry` errors. `schema.sql` is safe to repeat. To start over, see [Resetting your database](#resetting-your-database).

**Verify:**

```sql
SHOW TABLES;                          -- 15 tables
SELECT username, role FROM users;     -- 10 users
```

The sample staff accounts (all fictional, for development only):

| Username | Password | Role | Notes |
|---|---|---|---|
| `admin` | `admin123` | Admin | Eugene H. Krabs |
| `dr.cheeks` | `doctor123` | Doctor | General Medicine, Monday to Friday |
| `dr.tentacles` | `doctor123` | Doctor | Pediatrics, Monday, Wednesday, Friday (one sample day off, 10 days ahead) |
| `dr.pearl` | `doctor123` | Doctor | Ophthalmology, Tuesday and Thursday |
| `dr.squarepants` | `doctor123` | Doctor | Orthopedics, Monday to Thursday |
| `dr.patrick` | `doctor123` | Doctor | Neurology, Tuesday, Thursday, Saturday |
| `nurse.dora` | `nurse123` | Nurse | Supports `dr.cheeks` |
| `nurse.blossom` | `nurse123` | Nurse | Supports `dr.cheeks` |
| `nurse.bubbles` | `nurse123` | Nurse | Supports `dr.tentacles` |
| `nurse.buttercup` | `nurse123` | Nurse | Supports `dr.pearl` |

These passwords are public. Never use them outside your own computer. They still work for login, but any **new** password you set (change password, reset password, new user) must be at least 8 characters with an uppercase letter, a lowercase letter, a number, and a special character. Appointment dates in the seed are relative to the day you load it, so "today" always has a live queue to test with.

### Step 6: Configure the environment

Copy `source/.env.example` to `source/.env` and fill in your values:

```
APP_ENV=development

DB_HOST=localhost
DB_PORT=3306
DB_NAME=appointmed
DB_USER=appointmed_user
DB_PASSWORD=change_this_password

# Signs login tokens. Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=change_this_secret
JWT_EXPIRE_MINUTES=480

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# OPTIONAL email. Leave SMTP_HOST empty and emails are written to the backend console instead.
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@appointmed.example
SMTP_TLS=true
```

| Setting | Meaning |
|---|---|
| `APP_ENV` | `development` on your computer. |
| `DB_HOST`, `DB_PORT`, `DB_NAME` | Where MySQL is and the database from Step 4. |
| `DB_USER`, `DB_PASSWORD` | The app account from Step 4, **not** `root`. |
| `JWT_SECRET` | A long random string that signs login tokens. **Required:** the backend refuses to start without it. Each developer generates their own. |
| `JWT_EXPIRE_MINUTES` | How long a login stays valid. |
| `CORS_ORIGINS` | Websites allowed to call the API from a browser. Keep the two frontend addresses. |
| `SMTP_*` | Optional email. When `SMTP_HOST` is empty, emails are printed in the backend console. |

Common mistakes:

- The file must be at `source/.env`, next to `main.py`.
- No spaces around `=`, and no quotes around values.
- The name starts with a dot and has no extension (not `.env.txt`).
- Restart the backend after editing `.env`. It is read only at startup.
- **Never commit `.env`.**

### Step 7: Run the project

> **Shortcut:** `python dev.py start` (option **8**) opens both windows, waits for them, and opens the browser.

**Terminal 1: Backend** (from `source`, with `(.venv)` active):

```bash
uvicorn main:app --reload
```

Run it from the `source` folder, otherwise Python cannot find the `backend` package. Status page: http://127.0.0.1:8000. API docs: http://127.0.0.1:8000/docs.

**Terminal 2: Frontend** (from `source/frontend`):

```bash
npm run dev
```

Web app: http://localhost:5173. Stop either server with `Ctrl + C`.

### Verify the setup

1. Open http://127.0.0.1:8000. The status page shows **API: Online** and **Database: Connected**. http://127.0.0.1:8000/api/health returns `"status":"ok"`.
2. Open http://localhost:5173. You see the AppointMed landing page with the staff list. Click **Staff login** and sign in as `nurse.dora` / `nurse123`. You land on the nurse dashboard.

### Try the main workflow

1. **Book:** open http://localhost:5173/book, choose a doctor, a date on the calendar, and an open time, and submit a request with fictional details.
2. **Approve:** log in as `nurse.dora`, open **Notifications**, and approve the request. With no SMTP configured, the confirmation email appears in the backend console.
3. **Check in:** open **Appointments**. Only today's appointments can be checked in, and **a room must be chosen first** (use the room dropdown on the card, then **Check in**).
4. **Examine:** log in as `dr.cheeks`, start an examination for a checked-in patient, add a diagnosis and a prescription, and finish it.
5. **Pay:** open **Invoice** and mark the invoice as paid. The visit moves to **History** and the patient's record.
6. **Day off:** as `dr.cheeks`, open the **Agenda for** calendar, press **Manage days off**, and mark a free date unavailable. Open `/book` and see that date turn red for that doctor.
7. **Administer:** log in as `admin` to see **Users**, **Reports**, **Audit Logs**, and the **Database** page (backup, tables, SQL console).

### Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `RuntimeError: JWT_SECRET is missing` | `source/.env` is missing, in the wrong folder, or has no `JWT_SECRET` | Create `source/.env` (Step 6), then restart `uvicorn` |
| Status page shows **Database: Not connected** | MySQL is stopped, or the `DB_*` values do not match Step 4 | Start MySQL, check `.env`, restart the backend |
| `Access denied for user 'appointmed_user'` | Wrong password in `.env`, or the user was never created | Repeat Step 4 and match the password |
| `ModuleNotFoundError: No module named 'backend'` | `uvicorn` was started from the wrong folder | `cd source`, then `uvicorn main:app --reload` |
| `ModuleNotFoundError` for `bcrypt`, `jwt`, `fastapi` | The virtual environment is not active | Activate `.venv`, then `pip install -r requirements.txt` |
| "Cannot reach the server. Check that the backend is running." | The backend is stopped or not on port 8000 | Start the backend, reload the page |
| `Port 5173 is already in use` | Another Vite server is open (the port is fixed on purpose) | Close it, then `npm run dev` |
| `Duplicate entry` while loading `seed.sql` | The seed was already loaded | [Reset your database](#resetting-your-database) |
| `ERROR 1146: Table 'appointmed.departments' doesn't exist` | The database was not reset or its schema is out of date | Load `schema.sql` and `seed.sql` using Step 5 |
| "Too many failed attempts" at login | Five wrong passwords for that username within 5 minutes | Wait a few minutes (or restart the backend) |
| "Choose an exam room before checking the patient in." | Check-in requires a room | Pick a room on the appointment card, then press **Check in** |
| The booking page shows no available times | The doctor does not work that weekday, marked it a day off, the times passed or are taken, the date is outside the window, or online booking is off | Try another date or doctor, or check **Clinic Settings** as `admin` |
| No confirmation email arrives | `SMTP_HOST` is empty, so the email is printed in the backend console | Read the console, or configure SMTP |
| "The password needs ..." when setting a password | New passwords must have 8+ characters, upper and lower case, a number, and a special character | Follow the checklist under the field |
| `npm run build` fails with TypeScript errors | Strict mode is on, and unused variables and imports count as errors | Fix the lines the compiler reports |
| `dev.py` says Python 3.11 or newer is needed | `dev.py` was started with an older Python | Run it with a newer one, for example `py -3.12 dev.py` |
| `dev.py` says `Access denied for user 'root'` | Wrong MySQL root password, or (Linux) root uses socket login | Retype it. On Linux run `sudo mysql` and set one with `ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';` |
| `dev.py` prints "No supported terminal was found" | No desktop terminal, or no desktop session (SSH/WSL) | Open two terminals yourself and run the commands it prints |

### Resetting your database

Run as root:

```sql
DROP DATABASE appointmed;
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
```

Then repeat Step 5, or choose **Reset database** in the dev console (type `RESET` to confirm). The dev console reset loads `schema.sql` and `seed.sql`. Never run `seed.sql` against a shared or production database.

An administrator can also download and import a backup from the **Database** page (see [BACKEND.md](source/backend/BACKEND.md), Section 15).

### Staying up to date

Each time you start working, run `git pull`, then check what changed:

| If this changed | Do this |
|---|---|
| `source/requirements.txt` | `pip install -r requirements.txt` (with `.venv` active) |
| `source/frontend/package.json` or `package-lock.json` | `npm install` in `source/frontend` |
| `schema.sql` or `seed.sql` | Reset your database so it matches the team's |
| `source/.env.example` | Add new variables to your own `source/.env`, then restart the backend |

The dev console's **Update from GitHub** option does the pull and the reinstalls, and warns you when the SQL files changed.

---

## Project Structure

```
.
├── .gitignore
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── DOCUMENTATION.md          # technical documentation for the course
├── README.md
├── SECURITY.md
├── NOTES.md                  # study notes: structures, complexity, OOP, security, privacy
├── dev.py                    # terminal console: install, set up the database, start the project
└── source/
    ├── .env                  # local secrets (gitignored)
    ├── .env.example          # template for .env
    ├── main.py               # FastAPI entry point: CORS, error handlers, routers, status page
    ├── requirements.txt
    ├── assets/               # fonts, icons, and images
    ├── backend/
    │   ├── BACKEND.md
    │   ├── core/             # config, database, exceptions, security, mailer, utils
    │   ├── models/           # domain.py: User/Doctor/Nurse/Admin and AppointmentWorkflow
    │   ├── schemas/          # api.py (request bodies), database.py, site.py
    │   ├── repositories/     # base, user (+schedule, days off), patient, appointment (+notification),
    │   │                     #   clinical, system, department, site, staff_directory, database
    │   ├── services/         # auth, booking, scheduling, appointment, billing, patient, dashboard,
    │   │                     #   admin, department, site_service, staff_directory, database, backup_parser, waiting_queue
    │   └── routes/           # auth, public, staff, admin, database
    ├── database/
    │   ├── DATABASE.md
    │   ├── schema.sql        # all 15 tables and constraints
    │   ├── seed.sql          # fictional sample data
    ├── documentation/        # diagrams/, flowcharts/, screenshots/
    └── frontend/             # React + TypeScript web app (Vite + Tailwind)
        ├── FRONTEND.md
        ├── public/           # logos, hero and service images, doctor art, department icons
        └── src/
            ├── app.tsx       # routes, and the map from navigation items to pages
            ├── api/          # client.ts (the only fetch), endpoints.ts, databaseApi, departmentApi, staffDirectoryApi
            ├── components/   # Badge, Modal, ExamPanel, AgendaCalendar, BookingCalendar, ...
            ├── config/       # Navigation.ts: side-panel items per role
            ├── context/      # AuthContext.tsx
            ├── hooks/        # usePolling.ts
            ├── layouts/      # DashboardLayout.tsx
            ├── pages/        # LandingPage, BookingPage, StaffLoginPage, staff/, admin/, shared/
            ├── types/        # index.ts, database.ts, department.ts, staff.ts
            └── utils/        # format, csv, image, input (character filters), password (rules)
```

## Contributing

Thank you for helping build AppointMed. This section explains how we plan work, write and review code, and keep the project consistent. Please also read the [Code of Conduct](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md), and the study notes in [NOTES.md](NOTES.md).

### Before you start

1. **Get the app running.** Finish [Initialization](#initialization) first.
2. **Pick or create an issue.** Every change should start from a GitHub issue. Comment on it so two people do not do the same work.
3. **Keep the scope small.** One issue, one branch, one pull request that a teammate can review in about 15 minutes.
4. **Ask early.** If the requirement is unclear or touches the database design, ask before writing a lot of code.

### Branching

`main` always holds working code. Never commit directly to it. Name branches `type/short-description`:

| Prefix | Use for | Example |
|---|---|---|
| `feature/` | New functionality | `feature/doctor-days-off` |
| `fix/` | Bug fixes | `fix/slot-conflict` |
| `docs/` | Documentation, diagrams, screenshots | `docs/uml-diagram` |
| `refactor/` | Restructuring without changing behavior | `refactor/slot-queries` |
| `test/` | Adding or improving tests | `test/booking-validation` |
| `chore/` | Dependencies, config, tooling | `chore/update-dependencies` |

### Step-by-step workflow

```bash
git switch main
git pull
git switch -c feature/doctor-availability
# ...do the work, running the app as you go...
git status
git diff
git add source/backend/services/scheduling_service.py source/frontend/src/pages/BookingPage.tsx
git commit -m "Hide fully booked days on the booking page"
git push -u origin feature/doctor-availability
```

- Stage specific files instead of `git add .`, so you never commit `.env`, `node_modules`, or stray files. Read `git status` first.
- Commit often in small steps.

### Keeping your branch up to date

```bash
git fetch origin
git merge origin/main
```

If Git reports a **merge conflict**, edit the file to keep the correct version, remove the `<<<<<<<`, `=======`, `>>>>>>>` markers, then `git add <file>` and `git commit`. Run the app again afterward. For `package-lock.json` conflicts, run `npm install` instead of editing by hand.

### Commit messages

Write the subject as a short command in 72 characters or fewer, with no period. Add a blank line and a few sentences if the *why* is not obvious.

| Good | Not helpful |
|---|---|
| `Add conflict check when booking a slot` | `fixed stuff` |
| `Validate phone number on booking request` | `update` |

### Opening a pull request

1. Push your branch and open a pull request targeting `main`, with a clear title.
2. Use this description template:

```markdown
## What changed
A short summary of the change and why it is needed.

Closes #<issue-number>

## How to test
1. Steps a reviewer can follow. Say which user to log in as.

## Screenshots
(For visible changes. Fictional data only.)

## Checklist
- [ ] The app runs and the change works as described
- [ ] `npm run build` passes (no TypeScript errors)
- [ ] Input is validated on the server (Pydantic schema) and errors have clear messages
- [ ] New endpoints use `require_feature(...)` and stay inside the user's doctor scope
- [ ] SQL is parameterized and lives only in a repository
- [ ] No secrets, `.env` contents, or real personal data included
- [ ] Documentation (and NOTES.md, if a concept changed) updated
- [ ] I can explain every part of this code
```

### Reviewing a pull request

- **At least one teammate** must approve before merging. You may not approve your own pull request.
- Aim to review within **2 days**.
- Review for: does it do what the issue asks, is it readable, are errors handled, is input validated on the server, is SQL parameterized, are roles and doctor scope checked on the backend.
- Comment on the code, not the person. Explain *why* and mark small style points as optional ("nit:").
- Authors respond to every comment and push fixes to the same branch. After approval, the author merges and deletes the branch.

### Where code belongs

A request flows downward, and each layer only calls the one below it.

| Layer | Role | Where it lives |
|---|---|---|
| **Routes** | Thin endpoints. Declare who may call with `require_feature("...")`, call one service method, return the result. | `source/backend/routes/` |
| **Schemas** | Pydantic request bodies. Every input is validated here before it reaches a service. | `source/backend/schemas/` |
| **Services** | Business rules: conflicts, the status workflow, doctor scoping, transactions, audit logging, emails. | `source/backend/services/` |
| **Repositories** | The only place with SQL. Each extends `BaseRepository` and uses parameterized queries. | `source/backend/repositories/` |
| **Models** | `User` and its role subclasses, and the `AppointmentWorkflow` state machine. | `source/backend/models/domain.py` |
| **Core** | Settings, database pool and transactions, exceptions, security, mailer, utilities. | `source/backend/core/` |
| **Frontend** | Pages, components, API calls, and shared types. | `source/frontend/src/` |

Rules of thumb:

- A route function is short: read the request, call a service, return the result.
- Only repositories contain SQL. Only services contain business rules.
- When several changes must succeed together, wrap them in `with self._db.transaction() as tx:` and build repositories from `tx`.
- Use `user.scope_doctor_id` and return `NotFoundError` for anything outside it.
- Record important actions with `AuditRepository.record(...)`. Never put passwords or medical details in it.
- Use `to_money` for prices. Money is a `Decimal`, never a float.
- When a doctor-wide rule must not run twice at once (one exam at a time, days off), lock the doctor row with `_lock_doctor` inside the transaction.
- In the frontend, put pages in `pages/`, reusable pieces in `components/`, all backend calls in `api/`, and shared types in `types/`.

### Common tasks

**Add a backend endpoint**

1. Add a request body to `schemas/api.py` if the endpoint receives data (use the shared checks such as `_person_name`, `_no_control`).
2. Add the query to the right repository.
3. Add the rule to a service (scope check, transaction, audit entry).
4. Add the route with `Depends(require_feature("..."))`.
5. Try it at http://127.0.0.1:8000/docs with valid, invalid, and empty input, and as a role that should be refused.

**Give a role access to something new:** add the feature name to that role's `features` set in `models/domain.py`, then use the same name in `require_feature(...)`.

**Add a frontend page**

1. Create the page in `pages/staff/`, `pages/admin/`, or `pages/shared/`.
2. Add an item to the role's list in `config/Navigation.ts` (the first item stays the Dashboard).
3. Map its `path` to the component in `pageFor()` in `app.tsx`.
4. Add the API call and types. Use the character filters in `utils/input.ts` for text fields.

**Change the database structure**

1. Edit `source/database/schema.sql` (and `seed.sql` if sample data changes).
2. Update the matching repository queries and the frontend types.
3. Mention it clearly in your pull request.
4. After merging, teammates reset their database. (If you add a table, check that the Database page backup and import still list it.)

### How the course concepts appear in the code

| Concept | Where it lives in AppointMed |
|---|---|
| **Encapsulation** | `Settings` (frozen dataclass), `Database` (hides the pool, locking, error translation), `User` (private fields behind properties) |
| **Abstraction** | `Executor`, `BaseRepository` (abstract `table` and `columns`), `User.scope_doctor_id` |
| **Inheritance** | `Doctor`, `Nurse`, `Admin` extend `User`. Every repository extends `BaseRepository`. Every business error extends `AppError`. |
| **Polymorphism** | Each role answers `can_access` and `scope_doctor_id` its own way. `Database`, `Transaction`, and `AdminSession` are interchangeable `Executor`s. |
| **Constructors and factories** | `User.__init__` rejects a missing username or name. `User.from_row` and `Settings.from_env` are factories. |
| **Custom exceptions** | The `AppError` family (`AppointmentConflictError`, `InvalidScheduleError`, `InvalidStatusError`, `DuplicateEntryError`, `RateLimitError`, `DatabaseUnavailableError`, and others) |
| **Data structures and algorithms (ITEC 104)** | `WaitingQueue` (min-heap), `RateLimiter` (sliding window over a `deque`), `AppointmentWorkflow` (transition dictionary), slot generation with a taken-time set, sorted overlap detection |
| **Information management (ITEC 105)** | 15 tables, keys, `CHECK` constraints, the `active_slot` double-booking guard, row locks, transactions, parameterized queries, report aggregates, an audit log, backup and restore |

Study notes with code excerpts and complexity analysis are in [NOTES.md](NOTES.md).

### Coding standards

**Python (backend)**

- Follow [PEP 8](https://peps.python.org/pep-0008/): `snake_case` functions and variables, `PascalCase` classes, `UPPER_CASE` constants, 4-space indentation.
- Add type hints and a short docstring to every class and public method.
- Catch specific exceptions, never a bare `except:`.
- Raise a subclass of `AppError` for business problems.
- Keep business logic in services, not in routes.
- Read configuration from `settings`. Never hard-code passwords, hosts, or secrets.

**TypeScript and React (frontend)**

- Strict mode is on, and unused variables and imports fail the build. Avoid `any`.
- Components are `PascalCase` function components. Type your props.
- Keep all backend calls in `api/` (through `api/client.ts`).
- Keep `types/` in step with the backend JSON. MySQL `DECIMAL` arrives as text, so use `toNumber()` before arithmetic.
- Style with Tailwind utility classes and the shared strings in `components/ui.ts`.
- Handle loading, empty, and error states (the `usePolling` hook helps).
- Check access on the backend. Hiding a button is a convenience, not security.

**SQL and database**

Always use parameterized queries:

```python
# Good: the value is passed separately, so it cannot change the query
self._db.fetch_all("SELECT * FROM patients WHERE full_name LIKE %s", (f"%{term}%",))

# Bad: vulnerable to SQL injection
self._db.fetch_all(f"SELECT * FROM patients WHERE full_name LIKE '%{term}%'")
```

**Errors and validation**

- Validate every input with Pydantic before it reaches a service. The frontend repeats the rules for fast feedback, but the server is the authority.
- Raise meaningful custom exceptions and let the handler turn them into clear responses.
- Never expose stack traces, SQL, or password hashes.

**API conventions**

- All endpoints live under `/api`: `/api/auth`, `/api/public` (no login), `/api/staff`, `/api/admin` (including `/api/admin/database`). Use lowercase plural nouns and JSON.
- Errors always look like `{"detail": "..."}`.
- Status codes: `200` OK, `201` created, `400` or `422` invalid input, `401` not signed in, `403` not allowed, `404` not found, `409` conflict, `429` too many attempts, `503` database unavailable.

**Comments and naming**

Explain *why*, not *what*. Use descriptive names. Remove dead code and debugging prints before committing.

### Testing your changes

There are no automated tests yet, so test by hand.

- **Backend:** use http://127.0.0.1:8000/docs with valid, invalid, and empty input, and as a role that should be refused.
- **Frontend:** use the page as each affected role would, including the unhappy paths (empty form, wrong values, backend off).
- **Type check:** `npm run build` in `source/frontend` must finish with no errors.
- **Database:** if you touched the schema, reset your database and reload the SQL files from scratch.
- Record notable cases in the Testing Results section of `DOCUMENTATION.md`.

### Documentation

- Update `DOCUMENTATION.md`, the area documents (`BACKEND.md`, `DATABASE.md`, `FRONTEND.md`), and [NOTES.md](NOTES.md) when you add or change a feature.
- Save UML diagrams in `diagrams/`, flowcharts in `flowcharts/`, and screenshots in `screenshots/` (fictional data only).
- Update this file or the README if you change how the project is set up or run.

### Reporting bugs and suggesting features

Open a GitHub issue with:

- **Bug:** what you expected, what happened, steps to reproduce, the role you were using, and a screenshot or error text (no secrets).
- **Feature:** the problem it solves, who uses it, and how it should work.

Report security problems privately as described in [SECURITY.md](SECURITY.md), never in a public issue.

### Data and secrets

- Use only fictional or anonymized data in code, screenshots, and demos.
- Never commit `.env`, database backups or dumps (they contain password hashes and records), or credentials.
- **If you commit a secret by mistake,** tell the team right away and change that secret. Deleting the file in a later commit is not enough because it stays in Git history.
- Read [SECURITY.md](SECURITY.md) before touching authentication, roles, public endpoints, or the Database page.

### Definition of done

A task is finished when:

- It meets the issue's description and has been run and tested by hand.
- Errors and invalid input are handled with clear messages.
- Code follows the standards above, with no leftover debug code.
- Documentation is updated where needed.
- A teammate reviewed and approved the pull request, and it is merged into `main`.

### Understand what you submit

AI-assisted tools may be used for learning and productivity, but every team member must understand and be able to explain any code they commit. During the final presentation, the instructors may ask any member to walk through any part of the system.

---

## Final Project Instructions

*These are the official CMSC 203 course requirements the project is graded against. Requirements for ITEC 104 and ITEC 105 are not listed here; add them below when they are provided.*

## CMSC 203 – Object-Oriented Programming
### Final Project: Object-Oriented Application Development

**Project Title:** Design and Develop a Real-World Object-Oriented Application

### Project Description

The final project serves as the culminating assessment for CMSC 203 – Object-Oriented Programming. Students will design, develop, test, document, and present a functional desktop application that demonstrates mastery of object-oriented programming concepts learned throughout the course. The project should solve a practical problem using proper software engineering practices and object-oriented design principles.

This project directly measures the attainment of the course intended learning outcomes (CILOs), particularly the students' ability to apply OOP concepts, create maintainable software, utilize design patterns, develop graphical user interfaces, implement exception handling, and produce complete technical documentation.

### Final Project Theme

Develop a **Python GUI-Based Object-Oriented Management System** using Tkinter (or another instructor-approved Python GUI framework). Students may choose one of the following systems:

- Library Management System
- Hotel Reservation System
- Inventory Management System
- **Clinic Appointment System**
- Employee Management System
- Payroll System
- Banking System
- Event Registration System
- Custom Instructor-approved System

### Project Requirements

Your application must include the following:

**1. Object-Oriented Programming (30%)**

The system should demonstrate proper use of:

- Classes and Objects
- Constructors
- Encapsulation
- Inheritance
- Polymorphism
- Abstraction
- Method Overloading (where applicable)
- Interfaces or Abstract Classes (if applicable)

**2. Functional Features (20%)**

The application must include at least:

- User Login (optional but recommended)
- Add Records
- Edit Records
- Delete Records
- Search Records
- Display Records
- Save Data
- Load Data

**3. Graphical User Interface (10%)**

Develop a user-friendly interface that includes:

- Multiple windows/forms
- Buttons
- Labels
- Textboxes
- Combo Boxes
- Menus
- Tables/List Displays
- Appropriate fonts and colors

**4. Exception Handling (10%)**

Your application must properly handle errors such as:

- Invalid input
- Empty fields
- File errors
- Invalid data types
- Custom Exceptions (minimum of one)

**5. Code Quality (10%)**

Your code should demonstrate:

- Proper naming conventions
- Modular programming
- Reusable methods
- Comments where appropriate
- Readability
- Efficient organization using packages/modules

**6. Documentation (10%)**

Submit a technical documentation containing:

- Title Page
- Introduction
- Statement of the Problem
- Objectives
- Scope and Limitations
- System Features
- UML Class Diagram
- Flowchart
- Screenshot of the Application
- Testing Results
- Conclusion
- References

**7. Presentation and Demonstration (10%)**

Each group will deliver a 15–20-minute presentation that includes:

- System overview
- Problem addressed
- OOP concepts applied
- Live demonstration
- Challenges encountered
- Lessons learned
- Question and Answer

### Development Guidelines

- **Programming Language:** Python
- **GUI Framework:** Tkinter (preferred)
- **Team Composition:** 3–5 students per group
- **Version Control:** Git is encouraged.
- **Original Work:** The project must be the students' own work. AI-assisted coding tools may be used ethically for learning and productivity, but students must understand and be able to explain every part of their code.

### Deliverables

Submit the following:

1. Complete Python source code
2. Executable application (if applicable)
3. Technical documentation (PDF)
4. UML Class Diagram
5. Flowchart
6. PowerPoint Presentation
7. Demonstration during Final Examination Week

### Assessment Rubric (100 Points)

| Criteria | Weight |
|---|---|
| Application of OOP Principles | 30 pts |
| Functionality and Completeness | 20 pts |
| GUI Design and User Experience | 10 pts |
| Exception Handling and Program Robustness | 10 pts |
| Code Quality and Organization | 10 pts |
| Documentation | 10 pts |
| Presentation and Demonstration | 10 pts |
| **Total** | **100 pts** |

---

*Last Updated: November 2026*