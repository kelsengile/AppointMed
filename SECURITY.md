# Security Policy

AppointMed is a web-based system that manages patient, doctor, and appointment records in a shared MySQL database. It is a coursework project for CMSC 203, ITEC 104, and ITEC 105 at Laguna State Polytechnic University, and it is **not yet ready to hold real patient data**. Even so, we treat security seriously and ask contributors to do the same. This document explains how the system protects data today, where its known gaps are, and how to report a problem. The reasoning behind the main controls (hashing, validation, credentials, privacy) is explained in [NOTES.md](NOTES.md).

## Supported Versions

AppointMed is under active development for the 2026–2027 academic year. Security fixes are applied to the latest version on the `main` branch only.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, pull requests, or group chats.**

Report them privately:

1. Use GitHub's **Report a vulnerability** option under the repository's **Security** tab (private vulnerability reporting), or
2. Email the maintainers at **[add team contact email]** with the subject `[SECURITY] AppointMed – <short description>`.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce it (endpoint, page, or file, and the role you were using).
- Screenshots, logs, or proof-of-concept code, using fictional data only.
- Your suggested fix, if you have one.

### What to expect

- **Acknowledgment** within 3 days.
- **Assessment and updates** within 7 days, including whether we accept the report.
- **Fix and disclosure:** accepted issues are fixed as quickly as practical, and we will credit you in the changelog if you wish.

If the report is declined, we will explain why. For issues about a team member's conduct rather than the code, follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## How AppointMed Protects Data Today

### Authentication

- Passwords are stored only as salted **bcrypt** hashes, never as plain text.
- New passwords (change, reset, or new user) must be 8 to 72 bytes and contain an uppercase letter, a lowercase letter, a number, and a special character. Changing your own password requires the current one and a different new one. (The public sample passwords predate this rule and still work for login.)
- A successful login returns a signed **JWT** (HS256) that expires after `JWT_EXPIRE_MINUTES` (default 480). The signing key comes from `JWT_SECRET` in `source/.env`. The backend refuses to start without it and warns if it is still the placeholder.
- On **every** request the backend reloads the user from the database and uses the stored role, not the role in the token. Deactivating an account or changing a role takes effect immediately. Administrators cannot deactivate their own account.
- Login failures return one generic message and are written to the audit log. For an unknown username the server still checks a dummy hash, so response time does not reveal which usernames exist.
- Failed logins are limited to 5 per username every 5 minutes.

### Authorization

- Every protected route declares its feature with `require_feature(...)`. The features of each role are defined in one place, `backend/models/domain.py`. Marking days off needs the doctor-only `schedule` feature, and the Database page needs the admin-only `database` feature.
- Role checks happen **on the backend**. Hiding a button in the React frontend is only a convenience.
- Clinical data is scoped to a doctor. A doctor sees their own patients and appointments, and a nurse sees only those of the assigned doctor. Records outside the scope answer "not found". Administrators have no access to clinical records through the normal API.

### Public endpoints

- The unauthenticated endpoints (`/api/public/catalog`, `/departments`, `/staff`, `/slots`, `/calendar`, `/bookings`) expose only clinic information, department text, staff **names, roles, specializations, supported doctor names, and working weekdays**, open times, and the **dates** a doctor is unavailable. They never return clinical data, contact details, usernames, emails, or the reasons for days off.
- A booking request is validated by Pydantic, must fall inside the booking window, and is rejected when online booking is off. The server re-checks that the time is a real open slot (not a day off, not taken) under a lock on the doctor's row.
- Successful bookings are limited to 6 per visitor IP every 10 minutes.
- A booking is only a **request**. Staff must approve it.

### Input handling and the database

