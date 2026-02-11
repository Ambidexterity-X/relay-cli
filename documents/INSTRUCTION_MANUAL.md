# Instruction Manual: Build `relay`

**For:** Claude Opus 4.5  
**Task:** Build a fully working CLI chat application called `relay` from scratch.  
**Stack:** Python, Typer, Supabase (Auth + Postgres + Realtime), Rich  
**Environment:** WSL (Ubuntu), Python Virtual Environment

---

## Overview

You are building `relay` — a terminal-based multi-user chat app. Users can register, log in, create rooms, and chat with other users in real time. Messages are delivered via Supabase Realtime (WebSockets). The CLI is powered by Typer and output is rendered with Rich.

Read this entire document before writing any code.

---

## Constraints & Rules

- **Do not hallucinate APIs.** Only use Supabase Python SDK methods that actually exist. When in doubt, use simple REST-style calls via `supabase.table().select()` etc.
- **Do not use deprecated methods.** The Supabase Python SDK v2 uses `supabase.auth.sign_in_with_password()`, not `sign_in()`.
- **Always handle errors.** Every Supabase call can fail. Wrap calls in try/except and show the user a friendly message.
- **Never crash with a raw traceback.** All exceptions should be caught at the command level.
- **Keep files focused.** Each module has a single responsibility. Do not put auth logic in `chat.py`, etc.
- **Do not use threads.** Use `asyncio` for the concurrent input/listen loop in `chat.py`.
- **Do not hardcode credentials.** All secrets come from `.env`.

---

## Environment Setup

The user is running WSL with Python's virtual environment. The virtual environment is named `venv` and uses Python 3.11. Dependencies are installed via pip inside the virtual environment.

**Dependencies:**
```
supabase>=2.0.0
typer>=0.12.0
rich>=13.0.0
python-dotenv>=1.0.0
```

**`pyproject.toml` entry point:**
```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:BuildBackend"

[project]
name = "relay"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "supabase>=2.0.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
relay = "app.main:app"
```

Install in editable mode with:
```bash
pip install -e .
```

---

## Project Structure

Create exactly this structure — no more, no less:

```
relay/
├── app/
│   ├── __init__.py         # empty
│   ├── main.py             # Typer app entry point
│   ├── auth.py             # register, login, logout commands
│   ├── rooms.py            # rooms list & create commands
│   ├── chat.py             # join command + async chat loop
│   ├── supabase_client.py  # initializes Supabase client
│   └── session.py          # reads/writes session to .env
├── .env                    # created by user, not by code
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## The `.env` File

The user will create this manually after setting up their Supabase project. Your code must read from it. Never write `SUPABASE_URL` or `SUPABASE_KEY` — only write/clear the session fields.

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key

SUPABASE_ACCESS_TOKEN=
SUPABASE_REFRESH_TOKEN=
SUPABASE_USER_ID=
```

---

## Module Specifications

### `session.py`

Responsible for reading and writing session tokens to `.env`.

**Functions to implement:**

```python
def load_session() -> dict:
    """
    Reads .env and returns a dict with keys:
    access_token, refresh_token, user_id
    Returns empty strings for missing values.
    """

def save_session(access_token: str, refresh_token: str, user_id: str) -> None:
    """
    Writes session fields to .env using python-dotenv's set_key().
    Does not touch SUPABASE_URL or SUPABASE_KEY.
    """

def clear_session() -> None:
    """
    Clears access_token, refresh_token, user_id from .env by setting them to "".
    """

def is_logged_in() -> bool:
    """
    Returns True if access_token is present and non-empty in .env.
    """
```

Use `dotenv.set_key(dotenv_path, key, value)` for writing. Use `dotenv.dotenv_values()` for reading.

---

### `supabase_client.py`

Initializes and returns a Supabase client, optionally authenticated with a session.

```python
def get_client() -> Client:
    """
    Loads SUPABASE_URL and SUPABASE_KEY from .env.
    Creates a Supabase client.
    If a session exists in .env, sets the session on the client using
    supabase.auth.set_session(access_token, refresh_token).
    Returns the client.
    """
```

Always call `get_client()` at the start of every command function. Never create a global client at import time — this ensures the session is always fresh.

---

### `auth.py`

Contains three Typer commands: `register`, `login`, `logout`.

**`register` command:**
1. Prompt for email, password (hidden), and username using `typer.prompt()`.
2. Call `supabase.auth.sign_up({"email": email, "password": password})`.
3. On success, insert a row into `profiles`: `{"id": user.id, "username": username}`.
4. Call `save_session()` with the returned tokens.
5. Print a success message with Rich.
6. Handle errors: duplicate email, duplicate username (unique constraint), network errors.

**`login` command:**
1. Prompt for email and password.
2. Call `supabase.auth.sign_in_with_password({"email": email, "password": password})`.
3. On success, call `save_session()`.
4. Print a success message.
5. Handle errors: invalid credentials.

**`logout` command:**
1. Check `is_logged_in()` — if not logged in, tell the user and return.
2. Call `supabase.auth.sign_out()`.
3. Call `clear_session()`.
4. Print a confirmation message.

---

### `rooms.py`

Contains two commands: `list_rooms` (the default `rooms` command) and `create`.

**`list_rooms` command:**
1. Check `is_logged_in()` — redirect to login if not.
2. Query `rooms` table, joining with `profiles` to get creator username. Order by `created_at` ascending.
3. Render results as a Rich `Table` with columns: Name, Created By, Created At.
4. If no rooms exist, print a helpful message.

