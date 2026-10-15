# Security Policy

AppointMed manages patient, doctor, and appointment records in a shared MySQL database. Even as a coursework project, we treat security seriously and ask contributors to do the same.

## Supported Versions

AppointMed is under active development for the 2026–2027 academic year. Security fixes are applied to the latest version on the `main` branch only.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, pull requests, or group chats.**

Instead, report them privately:

1. Use GitHub's **Report a vulnerability** option under the repository's **Security** tab (private vulnerability reporting), or
2. Email the maintainers at **[add team contact email]** with the subject line `[SECURITY] AppointMed – <short description>`.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (affected endpoint, screen, or file).
- Any screenshots, logs, or proof-of-concept code, using fictional data only.
- Your suggested fix, if you have one.

### What to expect

- **Acknowledgment** within 3 days of your report.
- **Assessment and updates** within 7 days, including whether we accept the report.
- **Fix and disclosure:** accepted issues are fixed as quickly as practical, and we will credit you in the changelog if you wish.

If the report is declined, we will explain why.

## Security Practices in This Project

### Secrets and configuration

- Database credentials, JWT secrets, and other secrets live only in `main/.env`, which **must never be committed**. Keep `.env` listed in `.gitignore`.
- If a secret is ever committed or shared by mistake, treat it as compromised: rotate it immediately and tell the maintainers. Deleting the file in a later commit is not enough, since it remains in Git history.
- Change the default admin password from `seed.sql` before any real or shared use.

### Authentication and access control

- Passwords are stored only as salted hashes, never as plain text.
- API routes that need a login must use the permission dependencies in `backend/core/permissions.py`.
- Role checks (Admin, Doctor, Nurse/Secretary) are enforced **on the backend**. Hiding a button in the React UI is not a security measure.
- The unauthenticated `public_routes.py` endpoints used by the booking website must expose only what a patient needs to book (for example, available time slots) and never staff-only data or other patients' records.

### Data handling

- Use parameterized queries in all repositories. Never build SQL by concatenating user input.
- Validate all input with Pydantic schemas before it reaches the database.
- Do not return password hashes, internal errors, or stack traces in API responses. Use the exception handlers in `backend/core/exception_handlers.py`.
- Use only fictional or anonymized data in development, screenshots, documentation, and demos. Never commit real personal or medical information.

### Database

- Use a dedicated MySQL account for the application with only the privileges it needs, not `root`.
- Do not run `seed.sql` against a shared or production database. It is for development data.
- Restrict MySQL access to trusted machines on the clinic or team network.

### Dependencies

- Keep `requirements.txt` and `package.json` dependencies up to date, and review security alerts such as GitHub Dependabot.
- Add new dependencies only when needed, and prefer well-maintained packages.

## Scope

This policy covers the code in this repository: the FastAPI backend, the Electron desktop application, the public booking website, and the SQL scripts. Vulnerabilities in third-party tools (MySQL, Electron, Node.js, Python) should be reported to their respective maintainers.

Please do not test against systems you do not own, and do not access, modify, or delete data that is not yours while researching an issue.

---

*Last Updated: October 2026*