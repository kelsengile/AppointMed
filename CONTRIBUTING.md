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

Set aside about 30 minutes the first time. Do the steps in order, and use the **Verify** line at the end of each step before moving on. If something fails, check [Troubleshooting](#troubleshooting).

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
- **Windows, MySQL:** if `mysql --version` says the command is not recognized, add the MySQL `bin` folder to your PATH (usually `C:\Program Files\MySQL\MySQL Server 8.0\bin`), then open a new terminal.
- **Windows, terminals:** commands below work in Git Bash, PowerShell, and Command Prompt unless a step says otherwise.
- Write down the MySQL `root` password you chose during installation. You need it in Steps 4 and 5.
- A code editor such as [VS Code](https://code.visualstudio.com/) is recommended.

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

Tell Git who you are, so your commits are credited to you (skip if already set):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**Verify:** `git status` prints `On branch main` and `nothing to commit, working tree clean`.

### Step 2: Install backend dependencies

A virtual environment keeps this project's Python packages separate from the rest of your computer. From the project root:

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

> **PowerShell says "running scripts is disabled"?** Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try activating again. Or use Command Prompt instead.

To leave the virtual environment later, type `deactivate`.

### Step 3: Install frontend dependencies

From the project root:

```bash
cd source/frontend
npm install
```

This creates a `node_modules` folder. It is large and is gitignored, so never commit it.

**Verify:** the command ends without `npm ERR!` lines, and `node_modules` exists inside `source/frontend`.

### Step 4: Create the database and the app user

Log in to MySQL as root and enter your root password when asked:

```bash
mysql -u root -p
```

Then run the following. Replace `change_this_password` with a password of your own, and use the same one in Step 6.

```sql
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'appointmed_user'@'localhost' IDENTIFIED BY 'change_this_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

What each line does:

- `CREATE DATABASE` makes an empty database named `appointmed`. `utf8mb4` lets it store any character, including names with accents.
- `CREATE USER` makes a limited account just for the web app.
- `GRANT` lets that account read and write data inside `appointmed` only. It cannot create or drop tables, which is intentional. Only `root` changes the structure.
- `FLUSH PRIVILEGES` applies the change right away.

The web app connects as `appointmed_user`, never as `root`.

**Verify:** log in again with `mysql -u root -p` and run `SHOW DATABASES;`. `appointmed` should be in the list.

### Step 5: Load the schema and sample data

The schema creates the 12 tables. The seed fills them with fictional sample data: staff are SpongeBob SquarePants characters and patients are cartoon characters. Run both from the **project root**, in this order.

**Git Bash, Command Prompt, macOS, or Linux:**

```bash
mysql -u root -p appointmed < source/database/schema.sql
mysql -u root -p appointmed < source/database/seed.sql
```

**PowerShell** does not support the `<` operator. Use one of these instead:

```powershell
cmd /c "mysql -u root -p appointmed < source\database\schema.sql"
cmd /c "mysql -u root -p appointmed < source\database\seed.sql"
```

or, from the project root, open MySQL and use `SOURCE`:

```sql
mysql -u root -p appointmed
SOURCE source/database/schema.sql;
SOURCE source/database/seed.sql;
```

Load `seed.sql` **once**. Running it twice causes `Duplicate entry` errors. To start over, see [Resetting your database](#resetting-your-database).

**Verify:** in the MySQL prompt, run:

```sql
SHOW TABLES;                          -- 12 tables
SELECT username, role FROM users;     -- 5 users
```

The sample staff accounts (all fictional, for development only) are:

| Username | Password | Role | Notes |
|---|---|---|---|
| `admin` | `admin123` | Admin | Eugene H. Krabs |
| `dr.cheeks` | `doctor123` | Doctor | General Medicine, works Monday to Friday |
| `dr.tentacles` | `doctor123` | Doctor | Pediatrics, works Monday, Wednesday, Friday |
| `nurse.spongebob` | `nurse123` | Nurse | Supports `dr.cheeks` |
| `nurse.patrick` | `nurse123` | Nurse | Supports `dr.tentacles` |

These passwords are public. Never use them outside your own computer. Appointment dates in the seed are relative to the day you load it, so "today" always has a live queue to test with. The top of `seed.sql` describes exactly what data it covers.

### Step 6: Configure the environment

Copy `source/.env.example` to `source/.env` and fill in your values. The template looks like this:

```
# AppointMed local configuration. Copy this file to .env (same folder) and change the placeholders.
# .env is gitignored: never commit it.

APP_ENV=development

DB_HOST=localhost
DB_PORT=3306
DB_NAME=appointmed
DB_USER=appointmed_user
DB_PASSWORD=change_this_password

# Signs login tokens. Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=change_this_secret
# Minutes a login stays valid (default 480 = 8 hours)
JWT_EXPIRE_MINUTES=480

# Comma-separated list of origins allowed to call the API from a browser
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# OPTIONAL email. Leave SMTP_HOST empty and emails are written to the backend console instead.
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@appointmed.example
SMTP_TLS=true
```

Set `DB_PASSWORD` to the password from Step 4, and generate your own `JWT_SECRET`. The `.env` file is gitignored. **Never commit it.**

What each setting means:

| Setting | Meaning |
|---|---|
| `APP_ENV` | `development` on your computer. Do not change it unless the team agrees. |
| `DB_HOST`, `DB_PORT` | Where MySQL is running. Leave as is for a local install. |
| `DB_NAME` | The database from Step 4. |
| `DB_USER`, `DB_PASSWORD` | The app account from Step 4, **not** `root`. |
| `JWT_SECRET` | A long random string used to sign login tokens. **Required:** the backend refuses to start without it, and warns if it is still `change_this_secret`. Each developer generates their own. |
| `JWT_EXPIRE_MINUTES` | How long a login stays valid. |
| `CORS_ORIGINS` | Websites allowed to call the API from a browser. Keep it to the two frontend addresses above. |
| `SMTP_*` | Optional email settings. When `SMTP_HOST` is empty, booking confirmation and disapproval emails are written to the backend console instead of being sent. That is enough for development. |

Common mistakes:

- The file must be at `source/.env`, next to `main.py`. Not in `source/frontend` and not at the project root.
- No spaces around `=`, and no quotes around values.
- The file name starts with a dot and has no extension. Make sure your editor did not save it as `.env.txt`.
- Restart the backend after editing `.env`. It is read only at startup.

### Step 7: Run the project

Use two terminals, and leave both running. **Start the backend first**, because the frontend dev server forwards every `/api` request to it.

**Terminal 1: Backend** (from `source`, with `(.venv)` active):

```bash
uvicorn main:app --reload
```

You should see `Uvicorn running on http://127.0.0.1:8000`. With `--reload`, the server restarts by itself when you save a Python file. Run it from the `source` folder, otherwise Python cannot find the `backend` package.

- Status page: http://127.0.0.1:8000
- API docs (interactive): http://127.0.0.1:8000/docs

**Terminal 2: Frontend** (from `source/frontend`):

```bash
npm run dev
```

You should see `Local: http://localhost:5173/`. The page updates in the browser as you save files.

- Web app: http://localhost:5173

Stop either server with `Ctrl + C`.

### Verify the setup

1. Open http://127.0.0.1:8000. The status page should show **API: Online** and **Database: Connected**. Also check http://127.0.0.1:8000/api/health, which should show JSON with `"status":"ok"`.
2. Open http://localhost:5173. You should see the AppointMed landing page. Click **Staff login** and sign in as `nurse.spongebob` / `nurse123`. You should land on the nurse dashboard.

If the database shows **Not connected**, check that MySQL is running and that `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `source/.env` match Step 4.

### Try the main workflow

A quick tour that touches every role and confirms the whole system works:

1. **Book:** open http://localhost:5173/book, choose Dr. Sandy Cheeks, a weekday, and an open time, and submit a request with fictional details.
2. **Approve:** log in as `nurse.spongebob`, open **Notifications**, and approve the request. With no SMTP configured, the confirmation email appears in the backend console.
3. **Check in:** open **Appointments**. Only today's appointments can be checked in, so use today's seeded appointments (or **New appointment** with check-in) to continue.
4. **Examine:** log in as `dr.cheeks`, start an examination for a checked-in patient, add a diagnosis and a prescription, and finish it.
5. **Pay:** open **Invoice** and mark the invoice as paid. The visit moves to **History** and the patient's record.
6. **Administer:** log in as `admin` to see **Users**, **Reports**, and the **Audit Logs** entries your actions created.

### Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `RuntimeError: JWT_SECRET is missing` when the backend starts | `source/.env` is missing, in the wrong folder, or has no `JWT_SECRET` | Create `source/.env` (Step 6), then restart `uvicorn` |
| Status page shows **Database: Not connected** | MySQL is stopped, or the `DB_*` values do not match Step 4 | Start MySQL, check `.env`, restart the backend |
| `Access denied for user 'appointmed_user'` in the backend log | Wrong password in `.env`, or the user was never created | Repeat the `CREATE USER` and `GRANT` lines in Step 4 and match the password |
| `ModuleNotFoundError: No module named 'backend'` | `uvicorn` was started from the wrong folder | `cd source`, then `uvicorn main:app --reload` |
| `ModuleNotFoundError` for `bcrypt`, `jwt`, `fastapi`, and similar | The virtual environment is not active, or packages are not installed | Activate `.venv`, then `pip install -r requirements.txt` |
| The web app says "Cannot reach the server. Check that the backend is running." | The backend is stopped, or not on port 8000 (Vite forwards `/api` to `127.0.0.1:8000`) | Start the backend, then reload the page |
| `Port 5173 is already in use` | Another Vite server is open (the port is fixed on purpose) | Close the other terminal, then run `npm run dev` again |
| `Duplicate entry` while loading `seed.sql` | The seed was already loaded | [Reset your database](#resetting-your-database) |
| "Too many failed attempts" at login | Five wrong passwords for that username within 5 minutes | Wait a few minutes (or restart the backend) and use the sample passwords above |
| The booking page shows no available times | That doctor does not work that weekday (Dr. Tentacles works Monday, Wednesday, Friday only), the times already passed or are taken, the date is outside the booking window, or online booking is switched off in Clinic Settings | Try another date or doctor, or check **Clinic Settings** as `admin` |
| No confirmation email arrives | `SMTP_HOST` is empty, so the email is printed in the backend console | Read the console, or configure SMTP in `.env` |
| `npm run build` fails with TypeScript errors | Strict mode is on, and unused variables and imports count as errors | Fix the lines the compiler reports |
| PowerShell rejects `mysql ... < file.sql` | PowerShell does not support `<` | Use the `cmd /c` or `SOURCE` options in Step 5 |

### Resetting your database

To start over with fresh sample data, log in as root and run:

```sql
DROP DATABASE appointmed;
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
```

Then repeat Step 5. Never run `seed.sql` against a shared or production database.

### Staying up to date

Each time you start working, run `git pull`, then check what changed:

| If this changed | Do this |
|---|---|
| `source/requirements.txt` | `pip install -r requirements.txt` (with `.venv` active) |
| `source/frontend/package.json` or `package-lock.json` | `npm install` in `source/frontend` |
| `source/database/schema.sql` or `seed.sql` | Reset your database (see above) so it matches the team's |
| `source/.env.example` | Add any new variables to your own `source/.env`, then restart the backend |

Then start the backend and the frontend as in Step 7.

---

## Project Structure

```
.
├── .gitignore
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── README.md
├── SECURITY.md
└── source/
    ├── .env                      # local secrets (gitignored)
    ├── .env.example              # template for .env 
    ├── main.py                   # FastAPI entry point: CORS, error handlers, routers, status page
    ├── requirements.txt          # Python dependencies
    ├── assets/                   # fonts, icons, and images
    ├── backend/
    │   ├── core/                 # config.py, database.py, exceptions.py, security.py, mailer.py, utils.py
    │   ├── models/               # domain.py: User/Doctor/Nurse/Admin and AppointmentWorkflow
    │   ├── schemas/              # api.py: Pydantic request bodies
    │   ├── repositories/         # all SQL: base, user, patient, appointment, clinical, system
    │   ├── services/             # business rules: auth, booking, scheduling, appointment,
    │   │                         #   billing, patient, dashboard, admin, waiting_queue
    │   └── routes/               # auth_routes, public_routes, staff_routes, admin_routes
    ├── database/
    │   ├── schema.sql            # tables and constraints
    │   └── seed.sql              # fictional sample data
    ├── documentation/
    │   ├── DOCUMENTATION.md      # technical documentation
    │   ├── diagrams/             # UML class diagrams
    │   ├── flowcharts/
    │   └── screenshots/
    └── frontend/                 # React + TypeScript web app (Vite + Tailwind)
        ├── index.html
        ├── package.json
        ├── vite.config.ts        # dev server on :5173, proxies /api to the backend
        ├── tailwind.config.js
        ├── public/               # appointmed-logo.png, optional hero.jpg
        └── src/
            ├── main.tsx
            ├── app.tsx           # routes, and the map from navigation items to pages
            ├── api/              # client.ts (the only fetch call) and endpoints.ts
            ├── components/       # shared pieces: Badge, Modal, ExamPanel, EncounterCard, ...
            ├── config/           # Navigation.ts: side-panel items per role
            ├── context/          # AuthContext.tsx: signed-in user
            ├── hooks/            # usePolling.ts
            ├── layouts/          # DashboardLayout.tsx: side panel and page frame
            ├── pages/            # LandingPage, BookingPage, plus staff/, admin/, shared/
            ├── types/            # index.ts: types that match the backend JSON
            └── utils/            # format.ts: dates, money, age
```

## Contributing

Thank you for helping build AppointMed. This section explains how we plan work, write and review code, and keep the project consistent. Please also read the [Code of Conduct](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md).

### Before you start

1. **Get the app running.** Finish [Initialization](#initialization) first, so you can test your changes.
2. **Pick or create an issue.** Every change should start from a GitHub issue describing what is needed. Comment on it (or tell the group) that you are taking it, so two people do not do the same work.
3. **Keep the scope small.** One issue, one branch, one pull request. Split big features into pieces a teammate can review in about 15 minutes.
4. **Ask early.** If the requirement is unclear or touches the database design, ask the team before writing a lot of code.

### Branching

`main` always holds working code. Never commit directly to it. Create a branch for each piece of work, named `type/short-description` in lowercase with hyphens:

| Prefix | Use for | Example |
|---|---|---|
| `feature/` | New functionality | `feature/appointment-booking` |
| `fix/` | Bug fixes | `fix/slot-conflict` |
| `docs/` | Documentation, diagrams, screenshots | `docs/uml-diagram` |
| `refactor/` | Restructuring code without changing behavior | `refactor/remove-unused-visit-files` |
| `test/` | Adding or improving tests | `test/booking-validation` |
| `chore/` | Dependencies, config, tooling | `chore/update-dependencies` |

### Step-by-step workflow

```bash
# 1. Start from the latest main
git switch main
git pull

# 2. Create your branch
git switch -c feature/doctor-availability

# 3. Do the work, running the app as you go (see "Testing your changes")

# 4. Review what you changed before committing
git status
git diff

# 5. Stage and commit
git add source/backend/services/scheduling_service.py source/frontend/src/pages/BookingPage.tsx   # add specific files, not everything
git commit -m "Hide fully booked days on the booking page"

# 6. Push your branch and open a pull request on GitHub
git push -u origin feature/doctor-availability
```

Tips:

- Stage specific files instead of `git add .`, so you never commit `.env`, `node_modules`, or stray files by accident. Always read `git status` first.
- Commit often in small steps. It is easier to review and to undo.
- If you are mid-work and need to switch tasks, commit to your branch (or use `git stash`) before switching.

### Keeping your branch up to date

If `main` moves on while you work, bring those changes into your branch before opening or merging your pull request:

```bash
git fetch origin
git merge origin/main
```

If Git reports a **merge conflict**, it marks the clashing lines in the file with `<<<<<<<`, `=======`, and `>>>>>>>`. Edit the file to keep the correct version, remove the markers, then:

```bash
git add <the-fixed-file>
git commit
```

Run the app again afterward to be sure nothing broke. When two people changed the same code in different ways, talk to each other rather than guessing which version wins. `package-lock.json` conflicts are best fixed by running `npm install` again rather than editing by hand.

### Commit messages

Write the subject line as a short command that says what the commit does, in 72 characters or fewer, with no period at the end. Add a blank line and a few sentences of explanation if the *why* is not obvious.

| Good | Not helpful |
|---|---|
| `Add conflict check when booking a slot` | `fixed stuff` |
| `Validate phone number on booking request` | `update` |
| `Fix nurse routing when no doctor is assigned` | `changes to appointment_service.py` |

Each commit should do one thing and leave the app in a working state.

### Opening a pull request

1. Push your branch and click **Compare & pull request** on GitHub, targeting `main`.
2. Give it a clear title, like a commit subject.
3. Fill in the description using this template:

```markdown
## What changed
A short summary of the change and why it is needed.

Closes #<issue-number>

## How to test
1. Steps a reviewer can follow to see it working.
2. Include which user to log in as, if relevant.

## Screenshots
(For visible changes. Fictional data only.)

## Checklist
- [ ] The app runs and the change works as described
- [ ] `npm run build` passes (no TypeScript errors)
- [ ] Input is validated and errors are handled with clear messages
- [ ] New endpoints check the user's role with `require_feature(...)` and stay inside the user's doctor scope
- [ ] SQL is parameterized and lives only in a repository
- [ ] No secrets, `.env` contents, or real personal data included
- [ ] Documentation updated if behavior or the database changed
- [ ] I can explain every part of this code
```

### Reviewing a pull request

- **At least one teammate** must approve before merging. You may not approve your own pull request.
- Aim to review within **2 days**, so nobody is blocked for long.
- Review for: does it do what the issue asks, is it readable, are errors handled, is input validated, is SQL parameterized, are roles and doctor scope checked on the backend, and does it follow these guidelines.
- Comment on the code, not the person. Explain *why* and suggest an alternative. Mark small style points as optional ("nit:").
- Authors respond to every comment, push fixes to the same branch, and ask for another look.
- After approval, the author merges the pull request and deletes the branch.

### Where code belongs

The backend is layered. A request flows downward, and each layer only calls the one below it.

| Layer | Role | Where it lives |
|---|---|---|
| **Routes** | Thin FastAPI endpoints. They declare who may call them with `require_feature("...")`, read a validated request body, call one service method, and return the result. | `source/backend/routes/` |
| **Schemas** | Pydantic request bodies. Every input is validated here before it reaches a service. | `source/backend/schemas/api.py` |
| **Services** | Business rules: booking conflicts, the status workflow, doctor scoping, transactions, audit logging, and emails. | `source/backend/services/` |
| **Repositories** | The only place that contains SQL. Each one extends `BaseRepository` and uses parameterized queries. | `source/backend/repositories/` |
| **Models** | Domain objects: `User` and its role subclasses, and the `AppointmentWorkflow` state machine. | `source/backend/models/domain.py` |
| **Core** | Settings, the database pool and transactions, custom exceptions and their handlers, security (hashing, tokens, rate limiter, permission dependency), the mailer, and small utilities. | `source/backend/core/` |
| **Frontend** | Pages, components, API calls, and shared types. | `source/frontend/src/` |

Rules of thumb:

- A route function should be short. It reads the request, calls a service, and returns the result.
- Only repositories contain SQL. Only services contain business rules. Do not mix them.
- When several changes must succeed together, wrap them in `with self._db.transaction() as tx:` and build repositories from `tx`.
- Clinical data belongs to a doctor. Use `user.scope_doctor_id` and return `NotFoundError` for anything outside it, so a nurse can never reach another doctor's records.
- Record important actions with `AuditRepository.record(...)`. Never put passwords or medical details in it.
- Use `to_money` for prices and totals. Money is a `Decimal`, never a float.
- In the frontend, put pages in `pages/`, reusable pieces in `components/`, all backend calls in `api/endpoints.ts`, and shared types in `types/index.ts`.

### Common tasks

**Add a backend endpoint**

1. Add a request body to `schemas/api.py` if the endpoint receives data.
2. Add the query to the right repository in `repositories/`.
3. Add the rule to a service in `services/` (scope check, transaction, audit entry).
4. Add the route in `routes/` with `Depends(require_feature("..."))`.
5. Try it at http://127.0.0.1:8000/docs with valid, invalid, and empty input.

**Give a role access to something new:** add the feature name to that role's `features` set in `models/domain.py`, then use the same name in `require_feature(...)`.

**Add a frontend page**

1. Create the page in `pages/staff/`, `pages/admin/`, or `pages/shared/`.
2. Add an item to the role's list in `config/Navigation.ts` (the first item must stay the Dashboard).
3. Map its `path` to the component in `pageFor()` in `app.tsx`. Until then, the page shows the placeholder.
4. Add the API call to `api/endpoints.ts` and its types to `types/index.ts`.

**Change the database structure**

1. Edit `source/database/schema.sql` (and `seed.sql` if sample data must change). Do not change tables by hand in MySQL without updating the file.
2. Update the matching repository queries and the types in `types/index.ts`.
3. Mention it clearly in your pull request.
4. After merging, teammates reset their database (see [Staying up to date](#staying-up-to-date)).

### How the course concepts appear in the code

The project counts for three courses, so use these ideas where they fit naturally, and note them in `DOCUMENTATION.md` so they are easy to point to during the presentation.

| Concept | Where it lives in AppointMed |
|---|---|
| **Encapsulation** | `Settings` (a frozen dataclass that reads the environment once), `Database` (hides the connection pool, locking, and error translation), and `User` (private fields exposed through properties) |
| **Abstraction** | `Executor` (an abstract way to run SQL), `BaseRepository` (abstract `table` and `columns`), and `User.scope_doctor_id` |
| **Inheritance** | `Doctor`, `Nurse`, and `Admin` extend `User`. Every repository extends `BaseRepository`. Every business error extends `AppError`. |
| **Polymorphism** | Each role answers `can_access(feature)` and `scope_doctor_id` in its own way. `Database` and `Transaction` are interchangeable `Executor`s, so a repository works inside or outside a transaction. |
| **Constructors and factories** | `User.__init__` rejects a missing username or name. `User.from_row` builds the right subclass. `Settings.from_env` builds the settings. |
| **Custom exceptions** | The `AppError` family: `AppointmentConflictError`, `InvalidScheduleError`, `InvalidStatusError`, `DuplicateEntryError`, `RateLimitError`, `DatabaseUnavailableError`, and others |
| **Data structures and algorithms (ITEC 104)** | `WaitingQueue` (min-heap ordered by check-in time), `RateLimiter` (sliding window over a `deque`), `AppointmentWorkflow` (state machine with a transition table), slot generation and taken-slot sets in `SchedulingService`, and search and sorting in repositories |
| **Information management (ITEC 105)** | 12 normalized tables with primary and foreign keys, `CHECK` constraints, a double-booking guard (a generated `active_slot` column with a unique index), transactions, parameterized queries, aggregate report queries, and an append-only audit log |

### Coding standards

**Python (backend)**

- Follow [PEP 8](https://peps.python.org/pep-0008/): `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants, 4-space indentation.
- Add type hints to function parameters and return values.
- Give every class and public method a short docstring that says what it does.
- Catch specific exceptions (`except MySQLError:`), never a bare `except:`.
- Raise a subclass of `AppError` for business problems. The registered handlers turn it into `{"detail": "<plain message>"}` with the right status code.
- Keep business logic in service classes, not in route functions.
- Read configuration from `settings`. Never hard-code passwords, hosts, or secrets.

**TypeScript and React (frontend)**

- TypeScript strict mode is on, and unused variables and imports fail the build. Avoid `any`; define a type or interface instead.
- Components are function components in `PascalCase`. Variables and functions are `camelCase`.
- Type your props. Keep each component focused on one job.
- Keep all backend calls in `api/endpoints.ts` (which goes through `api/client.ts`) rather than scattering `fetch` calls across components.
- Keep `types/index.ts` in step with the backend JSON. MySQL `DECIMAL` values arrive as text, so convert with `toNumber()` from `utils/format.ts` before doing arithmetic.
- Style with Tailwind utility classes. Handle loading, empty, and error states on every screen that fetches data (the `usePolling` hook helps).
- Check access on the backend. Hiding a button or a page is a convenience, not security.

**SQL and database**

Always use parameterized queries. Never build SQL by joining user input into a string.

```python
# Good: the value is passed separately, so it cannot change the query
self._db.fetch_all("SELECT * FROM patients WHERE full_name LIKE %s", (f"%{term}%",))

# Bad: vulnerable to SQL injection
self._db.fetch_all(f"SELECT * FROM patients WHERE full_name LIKE '%{term}%'")
```

**Errors and validation**

- Validate every input with Pydantic before it reaches a service or the database.
- Raise meaningful custom exceptions for business problems and let the exception handler turn them into clear responses.
- Show users a plain message that says what went wrong and how to fix it. Never expose stack traces, SQL, or password hashes.

```python
class AppointmentConflictError(ConflictError):
    """Raised when a doctor already has an active appointment at the requested time."""
```

**API conventions**

- All endpoints live under `/api`: `/api/auth` (login and profile), `/api/public` (booking page, no login), `/api/staff` (doctors and nurses), and `/api/admin`. Use lowercase plural nouns and exchange JSON.
- Errors always look like `{"detail": "..."}`.
- Use proper status codes: `200` OK, `201` created, `400` or `422` invalid input, `401` not signed in, `403` not allowed, `404` not found, `409` conflict (such as a double booking), `429` too many attempts, `503` database unavailable.

**Comments and naming**

Explain *why*, not *what*. Use descriptive names (`available_slots`, not `x`). Remove dead code and debugging prints before committing.

### Testing your changes

The project does not have automated tests yet, so test by hand, and add automated tests as the backend grows.

- **Backend:** open http://127.0.0.1:8000/docs and try your endpoint with valid input, invalid input, and empty fields. Try it as a role that should be refused, too.
- **Frontend:** use the page as each affected role would. Try the unhappy paths too: empty form, wrong values, backend turned off.
- **Type check:** run `npm run build` in `source/frontend`. It must finish with no errors.
- **Database:** if you touched the schema, reset your database and reload both SQL files from scratch to confirm they run cleanly.
- Record notable test cases in the Testing Results section of `DOCUMENTATION.md`.

### Documentation

The technical documentation is part of the grade in each course, so keep it current as you build.

- Update `source/documentation/DOCUMENTATION.md` when you add or change a feature.
- Save UML diagrams in `diagrams/`, flowcharts in `flowcharts/`, and screenshots in `screenshots/`, all inside `source/documentation/`.
- Use fictional data in every screenshot.
- Update this file or the README if you change how the project is set up or run.

### Reporting bugs and suggesting features

Open a GitHub issue with:

- **Bug:** what you expected, what happened, steps to reproduce, the role you were using, and a screenshot or error text (no secrets).
- **Feature:** the problem it solves, who uses it (patient, nurse, doctor, admin), and a short description of how it should work.

Report security problems privately as described in [SECURITY.md](SECURITY.md), never in a public issue.

### Data and secrets

- Use only fictional or anonymized data in code, screenshots, and demos.
- Never commit `.env`, database dumps with real data, or credentials.
- **If you commit a secret by mistake,** tell the team right away and change that secret (new database password, new `JWT_SECRET`). Deleting the file in a later commit is not enough because it stays in Git history.
- Read [SECURITY.md](SECURITY.md) before touching authentication, roles, or public booking endpoints.

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

*Last Updated: October 2026*