- Every request body is validated on the server by Pydantic before it reaches a service: types, lengths, ranges, character allowlists for names, addresses, medicine text, and room names, control characters refused, no time zones in times, and valid money values. Text is trimmed and unknown fields are ignored. The frontend filters the same characters while typing, but is never trusted.
- All SQL is parameterized and lives only in repositories. Column names for generic inserts and updates come from a fixed per-table whitelist.
- Multi-step changes run in a transaction. Double booking is blocked inside MySQL by a unique index on a generated `active_slot` column, and exam starts, days off, and bookings for one doctor are serialized with a row lock.
- The app connects as `appointmed_user` with only `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on `appointmed`. It cannot change the table structure, and it never connects as `root`.
- Users are deactivated rather than deleted. Patients and rooms with appointments cannot be deleted.
- Database errors become generic messages. SQL text, driver details, stack traces, and password hashes are never returned to patients and staff. Unexpected errors return a plain "Something went wrong" and are logged on the server.
- Profile pictures: PNG, JPEG, or WebP only (identified from the file's first bytes), at most 300 KB. SVG is rejected.

### Admin Database page

The Database page gives an administrator powerful tools, so it has its own controls:

- Only users with the `database` feature (Admin) can reach it, and every action is written to the audit log (`DB_INSERT_ROW`, `DB_UPDATE_ROW`, `DB_DELETE_ROW`, `DB_RUN_SQL`, `BACKUP_DATABASE`, `RESTORE_DATABASE`) with the table name and counts, **never the values**.
- `password_hash` and `avatar` columns are never sent to the browser. The audit log is read-only, and statements that write to it are refused. New accounts cannot be inserted here (they must be created on the Users page so the password is hashed). Admins cannot change their own role or active status or delete their own account.
- Table and column names are checked against `information_schema`. Values are parameters. The console accepts one statement, only `SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`, `INSERT`, `UPDATE`, or `DELETE`, requires a `WHERE` for `UPDATE` and `DELETE`, limits reads to 5 seconds and 500 rows.
- **Backups contain every table, including password hashes and patient data.** They are returned only to an administrator, in a file named with the date. Treat them like a secret.
- **Import** never executes the file as SQL. It parses a fixed set of statements, checks that the tables and columns match, replaces the rows in one transaction (the audit log is kept), and refuses to finish unless the importing administrator's own account survives.

### Frontend

- The login token is kept in `sessionStorage`, so it disappears when the tab closes, and it is sent as a `Bearer` header. When the server rejects a token, the app signs the user out.
- "Remember me" stores only the **username** in `localStorage`. Passwords and tokens are never stored there.
- React escapes text by default, and the app does not render user-supplied text as raw HTML. Keep it that way.
- CSV downloads neutralize cells that start with `= + - @`.
- The dev server proxies `/api` to the backend, and `CORS_ORIGINS` lists the only browser origins the API accepts.

### Auditing

- Logins, failed logins, user and settings changes, request approvals and dismissals, check-ins, examinations, payments, cancellations, days off, and Database page actions are written to `audit_logs` with the acting user. The app only ever adds rows.
- Audit entries must not contain passwords or medical details.

### Email

- Booking confirmations and disapprovals are sent through SMTP when `SMTP_HOST` is set (STARTTLS by default). They contain the patient's name, the doctor, the time, and, for disapprovals, a reason typed by staff. **Staff must not put medical details in that reason.**
- When SMTP is not configured, the whole email, including the recipient address, is written to the backend log. Treat those logs as sensitive.

## Known Limitations

These gaps are acceptable for a coursework demo, but each must be addressed before any real use:

- **Rate limits are in memory.** They reset when the backend restarts, are not shared between processes, and see only the proxy's address behind a reverse proxy that does not forward client addresses.
- **Login limiting is per username.** Anyone can lock a known account out for 5 minutes by failing five times. There is no CAPTCHA or multi-factor authentication.
- **Tokens cannot be revoked one by one.** Logging out only clears the browser. Deactivating the account cuts off access before a token expires.
- **The token is readable by scripts on the page.** `sessionStorage` is exposed if cross-site scripting (XSS) ever happens, and no Content-Security-Policy header is set yet.
- **Public booking is open.** There is no CAPTCHA or email verification, so a confirmation can be sent to an address the sender does not own. Pending requests hold their slot until staff act, so a visitor can tie up slots (within the rate limit).
- **The public staff list shows every active account,** including nurses, administrators, and which doctor a nurse supports. Remove roles you do not want public from `StaffDirectoryRepository`.
- **The SQL console and backups are very powerful.** An administrator can change most tables (including `users`), and the console hides hash columns only by result-column name (an alias can reveal one). Backups include password hashes. Limit these to trusted administrators, or disable the Database page outside development.
- **Interactive API docs and health endpoints are public.** `/docs` is on, and `/api/health/db` reports whether the database is reachable and its name.
- **No HTTPS in development,** and no data is encrypted at rest in MySQL. The database password sits in plain text in `source/.env`.
- **No automated tests or dependency scanning yet.**
- **Compliance.** Real patient data is covered by laws such as the Philippine Data Privacy Act of 2012 (RA 10173). AppointMed has not been reviewed to meet them (see "Respect Data Privacy" in [NOTES.md](NOTES.md)).

## Before Any Real Deployment

1. **Remove or replace every account from `seed.sql`.** The sample passwords are public. Never load `seed.sql` into a shared or production database.
2. Generate a fresh, random `JWT_SECRET`, use a strong password for `appointmed_user`, and set `APP_ENV` and `CORS_ORIGINS` for the real site (no wildcards).
3. Serve everything over **HTTPS** (for example behind a reverse proxy) and make the backend see real client addresses.
4. Disable `/docs`, add security headers including a Content-Security-Policy, and consider turning off the Database page.
5. Keep MySQL off the public internet, restrict it to trusted machines, enable encryption at rest, and set up encrypted backups.
6. Move rate limiting to shared storage (for example Redis) if you run more than one backend process.
7. Configure SMTP with a dedicated account, and keep logs private.
8. Review the data privacy checklist in [NOTES.md](NOTES.md) with a qualified adviser.

## Rules for Contributors

- Keep secrets (database credentials, `JWT_SECRET`, SMTP passwords) only in `source/.env`, which **must never be committed**. Share only `source/.env.example`, which holds placeholders. If a secret is committed or shared by mistake, treat it as compromised: rotate it and tell the maintainers. Deleting the file in a later commit is not enough, since it stays in Git history.
- Never commit a database backup or dump. It contains password hashes and records.
- Protect every new route with `require_feature(...)`, and keep clinical data inside the user's doctor scope.
- Use parameterized queries in repositories. Never build SQL by concatenating user input.
- Validate all input with Pydantic schemas on the server before it reaches a service.
- Hash passwords with `hash_password`. Never return password hashes, internal errors, or stack traces in API responses.
- Do not log passwords, tokens, or medical details.
- Do not render user-supplied text as raw HTML in the frontend.
- Use only fictional or anonymized data in development, screenshots, documentation, and demos.
- Add dependencies only when needed, prefer well-maintained packages, and review security alerts such as GitHub Dependabot.

## Scope

This policy covers the code in this repository: the FastAPI backend, the React web frontend (including the public pages), the SQL scripts, and the `dev.py` console. Vulnerabilities in third-party tools (MySQL, Node.js, Python, browsers) should be reported to their maintainers.

Please do not test against systems you do not own, and do not access, modify, or delete data that is not yours while researching an issue.

---

*Last Updated: November 2026*