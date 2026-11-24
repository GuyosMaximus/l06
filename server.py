"""gmail-calendar MCP server (FastMCP, stdio transport).

Exposes exactly six tools. None of them sends or deletes anything.
Never print to stdout here: stdout is the MCP protocol channel.
"""
import logging
import sys

from mcp.server.fastmcp import FastMCP

import calendar_tools
import gmail_tools

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

mcp = FastMCP("gmail-calendar")


@mcp.tool()
def search_emails(query: str, max_results: int = 10) -> list[dict]:
    """Search Gmail using Gmail search syntax (e.g. 'from:bob is:unread').
    Returns id, sender, subject, date and snippet for up to max_results (1-50) messages."""
    return gmail_tools.search_emails(query, max_results)


@mcp.tool()
def read_email(message_id: str) -> dict:
    """Read one Gmail message by its id: headers and plain-text body."""
    return gmail_tools.read_email(message_id)


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> dict:
    """Save a plain-text email as a Gmail DRAFT. It is never sent."""
    return gmail_tools.create_draft(to, subject, body)


@mcp.tool()
def list_events(days_ahead: int = 7) -> list[dict]:
    """List upcoming events on the primary Google Calendar from now
    through days_ahead days (1-90), in Asia/Jerusalem time."""
    return calendar_tools.list_events(days_ahead)


@mcp.tool()
def find_free_slots(date: str, duration_minutes: int = 30) -> dict:
    """Find free time windows of at least duration_minutes on a date (YYYY-MM-DD),
    within 08:00-20:00 Asia/Jerusalem, based on the primary calendar."""
    return calendar_tools.find_free_slots(date, duration_minutes)


@mcp.tool()
def create_event(title: str, start: str, end: str, description: str = "") -> dict:
    """Create an event on the primary Google Calendar. start/end are ISO 8601
    (e.g. 2026-11-25T14:00); times without an offset are Asia/Jerusalem.
    No invitations are emailed."""
    return calendar_tools.create_event(title, start, end, description)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
