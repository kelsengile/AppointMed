# DOCUMENTATION | AppointMed

AppointMed is a web-based clinic management platform designed to streamline the daily operations of healthcare practices, from patient scheduling and record-keeping to administrative and back-office workflows. This document outlines the research conducted in support of the system's design and development, covering the problem domain, existing solutions, target users, and the technical and functional requirements that informed key design decisions. As a coursework project for CMSC 203 – Object-Oriented Programming, this research also grounds the system's architecture in object-oriented principles, ensuring that the final implementation reflects both sound software engineering practices and a genuine understanding of the challenges clinics face in managing day-to-day operations.

**Developers**

Ambrocio, Rhen Jemimah L.  
Altobar, Loraine R.    
Conel, Kelsen Gile S.  
Ortega, Xavier Kent C. 

**Course Affiliation**
 
Laguna State Polytechnic University | College of Computer Studies
CMSC 203 – Object-Oriented Programming
Instructor: Ms. Roxanne Garbo
Academic Year: 2026 – 2027
System Project Assigned: Clinic Appointment System
 
---

## Introduction

AppointMed is a web application for managing clinic appointments. Clinic staff (doctors, nurses, and administrators) sign in through a web browser to manage schedules, patient records, examinations, prescriptions, and billing. Patients use a public booking page to request an appointment without needing an account. All users share a single MySQL database, accessed only through a Python (FastAPI) backend, so everyone sees the same up-to-date information.

Because it runs in a browser, AppointMed needs no installation on each clinic computer. Any device on the clinic network with a modern browser can use it.

## Statement of the Problem

Many small clinics still rely on paper logbooks, phone calls, and scattered spreadsheets to manage appointments. This leads to several problems:

- Double-booked time slots and unclear doctor availability.
- Patients who must phone the clinic during office hours just to book a visit.
- Appointment requests that get lost or are handled late.
- Patient records that are hard to find and not shared between doctor and nurse.
- No clear record of who changed what, or which sessions have been billed.

## Objectives

**General objective:** To design and develop a web-based, object-oriented clinic appointment system that centralizes scheduling, patient records, and billing for clinic staff and lets patients request appointments online.

**Specific objectives:**

1. Provide a public booking page where patients can view available time slots and request an appointment.
2. Let nurses convert requests into appointments, register walk-ins, and manage the waiting queue.
3. Let doctors examine patients, record diagnoses, schedule follow-ups, and issue prescriptions.
4. Prevent conflicting bookings for the same doctor and time.
5. Restrict system functions by user role (Admin, Doctor, Nurse) with secure authentication.
6. Handle invalid input, database errors, and scheduling conflicts with clear messages.
7. Apply object-oriented principles (encapsulation, inheritance, polymorphism, abstraction) in the backend design.

## Scope and Limitations

**Scope**

- Web application for a single clinic, used by Doctor, Nurse, and Admin roles.
- Public booking page for patients (no patient accounts).
- Management of users, doctor schedules, rooms, appointments, examinations, prescriptions, and session invoices.
- Admin tools for clinic settings and an audit log.
- Centralized MySQL database accessed through a FastAPI backend.

**Limitations**

- Intended for one clinic; multi-branch support is not included.
- Prescriptions are record-keeping only. There is no pharmacy or inventory module.
- Billing covers per-session invoices only, with no online payment processing.
- No SMS or email delivery of reminders in the current version.
- No patient portal for viewing records.
- Uses fictional sample data only and is not certified for real medical records.

## Review of Related Study & Systems

*To be completed by the team.* Suggested approach:

1. Identify 3–5 existing clinic or appointment systems (commercial or open source) and compare their features against AppointMed.
2. Summarize 2–3 published studies or articles on appointment scheduling, no-show reduction, or clinic information systems.
3. Cite every source in the References section.

## System Features

| Feature | Description | Primary role |
|---|---|---|
| Online booking | Patients pick a doctor and an open time slot and submit a request | Public |
| Request inbox | Nurses review requests and convert or dismiss them | Nurse |
| Walk-in booking | Create an appointment directly for a patient at the clinic | Nurse, Doctor |
| Doctor schedules | Weekly working hours that drive slot availability | Admin, Doctor |
| Conflict prevention | A doctor cannot hold two active appointments at the same time | System |
| Check-in and queue | Patients are checked in and ordered in a waiting queue | Nurse |
| Room board | Track which rooms are available, occupied, or in maintenance | Nurse, Doctor |
| Examination | Record diagnosis and notes, then schedule a follow-up or send to history | Doctor |
| Prescriptions | Write medicines and instructions to hand to the patient | Doctor |
| Billing | Issue and track per-session invoices | Nurse |
| User management | Create, edit, and deactivate staff accounts | Admin |
| Clinic settings | Clinic name, default fee, booking window, and online booking toggle | Admin |
| Audit log | Review who did what and when | Admin |
| Authentication and roles | Secure login with role-based access enforced by the backend | All staff |

## UML Class Diagram

*To be added.* Save the exported diagram in `source/documentation/diagrams/` and link it here, for example:

```
![AppointMed UML class diagram](diagrams/uml-class-diagram.png)
```

## Flowchart

*To be added.* Save flowcharts in `source/documentation/flowcharts/`. Suggested flows:

1. Patient books an appointment online.
2. Nurse converts a request to an appointment and checks the patient in.
3. Doctor examines the patient and chooses follow-up or history.

## Screenshot of the Application

*To be added.* Save screenshots in `source/documentation/screenshots/`. Use fictional data only.

## Testing Results

*To be completed as features are built.* Record each test in a table:

| ID | Feature | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| T-01 | Health check | Open the web app with backend and MySQL running | Shows Backend API: Online and Database: Connected | | |

## Conclusion

*To be written after testing and the final demonstration.*

## References

- FastAPI documentation. https://fastapi.tiangolo.com
- React documentation. https://react.dev
- Vite documentation. https://vite.dev
- Tailwind CSS documentation. https://tailwindcss.com/docs
- Pydantic documentation. https://docs.pydantic.dev
- MySQL Reference Manual. https://dev.mysql.com/doc/
- Contributor Covenant, version 2.1. https://www.contributor-covenant.org

*Add the related studies and systems from the review section here.*

---

*Last Updated: October 2026*
