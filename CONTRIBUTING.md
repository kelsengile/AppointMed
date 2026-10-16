# CONTRIBUTING GUIDELINES

AppointMed is a clinic appointment and management system built with a Python (FastAPI) backend, an Electron + React + TypeScript desktop application, and a public one-page booking website. All clients connect to one MySQL database so that Doctor, Nurse/Secretary, and Admin users and the patient booking website all work with the same live data. This project was developed as the final requirement for CMSC 203 – Object-Oriented Programming, and follows an MVC-inspired architecture that separates data models, user interface views, and business-logic controllers to keep the codebase modular, maintainable, and easy to extend. These guidelines outline how to set up the project locally, understand its folder structure, and contribute changes in a way that keeps the system consistent.

The project is not deployed. Everything runs locally: MySQL, the backend, the desktop app, and the website all run on one machine and talk to each other over `127.0.0.1`.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Initialization (Local Setup)](#initialization-local-setup)
3. [Contributing](#contributing)
4. [Final Project Instructions](#final-project-instructions)

---

## Project Structure

```
├── 📁 main
│   ├── 📁 backend        # FastAPI app: models, schemas, repositories, services, routes, core, exceptions, utils, tests
│   ├── 📁 database       # schema.sql, seed.sql
│   ├── 📁 desktop        # Electron + React + TypeScript + Tailwind staff application
│   ├── 📁 documentation  # UML, flowchart, screenshots, testing results, presentation
│   ├── 📁 scripts        # Build and setup scripts
│   ├── 📁 website        # Public one-page booking site (React + TypeScript + Tailwind)
│   ├── 📄 .env.example   # Template for your local .env
│   ├── 🐍 .env           # Local configuration (never committed)
│   ├── 🐍 main.py        # Entry point that starts the backend
│   └── 📄 requirements.txt
├── ⚙️ .gitignore
├── 📝 CODE_OF_CONDUCT.md
├── 📝 CONTRIBUTING.md
├── 📝 README.md
└── 📝 SECURITY.md
```

**How the MVC-inspired layers map to the code:**

| Layer | Location | Responsibility |
|---|---|---|
| Model | `backend/models`, `backend/schemas` | Domain classes (OOP entities) and Pydantic validation |
| Controller | `backend/routes`, `backend/services` | API endpoints and business logic, such as conflict checking |
| View | `desktop/source`, `website/source` | React pages and components |
| Data access | `backend/repositories`, `backend/core/connection.py` | All SQL and the MySQL connection |

Keep these layers separate: routes call services, services call repositories, and only repositories talk to MySQL.

**Ports used locally:**

| Part | Address |
|---|---|
| Backend API | `http://127.0.0.1:8000` (Swagger docs at `/docs`) |
| Website (Vite) | `http://127.0.0.1:5173` |
| Desktop (Vite, loaded inside Electron) | `http://127.0.0.1:5174` |
| MySQL | `localhost:3306` |

---

## Initialization (Local Setup)

This guide takes you from a fresh computer to a working development environment. Allow about 30 to 45 minutes the first time, mostly for downloads.

**What you will have at the end:**

- A local MySQL database named `appointmed` with its tables and sample data.
- The backend API running at `http://127.0.0.1:8000`.
- The desktop app (an Electron window) showing **Connected** for the backend and the database.
- The booking website in your browser showing **Connected** for the backend.

**Setup checklist (follow in order):**

- [ ] [Step 1: Install the required tools](#step-1-install-the-required-tools)
- [ ] [Step 2: Verify the tools](#step-2-verify-the-tools)
- [ ] [Step 3: Clone the repository](#step-3-clone-the-repository)
- [ ] [Step 4: Set up the database](#step-4-set-up-the-database)
- [ ] [Step 5: Configure environment variables](#step-5-configure-environment-variables)
- [ ] [Step 6: Run the backend](#step-6-run-the-backend)
- [ ] [Step 7: Run the desktop application](#step-7-run-the-desktop-application)
- [ ] [Step 8: Run the booking website](#step-8-run-the-booking-website)
- [ ] [Step 9: Final verification](#step-9-final-verification)

> **Commands in this guide** work on Windows, macOS, and Linux unless a Windows-specific version is shown. On Windows, use **Command Prompt** or **Git Bash** if PowerShell gives you trouble (notes are included where it matters).

### Step 1: Install the required tools

Install each tool below. If you already have one, skip to [Step 2](#step-2-verify-the-tools) to confirm the version.

| Tool | Version | Download | Used for |
|---|---|---|---|
| Git | Latest | [git-scm.com](https://git-scm.com/downloads) | Version control |
| Python | 3.11 or newer | [python.org/downloads](https://www.python.org/downloads/) | Backend |
| Node.js (includes npm) | 20 LTS or newer | [nodejs.org](https://nodejs.org) | Desktop app and website |
| MySQL Server | 8.0 or newer | [dev.mysql.com/downloads/installer](https://dev.mysql.com/downloads/installer/) | Database |
| VS Code (recommended) | Latest | [code.visualstudio.com](https://code.visualstudio.com) | Code editor |

**Installation notes:**

- **Python (Windows):** On the first installer screen, tick **"Add python.exe to PATH"** before clicking Install. This is the most common setup mistake.
- **Node.js:** Choose the **LTS** download. npm is installed with it, so you do not install npm separately. If the installer offers **"Automatically install the necessary tools"**, leave it unchecked. This project does not need them.
- **MySQL (Windows):** Use the MySQL Installer. Choose **"Server only"** (or "Custom" and select only MySQL Server and, optionally, MySQL Workbench). During configuration:
  - Keep the default port **3306**.
  - Set a **root password** and write it down. You need it in Step 4.
  - Keep the "Start MySQL Server at system startup" option on so you do not have to start it by hand.
- **MySQL (macOS):** Use the DMG installer, or `brew install mysql` then `brew services start mysql`.
- **Git:** The default options are fine.

**Recommended VS Code extensions** (optional, but they make development easier):

| Extension | Why |
|---|---|
| Python (Microsoft) | Python support and virtual environment detection |
| Pylance | Type checking and autocomplete for Python |
| ESLint | Catches TypeScript and React mistakes |
| Tailwind CSS IntelliSense | Autocomplete for Tailwind classes |
| Prettier | Consistent formatting |
| MySQL (or SQLTools) | Browse the database from the editor |

### Step 2: Verify the tools

**Close and reopen your terminal** after installing (so the PATH updates), then run:

```bash
git --version
python --version
node --version
npm --version
mysql --version
```

You should see something like `Python 3.12.x`, `v20.x.x` (or newer) for Node, and `mysql  Ver 8.x`.

| Output | What to do |
|---|---|
| `'python' is not recognized` | Try `py --version`. If that works, use `py` wherever this guide says `python`. Otherwise reinstall Python with "Add python.exe to PATH" ticked. |
| `'mysql' is not recognized` | MySQL is installed but not on your PATH. Add its `bin` folder (for example `C:\Program Files\MySQL\MySQL Server 8.0\bin`) to your PATH, then reopen the terminal. See the [Troubleshooting](#troubleshooting) table. |
| Version is too old | Install the newer version from the links above. |

On macOS or Linux you may need `python3` instead of `python`.

### Step 3: Clone the repository

```bash
git clone https://github.com/<organization-or-username>/AppointMed.git
cd AppointMed
```

Tell Git who you are (once per computer), so your commits are credited to you:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Open the project in VS Code:

```bash
code .
```

You can use the integrated terminal (`` Ctrl+` ``) for the commands below. You will need **three terminals** open at the same time later, so use the **+** button for new ones.

### Step 4: Set up the database

AppointMed stores everything in MySQL. In this step you create an empty database, create a limited user for the app, then load the tables and sample data.

**4.1 Log in to MySQL as root**

```bash
mysql -u root -p
```

Enter the root password from Step 1. You should see a `mysql>` prompt.

**4.2 Create the database and application user**

Paste this at the `mysql>` prompt. Replace `choose-a-strong-password` with your own password and remember it. You need it in Step 5.

```sql
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'appointmed_user'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

> The app uses `appointmed_user`, not `root`, so a bug or leaked password cannot damage other databases. Only `root` can change table structure (you use it to load `schema.sql`).

**4.3 Load the tables and sample data**

Run these from the **project root** (the `AppointMed` folder), not from inside `main`:

```bash
mysql -u root -p appointmed < main/database/schema.sql
mysql -u root -p appointmed < main/database/seed.sql
```

> **PowerShell does not support the `<` symbol.** If you see an error about `<`, use Command Prompt or Git Bash, or run this instead:
> ```
> mysql -u root -p appointmed -e "source main/database/schema.sql"
> mysql -u root -p appointmed -e "source main/database/seed.sql"
> ```
> You can also open each file in MySQL Workbench and run it against the `appointmed` database.

**4.4 Check that it worked**

```bash
mysql -u appointmed_user -p appointmed -e "SHOW TABLES;"
```

Enter the **appointmed_user** password. You should see a list of tables once `schema.sql` has content. If you get `Access denied`, recheck the user and password from step 4.2.

> **Load `seed.sql` only once.** Running it twice can duplicate or conflict with existing records. To start over, see [Resetting your database](#resetting-your-database).

> **Each teammate has their own local database.** The shared source of truth is `schema.sql` and `seed.sql` in the repository. See [Database changes](#database-changes) for what to do when they change.

### Step 5: Configure environment variables

Settings that differ per computer, such as passwords, live in a file called `.env`. It is never committed to Git. A template named `.env.example` is provided.

**5.1 Copy the template**

```bash
# Windows (Command Prompt)
copy main\.env.example main\.env

# macOS / Linux / Git Bash / PowerShell
cp main/.env.example main/.env
```

**5.2 Generate a secret key**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the long string it prints.

**5.3 Edit `main/.env`**

Open the file and set at least `DB_PASSWORD` and `SECRET_KEY`:

| Variable | Meaning | What to set |
|---|---|---|
| `DB_HOST` | Where MySQL runs | `localhost` (leave as is) |
| `DB_PORT` | MySQL port | `3306` (leave as is) |
| `DB_USER` | MySQL application user | `appointmed_user` (from Step 4.2) |
| `DB_PASSWORD` | Password for that user | **The password you chose in Step 4.2** |
| `DB_NAME` | Database name | `appointmed` (leave as is) |
| `API_HOST` | Address the backend listens on | `127.0.0.1` (leave as is) |
| `API_PORT` | Backend port | `8000` (leave as is) |
| `API_RELOAD` | Restart the backend automatically when code changes | `true` for development |
| `SECRET_KEY` | Signs login tokens | **The string from step 5.2** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | How long a login lasts | `60` |
| `CORS_ORIGINS` | Websites allowed to call the API | Leave as is |

> **Never commit `.env` or share it in chats or issues.** If you edit `.env` while the backend is running, **restart the backend** so it reads the new values.

### Step 6: Run the backend

The backend is a Python program, and it runs inside a **virtual environment** (`.venv`) so its packages stay separate from the rest of your computer.

**6.1 Create the virtual environment** (once)

```bash
cd main
python -m venv .venv
```

**6.2 Activate it** (every time you open a new terminal for the backend)

```bash
# Windows (Command Prompt)
.venv\Scripts\activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux / Git Bash on Windows
source .venv/bin/activate        # Git Bash on Windows: source .venv/Scripts/activate
```

Your prompt now starts with `(.venv)`. If it does not, the environment is not active.

> **PowerShell says running scripts is disabled?** Run this once, then try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

**6.3 Install the backend packages** (once, and again whenever `requirements.txt` changes)

```bash
pip install -r requirements.txt
```

**6.4 Start the backend**

```bash
python main.py
```

You should see lines ending with `Uvicorn running on http://127.0.0.1:8000` and `Application startup complete.` **Leave this terminal open.**

**6.5 Check it in your browser**

| URL | Expected result |
|---|---|
| `http://127.0.0.1:8000/health` | `{"status":"ok","service":"AppointMed API"}` |
| `http://127.0.0.1:8000/health/db` | `{"status":"ok"}` (the API can reach MySQL) |
| `http://127.0.0.1:8000/docs` | The interactive Swagger API page |

If `/health/db` shows `"status":"error"`, recheck `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `main/.env`, make sure MySQL is running, then restart the backend.

To stop the backend, press `Ctrl+C` in its terminal. To leave the virtual environment, type `deactivate`.

### Step 7: Run the desktop application

Open a **new terminal** (leave the backend running in the first one).

```bash
cd main/desktop
npm install
npm run dev
```

- `npm install` downloads all desktop dependencies, including Electron. It takes a few minutes the first time and creates a `node_modules` folder (ignored by Git). You only repeat it when `package.json` changes.
- `npm run dev` starts the Vite dev server and then opens an Electron window titled **AppointMed**.

**Expected result:** a card titled "AppointMed Desktop" with **Backend API: Connected** and **MySQL database: Connected** in green.

**Handy tips:**

- Open the developer tools inside the Electron window with `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (macOS) to see console errors.
- Changes to files in `desktop/source` appear in the window automatically (hot reload).
- To stop the desktop app, press `Ctrl+C` in its terminal.

### Step 8: Run the booking website

Open a **third terminal**.

```bash
cd main/website
npm install
npm run dev
```

Open `http://127.0.0.1:5173` in your browser.

**Expected result:** a card titled "AppointMed" with **Backend API: Connected** in green. Edits to files in `website/source` refresh the page automatically.

### Step 9: Final verification

Confirm all of the following before you start working on features:

- [ ] `http://127.0.0.1:8000/docs` loads.
- [ ] `http://127.0.0.1:8000/health/db` returns `{"status":"ok"}`.
- [ ] The desktop window shows Backend API and MySQL database as **Connected**.
- [ ] The website at `http://127.0.0.1:5173` shows Backend API as **Connected**.
- [ ] If the database seed includes a default admin account, log in with it and **change the password immediately**.
- [ ] Backend tests run (from `main`, with the virtual environment active):

```bash
pytest backend/test
```

> While `backend/test` is still empty, pytest reports `no tests ran`. That is normal.

If a check fails, see [Troubleshooting](#troubleshooting).

### Everyday workflow

After the first setup, starting work takes three terminals:

| Terminal | Folder | Commands |
|---|---|---|
| 1. Backend | `main` | Activate `.venv` (Step 6.2), then `python main.py` |
| 2. Desktop | `main/desktop` | `npm run dev` |
| 3. Website | `main/website` | `npm run dev` |

Start the **backend first**, since the desktop app and website both depend on it. MySQL should already be running (it starts with your computer by default).

**After pulling changes from GitHub**, check what changed and update accordingly:

| If this changed | Run |
|---|---|
| `main/requirements.txt` | `pip install -r requirements.txt` (virtual environment active) |
| `desktop/package.json` | `npm install` inside `main/desktop` |
| `website/package.json` | `npm install` inside `main/website` |
| `main/database/schema.sql` or `seed.sql` | Reload your database (see below) |
| `main/.env.example` | Add any new variables to your own `main/.env` |

### Resetting your database

Use this when `schema.sql` or `seed.sql` changed, or when your local data is messy. **This deletes all data in your local `appointmed` database.**

```bash
mysql -u root -p -e "DROP DATABASE appointmed; CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p appointmed < main/database/schema.sql
mysql -u root -p appointmed < main/database/seed.sql
```

If you dropped the database, the application user's privileges on it are removed too, so re-run the `GRANT` and `FLUSH PRIVILEGES` lines from Step 4.2:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
FLUSH PRIVILEGES;
```

### Building executables (optional)

Use the scripts in `main/scripts` to build the deliverables:

```bash
main\scripts\build-backend.bat    # PyInstaller: bundles the FastAPI backend
main\scripts\build-desktop.bat    # Electron Builder: packages the desktop app
```

The desktop app can also be packaged manually with `npm run package` inside `main/desktop`. Running with `npm run dev` is enough for the final demo.

### Troubleshooting

**Tools and installation**

| Problem | What to check |
|---|---|
| `'python' is not recognized` | Try `py` instead. Otherwise reinstall Python with "Add python.exe to PATH" ticked, then reopen the terminal. |
| `'mysql' is not recognized` | Add the MySQL `bin` folder (for example `C:\Program Files\MySQL\MySQL Server 8.0\bin`) to your PATH: Windows search, "Edit the system environment variables", Environment Variables, select `Path`, Edit, New. Reopen the terminal. |
| `'npm' is not recognized` | Reinstall Node.js, then reopen the terminal. |
| `npm install` fails | Confirm Node.js is version 20 or newer. Delete the `node_modules` folder and `package-lock.json`, then run `npm install` again. |
| Electron download is slow or fails | Check your internet connection and try `npm install` again. On school networks, a different network or a phone hotspot often helps. |

**Database**

| Problem | What to check |
|---|---|
| `Can't connect to MySQL server` | MySQL is running (Windows: open "Services", find **MySQL80**, and start it). Check `DB_HOST` and `DB_PORT` in `.env`. |
| `Access denied for user` | The user exists, the password in `.env` matches, and privileges were granted on `appointmed` (Step 4.2). |
| `Unknown database 'appointmed'` | The database was not created. Repeat Step 4.2. |
| `/health/db` returns `"status":"error"` | Recheck every `DB_*` value in `.env`, then restart the backend. |
| Duplicate entry errors when loading `seed.sql` | It was already loaded. See [Resetting your database](#resetting-your-database). |
| `<` is not recognized (PowerShell) | Use Command Prompt or Git Bash, or the `source` form shown in Step 4.3. |

**Backend**

| Problem | What to check |
|---|---|
| `ModuleNotFoundError` | The virtual environment is active (prompt starts with `(.venv)`) and `pip install -r requirements.txt` was run. |
| `ModuleNotFoundError: backend` | Run `python main.py` from inside the `main` folder, not from the repository root. |
| PowerShell blocks `Activate.ps1` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use Command Prompt. |
| Changes to `.env` have no effect | Stop the backend with `Ctrl+C` and start it again. |

**Desktop and website**

| Problem | What to check |
|---|---|
| Shows "Not reachable" | The backend is running on the port in `API_PORT`, and the page's origin is listed in `CORS_ORIGINS` in `.env`. Restart the backend after editing `.env`. |
| Browser console shows a CORS error | Add the page's exact origin (for example `http://127.0.0.1:5173`) to `CORS_ORIGINS` and restart the backend. |
| Electron window is blank | Wait a few seconds for Vite to start, then press `Ctrl+R`. Check the terminal and the developer tools (`Ctrl+Shift+I`) for errors. |
| Electron window never opens | Another process may be using port 5174. Close it and rerun `npm run dev`. |
| `Port 5173`, `5174`, or `8000` is already in use | Another program or an old copy of this app is using it. Find it with `netstat -ano \| findstr :8000` (Windows) or `lsof -i :8000` (macOS/Linux), then close it (Windows: `taskkill /PID <number> /F`). The Vite ports are fixed on purpose so they match the CORS settings. |
| TypeScript errors in the editor | Run `npm install` in that folder, then restart VS Code's TypeScript server (Command Palette, "TypeScript: Restart TS Server"). |

If you are still stuck, ask in the team chat with the **exact error message**, the **step number** you were on, and your operating system. Do not paste your `.env` contents.

---

## Contributing

### Workflow

1. **Pick or create an issue** so the team knows who is working on what.
2. **Sync with `main`:**
```bash
   git checkout main
   git pull origin main
```
3. **Create a branch** for your work. Never commit directly to `main`.
```bash
   git checkout -b feat/appointment-conflict-check
```
4. **Make your changes** in small, focused commits.
5. **Test** your changes locally, with the backend, desktop app, and (if affected) website all running.
6. **Push** your branch and **open a pull request** into `main`.
7. **Get at least one teammate's review** before merging. Respond to feedback and push fixes to the same branch.
8. **Merge** once approved, then delete the branch.

### Branch naming

| Prefix | Use for | Example |
|---|---|---|
| `feat/` | New features | `feat/patient-search` |
| `fix/` | Bug fixes | `fix/double-booking` |
| `docs/` | Documentation only | `docs/uml-diagram` |
| `refactor/` | Code changes with no behavior change | `refactor/repository-base-class` |
| `test/` | Adding or fixing tests | `test/auth-permissions` |
| `chore/` | Tooling, dependencies, config | `chore/update-requirements` |

### Commit messages

Use the format `type: short summary in present tense`.

```
feat: add doctor availability check
fix: prevent overlapping appointments for the same doctor
docs: add flowchart to documentation folder
```

Keep the summary under about 72 characters, and add a body if the reason for the change isn't obvious.

### Pull request checklist

Before requesting a review, confirm that:

- [ ] The branch is up to date with `main` and has no merge conflicts.
- [ ] The app runs, and the feature works with each affected role (Admin, Doctor, Nurse/Secretary).
- [ ] Tests were added or updated, and `pytest backend/test` passes.
- [ ] Invalid input and errors are handled with clear messages, using the custom exceptions where appropriate.
- [ ] No secrets, `.env` files, real personal data, or build output are committed.
- [ ] Changes to the database are reflected in `main/database/schema.sql` (and `seed.sql` if needed) and announced to the team.
- [ ] New dependencies are added to `requirements.txt` or the relevant `package.json`.
- [ ] Documentation is updated if behavior, endpoints, or setup changed.
- [ ] You can explain every part of your code. The course requires it.

### Coding standards

**Python (backend)**

- Follow [PEP 8](https://peps.python.org/pep-0008/): `snake_case` for functions and variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Add type hints and short docstrings to classes and public methods.
- Apply OOP principles deliberately, since they make up 30% of the grade:
  - **Encapsulation:** use private attributes with properties in models.
  - **Inheritance:** share common fields through base classes such as `Person`, `Patient`, and `Doctor`.
  - **Polymorphism:** let each role in `roles.py` implement its own permissions.
  - **Abstraction:** define abstract base classes such as `BaseEntity` and `BaseRepository`.
- Raise custom exceptions from `backend/exceptions` rather than generic ones, and keep error mapping in `exception_handlers.py`.
- Keep SQL in repositories only, and always use parameterized queries.
- Validate all external input with Pydantic schemas.

**TypeScript / React (desktop and website)**

- Use TypeScript types for props, API responses, and state, and avoid `any`.
- Name components and their files in `PascalCase` (`PatientsPage.tsx`) and hooks with a `use` prefix (`useAuth.ts`).
- Keep API calls in `source/api`, reusable UI in `source/components`, and page-level screens in `source/pages`.
- Style with Tailwind utility classes. Avoid inline styles.
- Hiding UI by role is a convenience only. The backend must enforce permissions.

**General**

- Prefer small, reusable functions and clear names over clever code.
- Comment the *why*, not the obvious *what*.
- Don't leave dead code or debugging prints in merged work.

### Database changes

Every teammate has their own local database, so schema changes must be shared through the repository:

1. Update `main/database/schema.sql` (and `seed.sql` if starting data changes).
2. Mention the change in your pull request description, with the exact SQL needed to update an existing database.
3. Tell the team once it is merged so everyone reloads their local database (see [Resetting your database](#resetting-your-database)).

### Documentation and deliverables

Keep `main/documentation` current as you work. The final submission needs the technical documentation (PDF), UML class diagram, flowchart, application screenshots, testing results, and the PowerPoint presentation. Update the diagrams when classes or flows change, and save test results and screenshots as you go instead of at the end. Use only fictional data in screenshots.

### Reporting bugs and requesting features

Open a GitHub issue with:

- **Bugs:** what you expected, what happened, the steps to reproduce it, your role (Admin, Doctor, Nurse/Secretary), and any error message.
- **Features:** the problem it solves and how you imagine it working.

For security problems, do **not** open a public issue. See [SECURITY.md](SECURITY.md).

### AI-assisted coding

Per the course rules, AI tools may be used ethically for learning and productivity, but the work must be your own, and you must understand and be able to explain every part of your code. Don't submit code you cannot explain during the demonstration.

---

## Final Project Instructions

*These are the official course requirements the project is graded against.*

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