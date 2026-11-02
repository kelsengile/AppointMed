# Security Policy

AppointMed is a web-based system that manages patient, doctor, and appointment records in a shared MySQL database. It is a coursework project for CMSC 203, ITEC 104, and ITEC 105 at Laguna State Polytechnic University, and it is **not yet ready to hold real patient data**. Even so, we treat security seriously and ask contributors to do the same. This document explains how the system protects data today, where its known gaps are, and how to report a problem.

## Supported Versions

AppointMed is under active development for the 2026–2027 academic year. Security fixes are applied to the latest version on the `main` branch only.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, pull requests, or group chats.**

Instead, report them privately:

1. Use GitHub's **Report a vulnerability** option under the repository's **Security** tab (private vulnerability reporting), or
2. Email the maintainers at **[add team contact email]** with the subject line `[SECURITY] AppointMed – <short description>`.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (affected endpoint, page, or file, and the role you were using).
- Any screenshots, logs, or proof-of-concept code, using fictional data only.
- Your suggested fix, if you have one.

### What to expect

- **Acknowledgment** within 3 days of your report.
- **Assessment and updates** within 7 days, including whether we accept the report.
- **Fix and disclosure:** accepted issues are fixed as quickly as practical, and we will credit you in the changelog if you wish.

If the report is declined, we will explain why. For issues involving a team member's conduct rather than the code, follow the [Code of Conduct](CODE_OF_CONDUCT.md) instead.

## How AppointMed Protects Data Today

### Authentication

