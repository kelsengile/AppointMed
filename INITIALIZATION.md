# INITIALIZATION

Python + Tkinter clinic appointment system with a shared MySQL backend,
so Doctor, Nurse/Secretary, and Admin accounts on different devices all
see the same live data.

**Folder structure**

```
AppointMed/main/
├── main.py
├── requirements.txt
├── config/
├── database/
├── models/
├── controllers/
├── views/
│   ├── shared/
│   ├── doctor/
│   ├── nurse/
│   └── admin/
├── utils/
├── assets/
└── docs/
```

**Setup**

1. `pip install -r main/requirements.txt`
2. Start/point to a MySQL server reachable by all client devices.
3. Run `database/schema.sql` against it once to create the tables.
4. Update `config/settings.py` with that server's host/credentials.
5. Run `python main.py` on each device (doctor, nurse, and admin machines
   all point at the same `DB_CONFIG`).

**Architecture**

MVC-ish split:
- **models/** — plain Python classes, no Tkinter or SQL
- **views/** — Tkinter windows only, one subfolder per role
- **controllers/** — validation + database calls, raises custom exceptions
  from `utils/exceptions.py` which the views catch and display