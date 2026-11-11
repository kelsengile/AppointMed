"""Reusable responsive HTML and plain-text email layout."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence

FONT = "Poppins,'Segoe UI',Helvetica,Arial,sans-serif"
NAVY = "#1F3655"
BRAND = "#365983"
BRAND_LIGHT = "#527DAA"
BODY = "#355882"
MUTED = "#5079A7"
SOFT = "#8A9BB5"
PAGE = "#EAF4FC"
PANEL = "#F4F9FE"
LINE = "#DCE9FB"

TONES: dict[str, tuple[str, str, str]] = {
    "blue": ("#EFF5FE", "#BBD4F3", "#06408F"),
    "green": ("#ECFDF5", "#A7F3D0", "#065F46"),
    "amber": ("#FFFBEB", "#FDE68A", "#92400E"),
    "red": ("#FEF2F2", "#FECACA", "#991B1B"),
}

DEFAULT_FOOTER = "This is an automated message. Please do not reply to this email."


@dataclass(frozen=True)
class Button:
    """A call-to-action link shown as the blue gradient button."""

    label: str
    url: str


def _text(value: object) -> str:
    """Escape a value and keep its line breaks."""
    return escape(str(value)).replace("\n", "<br>")


def render_email(
    *,
    clinic: str,
    heading: str,
    greeting: str | None = None,
    paragraphs: Sequence[str] = (),
    badge: str | None = None,
    tone: str = "blue",
    details: Sequence[tuple[str, str]] = (),
    note: str | None = None,
    button: Button | None = None,
    footer: str | None = None,
    preheader: str | None = None,
) -> tuple[str, str]:
    """Build one email. Returns (plain_text, html)."""
    bg, border, ink = TONES.get(tone, TONES["blue"])
    footer_text = footer or DEFAULT_FOOTER
    hidden = (preheader or (paragraphs[0] if paragraphs else heading))[:140]

    body: list[str] = []
    if badge:
        body.append(
            f'<div style="margin:0 0 14px;"><span style="display:inline-block;padding:5px 14px;border-radius:999px;'
            f"background:{bg};border:1px solid {border};color:{ink};font-size:12px;font-weight:700;"
            f'letter-spacing:0.04em;text-transform:uppercase;">{escape(badge)}</span></div>'
        )
    body.append(f'<h1 style="margin:0;font-size:24px;line-height:1.3;font-weight:800;color:{NAVY};">{escape(heading)}</h1>')
    if greeting:
        body.append(f'<p style="margin:18px 0 0;font-size:15px;line-height:1.65;font-weight:600;color:{BODY};">{_text(greeting)}</p>')
    for paragraph in paragraphs:
        body.append(f'<p style="margin:14px 0 0;font-size:15px;line-height:1.65;color:{BODY};">{_text(paragraph)}</p>')

    if details:
        rows = []
        for index, (label, value) in enumerate(details):
            top = "" if index == 0 else f"border-top:1px solid {LINE};"
            rows.append(
                f'<tr><td valign="top" width="38%" style="padding:11px 12px 11px 0;{top}font-size:12px;font-weight:700;'
                f'letter-spacing:0.04em;text-transform:uppercase;color:{MUTED};">{escape(label)}</td>'
                f'<td valign="top" style="padding:11px 0;{top}font-size:15px;font-weight:600;color:{NAVY};">{_text(value)}</td></tr>'
            )
        body.append(
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:22px;background:{PANEL};'
            f'border:1px solid {LINE};border-radius:16px;"><tr><td style="padding:6px 20px;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table></td></tr></table>'
        )

    if note:
        body.append(
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;"><tr>'
            f'<td style="padding:14px 16px;background:{bg};border-left:4px solid {ink};border-radius:12px;'
            f'font-size:14px;line-height:1.6;color:{ink};">{_text(note)}</td></tr></table>'
        )

    if button:
        body.append(
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:28px;"><tr>'
            f'<td align="center" bgcolor="{BRAND}" style="border-radius:12px;background:{BRAND};'
            f'background-image:linear-gradient(90deg,{BRAND},{BRAND_LIGHT});">'
            f'<a href="{escape(button.url, quote=True)}" style="display:inline-block;padding:13px 28px;font-size:15px;'
            f'font-weight:700;color:#ffffff;text-decoration:none;border-radius:12px;">{escape(button.label)}</a></td></tr></table>'
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{escape(heading)}</title>
</head>
<body style="margin:0;padding:0;background:{PAGE};font-family:{FONT};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{PAGE};">{escape(hidden)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAGE};">
<tr><td align="center" style="padding:28px 12px;">
  <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;">
    <tr><td style="padding:0 6px 14px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
        <td width="40" height="40" align="center" bgcolor="{BRAND}" style="width:40px;height:40px;border-radius:12px;background:{BRAND};background-image:linear-gradient(135deg,{BRAND},{BRAND_LIGHT});color:#ffffff;font-size:20px;font-weight:800;line-height:40px;">A</td>
        <td style="padding-left:12px;font-size:20px;font-weight:800;color:{NAVY};letter-spacing:-0.01em;">AppointMed</td>
        <td align="right" style="font-size:12px;font-weight:600;color:{MUTED};">{escape(clinic)}</td>
      </tr></table>
    </td></tr>
    <tr><td style="background:#ffffff;border:1px solid {LINE};border-radius:24px;overflow:hidden;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr><td height="6" bgcolor="{BRAND}" style="height:6px;line-height:6px;font-size:0;background:{BRAND};background-image:linear-gradient(90deg,{BRAND},{BRAND_LIGHT});">&nbsp;</td></tr>
        <tr><td style="padding:32px 32px 34px;">{"".join(body)}</td></tr>
      </table>
    </td></tr>
    <tr><td align="center" style="padding:18px 16px 0;font-size:12px;line-height:1.6;color:{SOFT};">
      {_text(footer_text)}<br>&copy; {escape(clinic)}
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>"""

    lines: list[str] = []
    if greeting:
        lines += [greeting, ""]
    lines += [heading, ""]
    for paragraph in paragraphs:
        lines += [paragraph, ""]
    if details:
        lines += [f"{label}: {value}" for label, value in details] + [""]
    if note:
        lines += [note, ""]
    if button:
        lines += [f"{button.label}: {button.url}", ""]
    lines += ["--", footer_text, clinic]
    return "\n".join(lines), html