**`create` command:**
1. Check `is_logged_in()`.
2. Prompt for a room name.
3. Insert into `rooms`: `{"name": name, "created_by": user_id}`.
4. Handle unique constraint errors (room name taken).
5. Print confirmation.

---

### `chat.py`

This is the most complex module. It contains the `join` command and the async chat loop.

**`join` command:**

```python
def join(room_name: str = typer.Argument(..., help="Name of the room to join")):
```

**Step 1 — Auth check:**
Check `is_logged_in()`. If not, redirect and return.

**Step 2 — Look up room:**
Query `rooms` table where `name = room_name`. If not found, print error and return.

**Step 3 — Fetch history:**
Query last 20 messages for this `room_id`, ordered by `created_at` ascending. Join with `profiles` to get `username`. Render each with the `render_message()` helper (see below).

**Step 4 — Print separator:**
Print a Rich Rule (horizontal line) to visually separate history from live messages.

**Step 5 — Start async loop:**
Call `asyncio.run(chat_loop(supabase, room_id, user_id))`.

**The `chat_loop` async function:**

```python
async def chat_loop(supabase: Client, room_id: str, user_id: str):
```

This runs two concurrent `asyncio` tasks:

- **`input_task`** — Reads user input line by line using `asyncio.get_event_loop().run_in_executor(None, input, "")` to avoid blocking. On each line, inserts a row into `messages`: `{"room_id": room_id, "user_id": user_id, "content": text}`.

- **`listen_task`** — Opens a Supabase Realtime subscription on the `messages` table filtered by `room_id=eq.<room_id>`. In the callback, renders the incoming message using `render_message()`.

Use `asyncio.gather()` to run both tasks. Handle `KeyboardInterrupt` by cancelling both tasks, unsubscribing from Realtime, and printing a goodbye message.

**The `render_message()` helper:**

```python
def render_message(username: str, content: str, created_at: str) -> None:
```

Uses Rich `Console` to print:
```
[HH:MM]  username    content
```

- Timestamp: parsed from ISO string, formatted as `HH:MM`, styled `dim`.
- Username: styled with a color derived from `hash(username) % 6` mapping to a set of Rich color names (e.g. `cyan`, `green`, `yellow`, `magenta`, `blue`, `red`).
- Content: default white text.

Use a module-level `username_color_cache: dict[str, str]` to avoid recomputing colors.

---

### `main.py`

Wires everything together into a single Typer app.

```python
import typer
from app import auth, rooms, chat

app = typer.Typer(help="relay — a terminal chat app powered by Supabase")

app.command("register")(auth.register)
app.command("login")(auth.login)
app.command("logout")(auth.logout)
app.command("rooms")(rooms.list_rooms)
app.command("rooms-create")(rooms.create)
app.command("join")(chat.join)

if __name__ == "__main__":
    app()
```

---

## Supabase Database Schema

Before running the app, the following SQL must be executed in the Supabase SQL Editor. Include this in the README.

```sql
-- Profiles
create table profiles (
  id uuid references auth.users on delete cascade primary key,
  username text unique not null,
  created_at timestamptz default now()
);

-- Rooms
create table rooms (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  created_by uuid references profiles(id),
  created_at timestamptz default now()
);

-- Messages
create table messages (
  id uuid primary key default gen_random_uuid(),
  room_id uuid references rooms(id) on delete cascade,
  user_id uuid references profiles(id),
  content text not null,
  created_at timestamptz default now()
);

-- Enable Realtime
alter publication supabase_realtime add table messages;

-- RLS
alter table profiles enable row level security;
create policy "Profiles viewable by all" on profiles for select using (true);
create policy "Users insert own profile" on profiles for insert with check (auth.uid() = id);

alter table rooms enable row level security;
create policy "Rooms viewable by authenticated" on rooms for select using (auth.role() = 'authenticated');
create policy "Authenticated can create rooms" on rooms for insert with check (auth.role() = 'authenticated');

alter table messages enable row level security;
create policy "Messages viewable by authenticated" on messages for select using (auth.role() = 'authenticated');
create policy "Authenticated can send messages" on messages for insert with check (auth.uid() = user_id);
```

---

## Build Order

Build the files in this exact order to avoid import errors:

1. `app/__init__.py` — empty file
2. `.gitignore` — include `.env`, `__pycache__/`, `*.egg-info/`, `venv/`
3. `pyproject.toml`
4. `app/session.py`
5. `app/supabase_client.py`
6. `app/auth.py`
7. `app/rooms.py`
8. `app/chat.py`
9. `app/main.py`
10. `README.md`

---

## README Requirements

The README must include:

1. **What relay is** — one paragraph
2. **Prerequisites** — Python 3.11+, a Supabase account
3. **Setup steps** — clone, create venv, install deps, create `.env`, run SQL schema
4. **Usage** — one example per command with expected output
5. **Troubleshooting** — at least: "I get an auth error", "Messages aren't appearing in real time", "Room name already taken"

---

## Acceptance Criteria

The build is complete when all of the following work without errors:

- [ ] `relay register` creates a user and saves session to `.env`
- [ ] `relay login` authenticates and saves session
- [ ] `relay logout` clears session
- [ ] `relay rooms` lists all rooms in a Rich table
- [ ] `relay rooms-create` creates a new room
- [ ] `relay join <room>` shows last 20 messages then enters live mode
- [ ] Two terminals logged in as different users can exchange messages in real time
- [ ] `Ctrl+C` in `relay join` exits cleanly without a traceback
- [ ] All errors show friendly messages, never raw exceptions
