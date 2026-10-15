# CONTRIBUTING GUIDELINES

AppointMed is a clinic appointment and management system built with a Python (FastAPI) backend, an Electron + React + TypeScript desktop application, and a public one-page booking website. All clients connect to a shared MySQL database so that Doctor, Nurse/Secretary, and Admin users on different machines can view and update the same live data. This project was developed as the final requirement for CMSC 203 – Object-Oriented Programming, and follows an MVC-inspired architecture that separates data models, user interface views, and business-logic controllers to keep the codebase modular, maintainable, and easy to extend. These guidelines outline how to set up the project locally, understand its folder structure, and contribute changes in a way that keeps the system consistent across all client devices.

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
│   ├── 🐍 .env           # Local configuration (never committed)
│   ├── 🐍 main.py        # Entry point that starts the backend
│   └── 📄 requirements.txt
├── ⚙️ .gitignore
├── 📝 CONTRIBUTING.md
├── 📝 DOCUMENTATION.md
└── 📝 README.md
```

**How the MVC-inspired layers map to the code:**

| Layer | Location | Responsibility |
|---|---|---|
| Model | `backend/models`, `backend/schemas` | Domain classes (OOP entities) and Pydantic validation |
| Controller | `backend/routes`, `backend/services` | API endpoints and business logic, such as conflict checking |
| View | `desktop/src`, `website/src` | React pages and components |
| Data access | `backend/repositories`, `backend/core/connection.py` | All SQL and the MySQL connection |

Keep these layers separate: routes call services, services call repositories, and only repositories talk to MySQL.

---

## Initialization (Local Setup)

### Prerequisites

Install the following before you begin:

| Tool | Version | Purpose |
|---|---|---|
| Git | Latest | Version control |
| Python | 3.11 or newer | Backend |
| Node.js (with npm) | 20 LTS or newer | Desktop app and website |
| MySQL Server | 8.0 or newer | Shared database |

### 1. Clone the repository

```bash
git clone https://github.com/<organization-or-username>/AppointMed.git
cd AppointMed
```

### 2. Set up the database

Log in to MySQL and create the database and a dedicated application user (do not use `root` in `.env`):

```sql
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'appointmed_user'@'%' IDENTIFIED BY 'choose-a-strong-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'%';
FLUSH PRIVILEGES;
```

Then load the tables and the starting data:

```bash
mysql -u root -p appointmed < main/database/schema.sql
mysql -u root -p appointmed < main/database/seed.sql
```

> **Shared database:** The team uses one MySQL server so everyone sees the same live data. Run `seed.sql` **only on your own local database**, never on the shared server, because it would overwrite or duplicate records. To use the shared server, ask a maintainer for the host, port, and your own credentials.

### 3. Configure environment variables

Create `main/.env` and fill in your values:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=appointmed_user
DB_PASSWORD=your-password-here
DB_NAME=appointmed

# Backend
API_HOST=127.0.0.1
API_PORT=8000
SECRET_KEY=generate-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> **Never commit `.env`.** It is listed in `.gitignore`. Each machine has its own copy. Generate a secret key with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

### 4. Run the backend

```bash
cd main
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

The API runs at `http://127.0.0.1:8000`, and interactive API docs (Swagger) are available at `http://127.0.0.1:8000/docs`.

### 5. Run the desktop application

In a new terminal, with the backend running:

```bash
cd main/desktop
npm install
npm run dev
```

### 6. Run the booking website

In another terminal:

```bash
cd main/website
npm install
npm run dev
```

The website opens at the local URL printed by Vite (usually `http://localhost:5173`).

### 7. Verify your setup

- `http://127.0.0.1:8000/docs` loads.
- You can log in to the desktop app with the default admin account from `seed.sql`. **Change that password immediately.**
- Run the backend tests:

```bash
cd main
pytest backend/tests
```

### Building executables

Use the scripts in `main/scripts` to build the deliverables:

```bash
main\scripts\build-backend.bat    # PyInstaller: bundles the FastAPI backend
main\scripts\build-desktop.bat    # Electron Builder: packages the desktop app
```

### Troubleshooting

| Problem | What to check |
|---|---|
| `Can't connect to MySQL server` | MySQL is running, and `DB_HOST`, `DB_PORT`, and credentials in `.env` are correct. For a shared server, check your network and firewall. |
| `ModuleNotFoundError` | The virtual environment is activated and `pip install -r requirements.txt` was run. |
| Desktop app can't reach the API | The backend is running and `API_PORT` matches the port the desktop app calls. |
| `Access denied for user` | The MySQL user exists and was granted privileges on the `appointmed` database. |

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
- [ ] Tests were added or updated, and `pytest backend/tests` passes.
- [ ] Invalid input and errors are handled with clear messages, using the custom exceptions where appropriate.
- [ ] No secrets, `.env` files, real personal data, or build output are committed.
- [ ] Changes to the database are reflected in `main/database/schema.sql` (and `seed.sql` if needed) and announced to the team.
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
- Keep API calls in `src/api`, reusable UI in `src/components`, and page-level screens in `src/pages`.
- Style with Tailwind utility classes. Avoid inline styles.
- Hiding UI by role is a convenience only. The backend must enforce permissions.

**General**

- Prefer small, reusable functions and clear names over clever code.
- Comment the *why*, not the obvious *what*.
- Don't leave dead code or debugging prints in merged work.

### Database changes

The database is shared, so schema changes affect everyone:

1. Update `main/database/schema.sql` (and `seed.sql` if starting data changes).
2. Mention the change in your pull request description, with the exact SQL needed to update an existing database.
3. Tell the team once it is merged so everyone updates their local database.

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