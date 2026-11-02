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



### Features

- **Public online booking:** Patients choose a doctor, a date, and an open time slot generated from the doctor's weekly schedule. No account is needed. Requests are rate-limited, and a database constraint prevents double booking.
- **Request review:** Nurses (or the doctor) approve or disapprove each request, and the patient is emailed the result. Approving creates the patient record (or reuses a matching one) and the appointment.
- **Check-in queue:** Patients are served in check-in order using a min-heap `WaitingQueue`. Doctors examine one patient at a time and are notified when someone checks in.
- **Examination and prescriptions:** Doctors record the diagnosis and notes, prescribe medicines with unit prices, assign an exam room, and can book a follow-up visit.
- **Billing:** An invoice opens when the examination starts (consultation fee) and updates when it finishes (fee plus medicines). The doctor or nurse marks it paid, which completes the visit.
- **Patient records and history:** Search, add, edit, and delete patients (only when they have no visits), and review every completed visit with its prescription and bill, filterable by date range.
- **Walk-ins, rescheduling, cancelling, and rooms:** Staff can create walk-in appointments, move or cancel scheduled ones, and switch rooms between Available, Occupied, and Maintenance.
- **Role-based access control:** Doctor, Nurse, and Admin roles are enforced on the server. A nurse works only with the data of the doctor they are assigned to.
- **Admin tools:** Create, edit, and deactivate users, set doctors' weekly schedules, manage rooms, edit clinic settings (name, default fee, booking switch and window), view reports for a date range, and review the audit log.
- **Profiles:** Every user can edit their name, email, and photo, and change their password.
- **Validation and error handling:** Pydantic validates every input, and custom exceptions become plain `{"detail": "..."}` messages. SQL details are never shown to users.

### Developers:

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

AppointMed is developed as the final project for CMSC 203, ITEC 104, and ITEC 105, under the supervision of Ms. Roxanne Garbo, Sir Rolan C. Sotomayor, and Sir Jencel P. Sofer. It demonstrates object-oriented design, user interface development, exception handling, database integration, and software engineering practices.

| Course | Where it shows up in the project |
|---|---|
| **CMSC 203** (OOP) | Role classes (`Doctor`, `Nurse`, `Admin`) extending an abstract `User`, abstract repositories, encapsulated `Settings` and `Database`, and a family of custom exceptions |
| **ITEC 104** (Data Structures and Algorithms) | A min-heap waiting queue, a sliding-window rate limiter, an appointment status state machine, and slot generation and searching |
| **ITEC 105** (Information Management) | A 12-table normalized MySQL schema with keys, constraints, and a double-booking guard, plus transactions, parameterized queries, reports, and an audit log |

The exact classes and files are listed in [CONTRIBUTING.md](CONTRIBUTING.md#where-code-belongs).

---

*Last Updated: October 2026*