# How relay Works

This document explains the technical internals of `relay` — how the pieces fit together from the moment you run a command to the moment a message appears in your terminal.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Startup & Entry Point](#startup--entry-point)
- [Authentication Flow](#authentication-flow)
- [Session Persistence](#session-persistence)
- [Rooms](#rooms)
- [The Live Chat Loop](#the-live-chat-loop)
- [Realtime Messaging](#realtime-messaging)
- [Message Rendering](#message-rendering)
- [Error Handling & Edge Cases](#error-handling--edge-cases)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────┐
│                  Terminal                    │
│          relay join general                  │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────▼─────────────────────────┐
│              Typer CLI (main.py)             │
│   Parses command, routes to correct module   │
└───────┬───────────────────────┬─────────────┘
        │                       │
┌───────▼──────┐     ┌──────────▼────────────┐
│  session.py  │     │   supabase_client.py   │
│  Loads .env  │     │  Initializes client    │
│  tokens      │     │  with auth session     │
└──────────────┘     └──────────┬────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
    ┌─────────▼──────┐ ┌───────▼───────┐ ┌────────▼──────┐
    │    auth.py     │ │   rooms.py    │ │    chat.py    │
    │ register/login │ │  list/create  │ │  join + loop  │
    └────────────────┘ └───────────────┘ └───────────────┘
                                │
              ┌─────────────────┴──────────────────┐
              │           Supabase Cloud            │
              │  ┌──────────┐  ┌─────────────────┐ │
              │  │   Auth   │  │    Postgres DB   │ │
              │  └──────────┘  │ profiles, rooms, │ │
              │                │    messages      │ │
              │  ┌─────────────┴─────────────────┐│ │
              │  │         Realtime               ││ │
              │  │  (WebSocket subscription on    ││ │
              │  │   messages table)              ││ │
              │  └────────────────────────────────┘│ │
              └────────────────────────────────────┘
```

---

## Startup & Entry Point

When you type a `relay` command, Python's entry point (defined in `pyproject.toml`) calls the Typer app in `main.py`. Typer parses the command and arguments, then delegates to the appropriate module:

```
relay register     →  auth.py :: register()
relay login        →  auth.py :: login()
relay logout       →  auth.py :: logout()
relay rooms        →  rooms.py :: list_rooms()
relay rooms create →  rooms.py :: create_room()
relay join <name>  →  chat.py :: join()
```

Each command function first calls `session.py` to load any existing session from the `.env` file, then initializes the Supabase client with those credentials before doing any work.

---

## Authentication Flow

### Register

1. Typer prompts the user for email, password, and username.
2. `supabase.auth.sign_up()` is called with the email and password. Supabase creates a record in `auth.users` and returns a session.
3. A corresponding row is inserted into the `profiles` table using the new user's `id` and chosen username.
4. The session tokens are written to `.env` via `session.py`.

### Login

1. Typer prompts for email and password.
2. `supabase.auth.sign_in_with_password()` is called.
3. On success, the access token, refresh token, and user ID are saved to `.env`.
4. All subsequent commands read these tokens to authenticate the Supabase client.

### Logout

1. `supabase.auth.sign_out()` is called to invalidate the token on Supabase's side.
2. `session.py` clears the token fields from `.env`.

---

## Session Persistence

`session.py` is responsible for reading and writing session data to the `.env` file. It uses `python-dotenv` to parse and update key-value pairs without clobbering the rest of the file.

The fields it manages are:

```
SUPABASE_ACCESS_TOKEN
SUPABASE_REFRESH_TOKEN
SUPABASE_USER_ID
```

When `supabase_client.py` initializes, it reads these values and passes them into the Supabase client so all requests are authenticated as the logged-in user. This means Row Level Security (RLS) policies on Supabase apply correctly — users can only do what their role allows.

---

## Rooms

### Listing Rooms

`rooms.py` queries the `rooms` table and returns all rows, joining with `profiles` to show the creator's username. Results are printed as a Rich table in the terminal.

### Creating a Room

The user provides a room name. `rooms.py` inserts a new row into `rooms` with the current user's ID as `created_by`. If the name already exists, Supabase returns a unique constraint error which is caught and shown as a friendly message.

---

## The Live Chat Loop

The `join` command in `chat.py` is the most complex part of the app. Here's exactly what happens when you run `relay join general`:

### Step 1 — Look up the room

The room name is queried against the `rooms` table to retrieve the `room_id`. If no room with that name exists, the user is told and the command exits.

### Step 2 — Fetch history

The last 20 messages are fetched from the `messages` table, filtered by `room_id`, ordered by `created_at` ascending, with a join to `profiles` to get each sender's username. These are rendered with Rich before the live session begins.

### Step 3 — Open a Realtime subscription

A WebSocket connection is opened to Supabase Realtime, subscribing to `INSERT` events on the `messages` table filtered to the current `room_id`. Any new message inserted into that room by any user will be pushed to this client over the WebSocket.

### Step 4 — Run two concurrent tasks

Python's `asyncio` runs two tasks simultaneously:

- **Input loop** — Reads a line of text from the user. On Enter, it inserts a new row into `messages` with the current `room_id`, `user_id`, and `content`. The user's own messages appear via the Realtime listener like everyone else's, keeping display logic in one place.
- **Realtime listener** — Waits for incoming events from the WebSocket. When a new message arrives, it fetches the sender's username from `profiles` (or a local cache to avoid redundant lookups) and renders the message with Rich.

### Step 5 — Exit

`Ctrl+C` triggers a `KeyboardInterrupt`. The app catches this, unsubscribes from the Realtime channel, closes the WebSocket connection, and exits cleanly.

---

## Realtime Messaging

Supabase Realtime works by listening to Postgres's logical replication stream. When a row is inserted into the `messages` table, Supabase broadcasts the change over WebSocket to all subscribed clients.

In `relay`, the subscription is scoped to a specific room using a filter:

```
table: messages
event: INSERT
filter: room_id=eq.<room_id>
```

This means each client only receives messages for the room they're currently in — not all messages across all rooms.

The Realtime payload includes the full inserted row (all column values), so the app has the `user_id` and `content` immediately without needing an extra database query. The `user_id` is resolved to a username using a local in-memory cache populated as users are seen.

---

## Message Rendering

All terminal output goes through the [Rich](https://github.com/Textualize/rich) library. Each message is rendered on a single line:

```
[HH:MM]  username    message content
```

- The **timestamp** is formatted from the message's `created_at` field and styled as dim/muted.
- The **username** is assigned a consistent color using a hash of the username string, so the same user always appears in the same color within a session.
- The **message content** is plain white text.

History messages and live messages use the same rendering function, so there's no visual difference between the two.

---

## Error Handling & Edge Cases

| Scenario | Behaviour |
|---|---|
| Running a command without being logged in | Detects missing session tokens, prints a prompt to run `relay login`, exits |
| Joining a room that doesn't exist | Prints an error and exits |
| Creating a room with a duplicate name | Catches the unique constraint error, prints a friendly message |
| Registering with an already-used email | Supabase returns an error, shown to the user |
| Network loss during chat | Realtime WebSocket disconnects; the app catches the error, notifies the user, and exits |
| Pressing Ctrl+C in the chat loop | Cleanly unsubscribes from Realtime and exits without a stack trace |