- Passwords are stored only as salted **bcrypt** hashes, never as plain text. New passwords must be 8 to 72 characters (72 is bcrypt's limit). Changing your own password requires the current one.
- A successful login returns a signed **JWT** (HS256) that expires after `JWT_EXPIRE_MINUTES` (default 480, or 8 hours). The signing key comes from `JWT_SECRET` in `source/.env`. The backend refuses to start without it and logs a warning if it is still the placeholder.
- On **every** request the backend reloads the user from the database and uses the stored role, not the role inside the token. Deactivating an account, or changing a user's role, takes effect immediately. Administrators cannot deactivate their own account.
- Login failures return one generic message ("Incorrect username or password") and are written to the audit log.
- Failed logins are limited to 5 per username every 5 minutes.

### Authorization

- Every protected route declares the feature it needs with `require_feature(...)`. The features each role may use are defined in one place, `backend/models/domain.py`.
- Role checks happen **on the backend**. Hiding a button or page in the React frontend is only a convenience, because anyone can call the API directly.
- Clinical data is scoped to a doctor. A doctor sees their own patients and appointments, and a nurse sees only those of the doctor they are assigned to. Services compare the record's doctor with the user's scope and answer "not found" for anything outside it. Administrators have no access to clinical records.

### Public booking endpoints

- The unauthenticated endpoints (`/api/public/catalog`, `/slots`, `/bookings`) expose only clinic information, doctor names, specializations, working weekdays, and open times. They never return staff-only data or other patients' records.
- A booking request is validated by Pydantic, must fall inside the booking window, and is rejected when an administrator switches online booking off. The server re-checks that the chosen time is a real open slot instead of trusting the browser.
- Successful bookings are limited to 6 per visitor IP every 10 minutes.
- A booking is only a **request**. Staff must approve it before it becomes an appointment.

### Input handling and the database

- Every request body is validated by Pydantic before it reaches a service. Text is trimmed and unknown fields are ignored.
- All SQL is parameterized and lives only in repositories. Column names for generic inserts and updates come from a fixed per-table whitelist.
- Multi-step changes run in a transaction, so they succeed or fail together. Double booking is also blocked inside MySQL by a unique index on a generated `active_slot` column.
- The app connects as `appointmed_user`, which has only `SELECT`, `INSERT`, `UPDATE`, and `DELETE` on the `appointmed` database. It cannot change the table structure, and it never connects as `root`.
- Users are deactivated rather than deleted. Patients with appointments, and rooms that appear in appointments, cannot be deleted, which protects the clinical history.
- Database errors are translated into generic messages. SQL text, driver details, stack traces, and password hashes are never returned. Unexpected errors return a plain "Something went wrong" and are logged on the server.
- Profile pictures are checked on the server: PNG, JPEG, or WebP only (identified from the file's first bytes, not the declared type), at most 300 KB. SVG is rejected.

### Frontend

- The login token is kept in `sessionStorage`, so it disappears when the tab closes, and it is sent as a `Bearer` header. When the server rejects a token, the app signs the user out.
- React escapes text by default, and the app does not render user-supplied text as raw HTML. Keep it that way.
- The dev server proxies `/api` to the backend, and `CORS_ORIGINS` lists the only browser origins the API accepts.

### Auditing

- Logins, failed logins, user and settings changes, request approvals and dismissals, check-ins, examinations, payments, and cancellations are written to `audit_logs` with the acting user. The app only ever adds rows. It never updates or deletes them, although its database account technically could.
- Audit entries must not contain passwords or medical details.

### Email

- Booking confirmations and disapprovals are sent through SMTP when `SMTP_HOST` is set (with STARTTLS by default). They contain the patient's name, the doctor, the time, and, for disapprovals, a reason typed by staff. **Staff must not put medical details in that reason.**
- When SMTP is not configured, the whole email, including the recipient address, is written to the backend log. Treat those logs as sensitive.

## Known Limitations

These gaps are known and are acceptable for a coursework demo, but each one must be addressed before any real use:

- **Rate limits are in memory.** They reset when the backend restarts, are not shared between server processes, and see only the proxy's address if the app runs behind a reverse proxy that is not configured to forward client addresses.
- **Login limiting is per username.** Anyone can lock a known account out for 5 minutes by failing five times. There is no CAPTCHA, multi-factor authentication, or password complexity rule beyond length.
- **Tokens cannot be revoked one by one.** Logging out only clears the browser. Deactivating the account is the way to cut off access before a token expires.
- **The token is readable by scripts on the page.** `sessionStorage` is exposed if cross-site scripting (XSS) ever happens, and no Content-Security-Policy header is set yet.
- **Public booking is open.** There is no CAPTCHA or email verification, so a confirmation can be sent to an address the sender does not own. Pending requests also hold their time slot until staff act on them, so a visitor can tie up slots (within the rate limit).
- **Interactive API docs and health endpoints are public.** `/docs` is on, and `/api/health/db` reports whether the database is reachable and its name.
- **No HTTPS in development,** and no data is encrypted at rest in MySQL.
- **No automated tests or dependency scanning yet.**
- **Compliance.** Real patient data is covered by laws such as the Philippine Data Privacy Act of 2012 (RA 10173). AppointMed has not been designed or reviewed to meet them.

## Before Any Real Deployment

Do all of these before putting the system in front of real users or data:

1. **Remove or replace every account from `seed.sql`.** The sample passwords are public. Never load `seed.sql` into a shared or production database.
2. Generate a fresh, random `JWT_SECRET`, use a strong password for `appointmed_user`, and set `APP_ENV` and `CORS_ORIGINS` for the real site (no wildcards).
3. Serve everything over **HTTPS** (for example behind a reverse proxy), and configure the proxy so the backend sees real client addresses.
4. Disable `/docs`, and add security headers, including a Content-Security-Policy.
5. Keep MySQL off the public internet, restrict it to trusted machines, and set up backups.
6. Move rate limiting to shared storage (for example Redis) if you run more than one backend process.
7. Configure SMTP with a dedicated account, and keep logs private.

## Rules for Contributors

- Keep secrets (database credentials, `JWT_SECRET`, SMTP passwords) only in `source/.env`, which **must never be committed**. Share only `source/.env.example`, which holds placeholders. If a secret is ever committed or shared by mistake, treat it as compromised: rotate it immediately and tell the maintainers. Deleting the file in a later commit is not enough, since it remains in Git history.
- Protect every new route with `require_feature(...)`, and keep clinical data inside the user's doctor scope.
- Use parameterized queries in repositories. Never build SQL by concatenating user input.
- Validate all input with Pydantic schemas before it reaches a service.
- Never return password hashes, internal errors, or stack traces in API responses.
- Do not log passwords, tokens, or medical details.
- Do not render user-supplied text as raw HTML in the frontend.
- Use only fictional or anonymized data in development, screenshots, documentation, and demos. Never commit real personal or medical information.
- Add dependencies only when needed, prefer well-maintained packages, and review security alerts such as GitHub Dependabot.

## Scope

This policy covers the code in this repository: the FastAPI backend, the React web frontend (including the public booking page), and the SQL scripts. Vulnerabilities in third-party tools (MySQL, Node.js, Python, browsers) should be reported to their respective maintainers.

Please do not test against systems you do not own, and do not access, modify, or delete data that is not yours while researching an issue.

---

*Last Updated: October 2026*