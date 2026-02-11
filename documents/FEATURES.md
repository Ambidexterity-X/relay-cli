# relay — Feature Documentation

> A terminal-based multi-user chat app built with Python, Typer, and Supabase.

---

## Table of Contents

- [Overview](#overview)
- [Commands](#commands)
- [Authentication](#authentication)
- [Rooms](#rooms)
- [Chat](#chat)
- [Message Display](#message-display)
- [Session Management](#session-management)
- [Data Model](#data-model)
- [Project Structure](#project-structure)

---

## Overview

`relay` is a CLI chat application that allows multiple users to communicate in real time through named rooms. It runs entirely in the terminal and uses Supabase for authentication, data storage, and live message delivery via Realtime subscriptions.

---

## Commands

| Command | Description |
|---|---|
| `relay register` | Create a new account with email, password, and username |
| `relay login` | Log in with email and password, saves session locally |
| `relay logout` | Clear the local session |
| `relay rooms` | List all available rooms |
| `relay rooms create` | Create a new chat room |
| `relay join <room-name>` | Join a room and start chatting live |

---

## Authentication

- **Provider:** Supabase Auth (email/password)
- On `register`, the user provides an email, password, and a unique username. A record is created in the `profiles` table linked to the Supabase auth user.
- On `login`, credentials are verified against Supabase Auth. The resulting access token, refresh token, and user ID are saved to the local `.env` file.
- On `logout`, the session fields are cleared from the `.env` file.
- All commands that require authentication will check for a valid session before proceeding and prompt the user to log in if none is found.

---

## Rooms

- Any authenticated user can **view** the list of rooms.
- Any authenticated user can **create** a new room by providing a unique name.
- Rooms are stored in the `rooms` table with a reference to the user who created them.

---

## Chat

### Joining a Room

When a user runs `relay join <room-name>`, the following happens:

1. The session is loaded and the Supabase client is authenticated.
2. The room is looked up by name to get its `room_id`.
3. The **last 20 messages** are fetched from the database, along with the sender's username, and displayed in the terminal.
4. A **Supabase Realtime** subscription is opened on the `messages` table, filtered by `room_id`.
5. Two concurrent tasks run:
   - **Input loop** — reads the user's typed input and sends each message to Supabase on Enter.
   - **Realtime listener** — prints incoming messages from other users as they arrive.
6. Pressing `Ctrl+C` cleanly unsubscribes from Realtime and exits the room.

---

## Message Display

Messages are rendered using the [Rich](https://github.com/Textualize/rich) library for a clean, readable terminal experience.

**Format:**
```
[HH:MM]  username   message content
```

- **Timestamp** — dimmed/muted color
- **Username** — unique color per user (consistent within a session)
- **Message** — plain white text

**Example:**
```
[12:45]  alice    hello everyone!
[12:46]  bob      hey alice, how's it going?
[12:47]  alice    pretty good! just testing relay 🚀
```

---

## Session Management

- Sessions are stored in the project's `.env` file alongside Supabase credentials.
- The `.env` file is **never committed to version control** (listed in `.gitignore`).

**`.env` structure:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

SUPABASE_ACCESS_TOKEN=...
SUPABASE_REFRESH_TOKEN=...
SUPABASE_USER_ID=...
```

---

## Data Model

### `profiles`
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` | References `auth.users` |
| `username` | `text` | Unique |
| `created_at` | `timestamptz` | Auto-set |

### `rooms`
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` | Primary key |
| `name` | `text` | Unique |
| `created_by` | `uuid` | References `profiles.id` |
| `created_at` | `timestamptz` | Auto-set |

### `messages`
| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` | Primary key |
| `room_id` | `uuid` | References `rooms.id` |
| `user_id` | `uuid` | References `profiles.id` |
| `content` | `text` | Message body |
| `created_at` | `timestamptz` | Auto-set |

Realtime is enabled on the `messages` table.

---

## Project Structure

```
relay/
├── app/
│   ├── __init__.py
│   ├── main.py            # Entry point, registers all Typer commands
│   ├── auth.py            # register, login, logout
│   ├── rooms.py           # rooms list & create
│   ├── chat.py            # join room + realtime message loop
│   ├── supabase_client.py # Initializes the Supabase client
│   └── session.py         # Reads and writes session tokens to .env
├── .env                   # Supabase credentials + active session
├── .gitignore
├── pyproject.toml         # Project metadata and entry point
└── README.md
```

**Entry point (`pyproject.toml`):**
```toml
[project.scripts]
relay = "app.main:app"
```
