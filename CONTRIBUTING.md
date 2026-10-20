# CONTRIBUTING GUIDELINES

AppointMed is a web-based clinic appointment and management system built with a Python (FastAPI) backend and a React + TypeScript web frontend. Clinic staff (Doctor, Nurse, and Admin users) work in a browser-based portal, and patients use a public booking page. Everything connects to one MySQL database so all users work with the same live data. This project was developed as the final requirement for CMSC 203 – Object-Oriented Programming, and follows an MVC-inspired architecture that separates data models, user interface views, and business-logic controllers to keep the codebase modular, maintainable, and easy to extend. These guidelines outline how to set up the project locally, understand its folder structure, and contribute changes in a way that keeps the system consistent.

---

## Initialization

### Prerequisites

- [Git](https://git-scm.com/)
- [Python](https://www.python.org/) 3.11 or newer
- [Node.js](https://nodejs.org/) 20 or newer (includes npm)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/) 8.0 or newer

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### Step 2: Install backend dependencies

```bash
cd source
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Install frontend dependencies

```bash
cd source/frontend
npm install
```

### Step 4: Create the database and the app user

Log in to MySQL as root:

```bash
mysql -u root -p
```

Then run the following. Replace the password with your own, and use the same one in Step 6.

```sql
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'appointmed_user'@'localhost' IDENTIFIED BY 'change_this_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

The web app connects as `appointmed_user`, never as `root`.

### Step 5: Load the schema and sample data

From the project root:

```bash
mysql -u root -p appointmed < source/database/schema.sql
mysql -u root -p appointmed < source/database/seed.sql
```

Load `seed.sql` **once**. It contains fictional development data only. Sample logins are listed at the top of `seed.sql`.

### Step 6: Configure the environment

Copy the template and fill in your values:

```bash
cd source
cp .env.example .env        # Windows: copy .env.example .env
```

Set `DB_PASSWORD` to the password from Step 4, and set a new `JWT_SECRET`. The `.env` file is gitignored. **Never commit it.**

### Step 7: Run the project

Use two terminals.

**Backend** (from `source`, with the virtual environment active):

```bash
uvicorn main:app --reload
```

- Status page: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

**Frontend** (from `source/frontend`):

```bash
npm run dev
```

- Web app: http://localhost:5173

### Verify the setup

Open http://localhost:5173. You should see:

- **Backend API: Online** means the frontend can reach FastAPI.
- **Database: Connected** means FastAPI can reach MySQL.

If the database shows **Not connected**, check that MySQL is running and that `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in `source/.env` match Step 4.

### Resetting your database

To start over with fresh sample data:

```sql
DROP DATABASE appointmed;
CREATE DATABASE appointmed CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT SELECT, INSERT, UPDATE, DELETE ON appointmed.* TO 'appointmed_user'@'localhost';
```

Then repeat Step 5. Never run `seed.sql` against a shared or production database.

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
    ├── .env                  # local secrets (gitignored)
    ├── .env.example          # template for .env
    ├── main.py               # FastAPI entry point
    ├── requirements.txt      # Python dependencies
    ├── assets/               # fonts, icons, and images
    ├── database/
    │   ├── schema.sql        # tables and constraints
    │   └── seed.sql          # fictional sample data
    ├── documentation/
    │   ├── DOCUMENTATION.md  # technical documentation
    │   ├── diagrams/         # UML class diagrams
    │   ├── flowcharts/
    │   └── screenshots/
    └── frontend/             # React + TypeScript web app (Vite)
        ├── index.html
        ├── package.json
        ├── vite.config.ts
        ├── tailwind.config.js
        └── src/
            ├── main.tsx
            └── app.tsx
```

As the backend grows, split `main.py` into modules (models, repositories, services, routes) rather than letting one file grow large.

---

## Contributing

### Workflow

1. Pull the latest `main` before starting.
2. Create a branch named for the work: `feature/appointment-booking`, `fix/slot-conflict`, `docs/uml-diagram`.
3. Make small, focused commits with clear messages, for example `Add doctor availability endpoint`.
4. Push your branch and open a pull request. Describe what changed and how you tested it.
5. At least one teammate reviews the pull request before it is merged.

### Coding standards

- **Python:** follow PEP 8, use type hints, and give classes and methods docstrings. Keep business logic in service classes, not in route functions.
- **TypeScript/React:** use function components and typed props. Keep API calls in one place rather than scattering `fetch` calls across components.
- **Object-oriented design:** prefer clear classes with single responsibilities. Use inheritance, abstraction, and encapsulation where they make the design simpler, not just to tick a rubric box.
- **Errors:** validate input with Pydantic, raise meaningful custom exceptions, and return clear messages. Never expose stack traces or password hashes.
- **SQL:** use parameterized queries only. Never build SQL by joining user input into strings.

### Data and secrets

- Use only fictional or anonymized data in code, screenshots, and demos.
- Never commit `.env`, database dumps with real data, or credentials.
- Read [SECURITY.md](SECURITY.md) before touching authentication, roles, or public booking endpoints.

### Understand what you submit

AI-assisted tools may be used for learning and productivity, but every team member must understand and be able to explain any code they commit.

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
