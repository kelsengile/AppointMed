import smtplib, ssl
from email.message import EmailMessage
from backend.core.config import settings as s
from backend.core.mailer import mailer, LOGO_PATH
from backend.core.email_templates import render_email

print("logo exists:", LOGO_PATH.is_file(), "| size KB:", LOGO_PATH.stat().st_size // 1024 if LOGO_PATH.is_file() else "-")

def send(label, message):
    try:
        ctx = ssl.create_default_context()
        server = smtplib.SMTP(s.smtp_host, 587, timeout=30)
        server.ehlo(); server.starttls(context=ctx); server.ehlo()
        server.login(s.smtp_user, s.smtp_password.replace(" ", ""))
        server.send_message(message)
        server.quit()
        print(label, "-> OK")
    except Exception as e:
        print(label, "-> FAILED:", type(e).__name__, e)

# 1) plain text only
m = EmailMessage()
m["From"] = s.smtp_user; m["To"] = s.smtp_user; m["Subject"] = "Plain test"
m.set_content("plain text test")
send("plain text", m)

# 2) the app's real email (HTML + embedded logo)
text, html = render_email(clinic="Test", heading="Test", paragraphs=["Hello"])
msg = mailer._build(s.smtp_user, "Real layout test", text, html)
print("message size KB:", len(msg.as_bytes()) // 1024)
send("app email (html + logo)", msg)

# 3) the app's HTML without the logo
m3 = EmailMessage()
m3["From"] = s.smtp_user; m3["To"] = s.smtp_user; m3["Subject"] = "HTML no logo"
m3.set_content(text); m3.add_alternative(html, subtype="html")
send("html without logo", m3)