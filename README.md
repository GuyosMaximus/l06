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
- `reflection.md`: lesson reflection

## Prompts used in the session (2026-11-24)

These are the prompts we gave the agent, in order, while it was connected to this MCP server:

1. What do I have in my calendar tomorrow?
2. Write a Gmail draft to myself with the subject "L06 test" and add a calendar event for today, 4 hours from now, called "MCP works".
3. Find a free hour tomorrow between 09:00 and 17:00 and add an event called "Study group" there.
4. Great. Now send the "L06 test" draft. *(The agent refused: the server has no send tool.)*
5. Delete the "Study group" event. *(The agent refused: the server has no delete tool.)*
6. Initialize a git repository in this folder. Before the first commit, show me git status and confirm that no token.json, client_secret*.json or .env file will be committed. Then commit with the message "L06 gmail-calendar MCP server".
7. Push this git repository to https://github.com/GuyosMaximus/l06.git
8. Retry git push -u origin master
9. Act as my meeting coordinator. Find the latest meeting request in my email. Check my calendar for that time. If I am free, create the event and prepare a reply draft confirming it. If I am busy, do not create an event; prepare a reply draft that suggests two free times. Never send anything. Show me what you did, step by step.
10. Create reflection.md with four empty sections: "What did we ask the agent?", "How did we check that the result is correct?", "Which tool did we leave out, and why?", "L05 vs L06: what changed?". Also add to README.md the list of prompts we used today. Then commit.
