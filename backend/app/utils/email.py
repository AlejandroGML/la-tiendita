"""Transactional email utility — console logging (MVP) or SMTP delivery.

Uses Jinja2 FileSystemLoader to render HTML templates with i18n messages
loaded from JSON locale files matching the recipient's preferred language.
"""

import json
import logging
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

# Jinja2 environment: templates live under app/templates/
# The FileSystemLoader is rooted at the templates directory so that
# ``emails/password_reset.html`` resolves correctly and ``extends "base.html"``
# finds the base file in the parent directory.
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))


def _load_i18n_messages(lang: str) -> dict:
    """Load the i18n JSON dictionary for the given language code.

    Falls back to English if the requested locale file is missing.
    Returns an empty dict as a last resort so templates degrade gracefully.
    """
    i18n_dir = Path(__file__).resolve().parent.parent / "i18n"
    language_file = i18n_dir / f"{lang}.json"

    if language_file.is_file():
        try:
            return json.loads(language_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load i18n file %s: %s", language_file, exc)

    # Fallback to English
    en_file = i18n_dir / "en.json"
    if en_file.is_file():
        try:
            return json.loads(en_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load fallback i18n file: %s", exc)

    return {}


def render_template(name: str, **ctx) -> str:
    """Render a Jinja2 email template with i18n messages and context variables.

    Args:
        name: Template path relative to ``app/templates/``
              (e.g. ``"emails/password_reset.html"``).
        **ctx: Variables passed to the template (user_name, reset_link,
               order_id, lang, etc.). If ``lang`` is provided the corresponding
               locale JSON is loaded and injected as ``messages``.

    Returns:
        Rendered HTML string.
    """
    lang = ctx.get("lang", "en")
    messages = _load_i18n_messages(lang)
    template = _env.get_template(name)
    return template.render(messages=messages, **ctx)


def send_email(to: str, subject: str, html_body: str) -> None:
    """Send a transactional email.

    Behaviour depends on ``settings.EMAIL_MODE``:

    - ``"log"`` (default): writes the email content to the application log
      at INFO level — suitable for development and MVP.
    - ``"smtp"``: delivers via an SMTP relay using the configured
      credentials. SMTP errors are logged but NOT re-raised — email
      delivery is non-critical and should never block the caller.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        html_body: Rendered HTML body.
    """
    if settings.EMAIL_MODE == "smtp":
        _send_smtp(to, subject, html_body)
    else:
        logger.info(
            "EMAIL → %s | Subject: %s\n%s",
            to,
            subject,
            html_body,
        )


def _send_smtp(to: str, subject: str, html_body: str) -> None:
    """Deliver an email via SMTP using the configured credentials."""
    msg = MIMEText(html_body, "html", "utf-8")
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
            logger.info("SMTP email sent to %s", to)
    except smtplib.SMTPException as exc:
        logger.error("SMTP delivery failed for %s: %s", to, exc)
    except OSError as exc:
        logger.error("SMTP connection error for %s: %s", to, exc)
