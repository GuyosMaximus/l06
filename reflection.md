# Reflection: L06

## What did we ask the agent?

- List tomorrow's calendar events (`list_events`).
- Create a Gmail draft (`"L06 test"`) and schedule a calendar event (`"MCP works"`) 4 hours from now.
- Find a free hour tomorrow between 09:00 and 17:00 (`find_free_slots`) and schedule `"Study group"`.
- Attempt to send the draft and delete the event to verify safety boundaries.
- Act as a meeting coordinator: read an incoming meeting request email, check calendar availability, and prepare a reply draft proposing two alternative free slots without sending it.

## How did we check that the result is correct?

- Checked **Gmail -> Drafts** directly to verify both drafts (`"L06 test"` and the meeting reply) were saved and never sent.
- Checked **Google Calendar** to verify events (`"MCP works"` and `"Study group"`) were created at the exact expected times in `Asia/Jerusalem` timezone, and that no conflicting event was created when the slot was busy.
- Confirmed the agent refused to send emails or delete events and did not create workaround Python scripts in the workspace.

## Which tool did we leave out, and why?

- We intentionally left out any **email sending tool** (`send_email`) and any **event deletion/modification tool** (`delete_event` / `update_event`).
- **Why:** To enforce **Human-in-the-Loop** safety and prevent irreversible actions or prompt-injection attacks from incoming emails. The agent prepares drafts only, leaving final review and sending strictly to the user.

## L05 vs L06: what changed?

- **New request:** In L05, every new task required writing a dedicated Python script (`main.py`); in L06, we reuse the same MCP server and simply give natural-language prompts with zero new code.
- **Who chooses the steps:** In L05, hardcoded Python logic dictated the workflow; in L06, the LLM dynamically selects which MCP tools to call and in what order.
- **Checking availability:** In L05, the script did not check for calendar conflicts; in L06, the agent automatically calls `find_free_slots` / `list_events` before scheduling.
