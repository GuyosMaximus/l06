"""Read-only Gmail helpers plus draft creation. Nothing here sends or deletes."""
import base64
import html
import re
from email.message import EmailMessage

from google_auth import gmail_service

MAX_BODY_CHARS = 20000


def _headers(payload: dict) -> dict:
    wanted = {"from", "to", "cc", "subject", "date"}
    return {h["name"].lower(): h["value"] for h in payload.get("headers", [])
            if h["name"].lower() in wanted}


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")


def _find_part(payload: dict, mime: str) -> str | None:
    if payload.get("mimeType") == mime and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    for part in payload.get("parts", []) or []:
        found = _find_part(part, mime)
        if found:
            return found
    return None


def _html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def search_emails(query: str, max_results: int = 10) -> list[dict]:
    max_results = max(1, min(int(max_results), 50))
    svc = gmail_service()
    resp = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    results = []
    for ref in resp.get("messages", []):
        msg = svc.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        h = _headers(msg.get("payload", {}))
        results.append({
            "id": msg["id"],
            "thread_id": msg.get("threadId"),
            "from": h.get("from", ""),
            "subject": h.get("subject", ""),
            "date": h.get("date", ""),
            "snippet": html.unescape(msg.get("snippet", "")),
        })
    return results


def read_email(message_id: str) -> dict:
    svc = gmail_service()
    msg = svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    payload = msg.get("payload", {})
    body = _find_part(payload, "text/plain")
    if body is None:
        html_body = _find_part(payload, "text/html")
        body = _html_to_text(html_body) if html_body else msg.get("snippet", "")
    truncated = len(body) > MAX_BODY_CHARS
    return {
        "id": msg["id"],
        "thread_id": msg.get("threadId"),
        "labels": msg.get("labelIds", []),
        **_headers(payload),
        "body": body[:MAX_BODY_CHARS],
        "truncated": truncated,
    }


def create_draft(to: str, subject: str, body: str) -> dict:
    mail = EmailMessage()
    mail["To"] = to
    mail["Subject"] = subject
    mail.set_content(body)
    raw = base64.urlsafe_b64encode(mail.as_bytes()).decode()
    draft = gmail_service().users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()
    return {
        "draft_id": draft["id"],
        "message_id": draft.get("message", {}).get("id"),
        "status": "Draft saved. It was NOT sent; review it in Gmail Drafts.",
    }
