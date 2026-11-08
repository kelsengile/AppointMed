<div align="center">
  <img src="/source/assets/icons/appointmed-logo.png" width="250" style="display: block; margin: 0;"/>
</div>

<h1 align="center" style="font-size: 40px;">AppointMed</h1>

<p align="center">
  <img src="https://img.shields.io/badge/React-111111?style=flat-square&logo=react&logoColor=61DAFB" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-111111?style=flat-square&logo=typescript&logoColor=3178C6" alt="TypeScript">
  <img src="https://img.shields.io/badge/Vite-111111?style=flat-square&logo=vite&logoColor=646CFF" alt="Vite">
  <img src="https://img.shields.io/badge/Tailwind_CSS-111111?style=flat-square&logo=tailwindcss&logoColor=06B6D4" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/Python-111111?style=flat-square&logo=python&logoColor=3776AB" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-111111?style=flat-square&logo=fastapi&logoColor=009688" alt="FastAPI">
  <br>
  <img src="https://img.shields.io/badge/MySQL_Server-111111?style=flat-square&logo=mysql&logoColor=4479A1" alt="MySQL Server">
  <img src="https://img.shields.io/badge/MySQL_Connector%2FPython-111111?style=flat-square&logo=mysql&logoColor=4479A1" alt="MySQL Connector/Python">
  <img src="https://img.shields.io/badge/Pydantic-111111?style=flat-square&logo=pydantic&logoColor=E92063" alt="Pydantic">
  <img src="https://img.shields.io/badge/Git-111111?style=flat-square&logo=git&logoColor=F05032" alt="Git">
  <img src="https://img.shields.io/badge/GitHub-111111?style=flat-square&logo=github&logoColor=FFFFFF" alt="GitHub">
</p>

<br>

AppointMed is a web-based clinic appointment and management system. Patients request appointments on a public booking page, and clinic staff (doctors, nurses, and administrators) use a role-based browser portal that takes each visit from request to payment. A FastAPI backend serves both, and every record lives in one shared MySQL database.

### Quick start

```bash
python dev.py        # Windows: py dev.py  ->  press "f" for first-time setup
```

The dev console checks your tools, installs packages, writes `source/.env`, sets up the database, and starts the backend (http://127.0.0.1:8000) and the web app (http://localhost:5173). Full steps are in [CONTRIBUTING.md](CONTRIBUTING.md).

### Features

- **Public front page:** A landing page with services, a live "Meet Our Staff" list (from the database), clinical departments with a search popup, and the clinic's name and address from Clinic Settings.
- **Public online booking:** Patients choose a doctor, a date from a calendar that shows unavailable and fully booked days, and an open time slot built from the doctor's weekly schedule. No account is needed. Requests are rate-limited, and a database constraint prevents double booking.
- **Doctor days off:** Doctors mark single dates as unavailable (with a reason only staff can see). Those days disappear from booking, approval, rescheduling, and follow-ups.
- **Request review:** Nurses (or the doctor) approve or disapprove each request, and the patient is emailed the result. Approving creates the patient record (or reuses a matching one) and the appointment.
- **Check-in queue:** A room must be chosen before a patient is checked in. Patients are served in check-in order using a min-heap `WaitingQueue`. Doctors examine one patient at a time (enforced with a row lock) and are notified when someone checks in.
- **Examination and prescriptions:** Doctors record the diagnosis and notes, prescribe medicines with a dosage amount and unit and a unit price, assign an exam room, and can book a follow-up visit.
- **Billing:** An invoice opens when the examination starts and updates when it finishes (fee plus medicines). The doctor or nurse marks it paid, which completes the visit.
- **Patient records and history:** Search, add, edit, and delete patients (only when they have no visits), and review every completed visit, filterable by date range.
- **Role-based access control:** Doctor, Nurse, and Admin roles are enforced on the server. A nurse works only with the data of the doctor they are assigned to.
- **Admin tools:** Users, weekly schedules, rooms, clinic settings, reports with CSV download, and an audit log.
- **Admin Database page:** Browse and edit table rows, run one SQL statement in a guarded console, download a full `.sql` backup, and import a backup made by the app. Every change is audited.
- **Strong passwords and safe input:** New passwords need 8+ characters with upper and lower case, a number, and a special character. Pydantic validates every input on the server, and the forms stop invalid characters from being typed.
- **Profiles:** Every user can edit their name, email, and photo, and change their password.

### Developers

**Ambrocio, Rhen Jemimah L.**  
**Altobar, Loraine R.**  
**Conel, Kelsen Gile S.**  
**Ortega, Xavier Kent C.**

---

## Coursework Project

**Laguna State Polytechnic University** | **College of Computer Studies**  
**CMSC 203 – Object-Oriented Programming, ITEC 104 – Data Structures and Algorithm, ITEC 105 – Information Management**  
**Instructors:** Ms. Roxanne Garbo, Sir Rolan C. Sotomayor, Sir Jencel P. Sofer  
**Academic Year:** 2026–2027

AppointMed is developed as the final project for CMSC 203, ITEC 104, and ITEC 105. It demonstrates object-oriented design, user interface development, exception handling, database integration, and software engineering practices.

| Course | Where it shows up in the project |
|---|---|
| **CMSC 203** (OOP) | Role classes (`Doctor`, `Nurse`, `Admin`) extending an abstract `User`, abstract `Executor` and `BaseRepository`, encapsulated `Settings` and `Database`, and a family of custom exceptions |
| **ITEC 104** (Data Structures and Algorithms) | A min-heap waiting queue, a sliding-window rate limiter on a `deque`, an appointment state machine, hash-set slot lookups, and sorted overlap detection |
| **ITEC 105** (Information Management) | A normalized MySQL schema (13 tables plus `departments`) with keys, `CHECK` constraints, and a double-booking guard, plus transactions, parameterized queries, reports, an audit log, and backup and restore |

---

*Last Updated: November 2026*