# CONTRIBUTING GUIDELINES

AppointMed is a Python + CustomTkinter desktop application for managing clinic appointments, built around a shared MySQL backend so that Doctor, Nurse/Secretary, and Admin users on different machines can view and update the same live data in real time. This project was developed as the final requirement for CMSC 203 – Object-Oriented Programming, and follows an MVC-inspired architecture that separates data models, GUI views, and business-logic controllers to keep the codebase modular, maintainable, and easy to extend. These guidelines outline how to set up the project locally, understand its folder structure, and contribute changes in a way that keeps the system consistent across all client devices.

---
## Initialization:

Python + CustomTkinter clinic appointment system with a shared MySQL backend,
so Doctor, Nurse/Secretary, and Admin accounts on different devices all
see the same live data.

**Setup**

1. Install Git, Make a GitHub Acc, and Install MySQL Server and Workbench
1. `py -m pip install -r main/requirements.txt`
2. Start/point to a MySQL server reachable by all client devices.
3. Run `database/schema.sql` against it once to create the tables.
4. Update `config/settings.py` with that server's host/credentials.
5. Run `python main.py` on each device 

**Architecture**

MVC-ish split:
- **models/** — plain Python classes, no Tkinter or SQL
- **views/** — Tkinter windows only, one subfolder per role
- **controllers/** — validation + database calls, raises custom exceptions
  from `utils/exceptions.py` which the views catch and display

**Folder structure**

```
AppointMed/
├── 📁 main
│   ├── 📁 assets                      # Static files used by the app (images, icons)
│   │   └── 📁 icons
│   │   └── 📁 images                     
│   ├── 📁 config                      # App-wide settings (DB credentials, constants)
│   │   └── 🐍 settings.py            
│   ├── 📁 controllers                 # Business logic — validation + DB calls (the "C" in MVC)
│   │   ├── 🐍 appointment_controller.py   
│   │   ├── 🐍 auth_controller.py          
│   │   └── 🐍 user_controller.py          
│   ├── 📁 database                    # Everything related to connecting to and setting up MySQL
│   │   ├── 🐍 db_connector.py         
│   │   ├── 📄 schema.sql              
│   │   └── 📄 seed.sql                
│   ├── 📁 docs                        # Required documentation deliverables
│   │   ├── 📁 flowcharts              
│   │   ├── 📁 screenshots             
│   │   └── 📁 uml                     
│   ├── 📁 models                      # Plain data classes — no Tkinter, no SQL (the "M" in MVC)
│   │   ├── 🐍 appointment.py          
│   │   └── 🐍 user.py                 
│   ├── 📁 utils                       # Shared helper code used across the app
│   │   └── 🐍 exceptions.py           
│   ├── 📁 views                       # Tkinter/CustomTkinter windows only (the "V" in MVC)
│   │   ├── 📁 admin                   # Admin-only screens  
│   │   │   └── 🐍 admin_dashboard.py  
│   │   ├── 📁 doctor                  # Doctor-only screens
│   │   │   └── 🐍 doctor_dashboard.py 
│   │   ├── 📁 nurse                   # Nurse/Secretary-only screens
│   │   │   └── 🐍 nurse_dashboard.py  
│   │   ├── 📁 shared                  # Screens used by every role
│   │   │   └── 🐍 login_view.py       
│   │   └── 🐍 __init__.py
│   ├── 🐍 main.py                     # Entry point — run this on every client device
│   └── 📄 requirements.txt            # Python dependencies to install
├── 📝 CONTRIBUTING.md                 
├── 📝 DOCUMENTATION.md                 
└── 📝 README.md                       
```

---

*Final Project Instructions:*

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