# gmail-calendar MCP server

A small MCP server (Python, [FastMCP](https://github.com/modelcontextprotocol/python-sdk), stdio transport) that gives an AI client safe access to your Gmail and Google Calendar.

## Tools

| Tool | What it does |
|---|---|
| `search_emails(query, max_results)` | Searches Gmail with Gmail search syntax and returns up to 50 results. |
| `read_email(message_id)` | Reads one message: its headers and plain-text body. |
| `create_draft(to, subject, body)` | Saves a **draft only**. It never sends. |
| `list_events(days_ahead)` | Lists upcoming primary-calendar events (1–90 days ahead). |
| `find_free_slots(date, duration_minutes)` | Finds free windows between 08:00 and 20:00 on a `YYYY-MM-DD` date. |
| `create_event(title, start, end, description)` | Creates an event. ISO 8601 times without an offset are treated as Asia/Jerusalem. No invites are sent. |

The server has **no tool that sends or deletes anything**. All times use the **Asia/Jerusalem** time zone.

## Credentials (reused, never copied)

The server reuses your existing OAuth files and reads them from where they already are:

- `token.json` is read from `GOOGLE_PRIVATE_DIR`
  (default: `C:\Users\Guy\.gemini\antigravity\scratch\gmail-calendar-agent`).
- `client_secret*.json` is only needed if `token.json` does not already contain the client ID and secret. The server looks in `GOOGLE_PRIVATE_DIR` first, then in `GOOGLE_CLIENT_SECRET_DIR` (default: `C:\Users\Guy\Downloads`).

Expired access tokens are refreshed **in memory** using the refresh token. Nothing is written to disk, no browser is opened and no secrets are logged. If the refresh token has been revoked or expired, re-authorize with your original agent script **outside** this server.

> If your OAuth consent screen is in **Testing** mode, Google expires refresh tokens after **7 days**, and you'll see `invalid_grant: Token has been expired or revoked`. Re-authorize outside this server, or publish the app to stop the 7-day expiry.

Each tool needs the matching OAuth scope in `token.json`:
- `gmail.readonly` (or `gmail.modify`) for searching and reading mail
- `gmail.compose` for creating drafts
- `calendar` (or `calendar.events`) for calendar tools

> Never copy `token.json`, `client_secret*.json`, `credentials.json` or `.env` into this folder. `.gitignore` blocks them anyway.

## Run

Requirements: [uv](https://docs.astral.sh/uv/) and Python 3.10 or later.

```powershell
cd C:\uoh\l06
uv sync                 # install dependencies into .venv
uv run server.py        # start the server on stdio (it waits for an MCP client)
```

To use a different private folder:

```powershell
$env:GOOGLE_PRIVATE_DIR = "D:\secrets\google"; uv run server.py
```

Test interactively with the MCP Inspector:

```powershell
uv run mcp dev server.py
```

## Add to an MCP client

Example configuration (Claude Desktop, Antigravity and similar clients):

```json
{
  "mcpServers": {
    "gmail-calendar": {
      "command": "uv",
      "args": ["--directory", "C:\\uoh\\l06", "run", "server.py"],
      "env": {
        "GOOGLE_PRIVATE_DIR": "C:\\Users\\Guy\\.gemini\\antigravity\\scratch\\gmail-calendar-agent"
      }
    }
  }
}
```

## Files

- `server.py`: the FastMCP server and tool definitions
- `google_auth.py`: loads and refreshes credentials (never opens a browser)
- `gmail_tools.py`: Gmail search, read and draft
- `calendar_tools.py`: Calendar list, free slots and create
