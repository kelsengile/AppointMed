# Security Policy

AppointMed is a web-based system that manages patient, doctor, and appointment records in a shared MySQL database. Even as a coursework project, we treat security seriously and ask contributors to do the same.

## Supported Versions

AppointMed is under active development for the 2026–2027 academic year. Security fixes are applied to the latest version on the `main` branch only.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues, pull requests, or group chats.**

Instead, report them privately:

1. Use GitHub's **Report a vulnerability** option under the repository's **Security** tab (private vulnerability reporting), or
2. Email the maintainers at **[add team contact email]** with the subject line `[SECURITY] AppointMed – <short description>`.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (affected endpoint, page, or file).
- Any screenshots, logs, or proof-of-concept code, using fictional data only.
- Your suggested fix, if you have one.

### What to expect

- **Acknowledgment** within 3 days of your report.
- **Assessment and updates** within 7 days, including whether we accept the report.
- **Fix and disclosure:** accepted issues are fixed as quickly as practical, and we will credit you in the changelog if you wish.

If the report is declined, we will explain why.

## Security Practices in This Project

### Secrets and configuration

- Database credentials, JWT secrets, and other secrets live only in `source/.env`, which **must never be committed**. Keep it listed in `.gitignore`. Share only `source/.env.example`, which holds placeholders.
- If a secret is ever committed or shared by mistake, treat it as compromised: rotate it immediately and tell the maintainers. Deleting the file in a later commit is not enough, since it remains in Git history.
- Change the default admin password from `seed.sql` before any real or shared use.

### Authentication and access control

- Passwords are stored only as salted hashes, never as plain text.
- API routes that need a login must use the shared permission checks in the backend.
- Role checks (Admin, Doctor, Nurse) are enforced **on the backend**. Hiding a button or page in the React frontend is not a security measure, because anyone can call the API directly.
- The unauthenticated endpoints used by the public booking page must expose only what a patient needs to book (for example, available time slots) and never staff-only data or other patients' records.

### Web-specific practices

- Configure `CORS_ORIGINS` to list only the origins that host the frontend. Do not use a wildcard in production.
- Serve the site over HTTPS in any real deployment, so logins and tokens are not sent in plain text.
- Do not store login tokens anywhere that scripts from other sites can read, and keep tokens short-lived.
- Rate-limit or otherwise protect the public booking endpoint against spam and abuse.
- Do not render user-supplied text as raw HTML in the frontend.

### Data handling

- Use parameterized queries in all database code. Never build SQL by concatenating user input.
- Validate all input with Pydantic schemas before it reaches the database.
- Do not return password hashes, internal errors, or stack traces in API responses. The `/api/health/db` endpoint, for example, reports only whether the database is reachable, never why it is not.
- Use only fictional or anonymized data in development, screenshots, documentation, and demos. Never commit real personal or medical information.

### Database

- Use a dedicated MySQL account for the application with only the privileges it needs, not `root`.
- Do not run `seed.sql` against a shared or production database. It is for development data.
- Restrict MySQL access to trusted machines on the clinic or team network.

### Dependencies

- Keep `requirements.txt` and `package.json` dependencies up to date, and review security alerts such as GitHub Dependabot.
- Add new dependencies only when needed, and prefer well-maintained packages.

## Scope

This policy covers the code in this repository: the FastAPI backend, the React web frontend (including the public booking page), and the SQL scripts. Vulnerabilities in third-party tools (MySQL, Node.js, Python, browsers) should be reported to their respective maintainers.

Please do not test against systems you do not own, and do not access, modify, or delete data that is not yours while researching an issue.

---

*Last Updated: October 2026*
