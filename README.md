# relay

A terminal-based multi-user chat application powered by Supabase. Users can register, log in, create chat rooms, and exchange messages in real time. The CLI is built with Typer for easy command handling, and Rich for beautiful terminal output. Messages are delivered instantly via Supabase Realtime (WebSockets).

## Prerequisites

- **Python 3.11+**
- **A Supabase account** with a project created

## Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd relay-cli
```

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 4. Create the `.env` File

Create a `.env` file in the project root with your Supabase credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key

SUPABASE_ACCESS_TOKEN=
SUPABASE_REFRESH_TOKEN=
SUPABASE_USER_ID=
```

You can find your Supabase URL and anon key in your Supabase project settings under "API".

### 5. Set Up the Database Schema

Run the following SQL in your Supabase SQL Editor (Dashboard → SQL Editor → New Query):

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

-- RLS Policies
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

## Usage

### Register a New Account

```bash
relay register
```

**Example:**
```
$ relay register
Email: alice@example.com
Password: ********
Confirm password: ********
Username: alice
Successfully registered and logged in as alice!
```

### Log In

```bash
relay login
```

**Example:**
```
$ relay login
Email: alice@example.com
Password: ********
Successfully logged in as alice!
```

### Log Out

```bash
relay logout
```

**Example:**
```
$ relay logout
Successfully logged out.
```

### List Chat Rooms

```bash
relay rooms
```

**Example:**
```
$ relay rooms
                    Chat Rooms
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Name         ┃ Created By ┃ Created At       ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ general      │ alice      │ 2026-02-10 10:30 │
│ random       │ bob        │ 2026-02-10 11:45 │
└──────────────┴────────────┴──────────────────┘
```

### Create a New Room

```bash
relay rooms-create
```

**Example:**
```
$ relay rooms-create
Room name: announcements
Room announcements created successfully!
Join it with relay join announcements
```

### Join a Room and Chat

```bash
relay join <room-name>
```

**Example:**
```
$ relay join general

Joined room: general

--- Recent messages ---
[10:32]  alice  Hello everyone!
[10:33]  bob    Hey Alice!

───────────────────── Live Chat ─────────────────────

Type your message and press Enter to send. Press Ctrl+C to exit.

Hello from the CLI!
[10:35]  alice  Hello from the CLI!
```

Press `Ctrl+C` to exit the chat room.

## Commands Reference

| Command | Description |
|---------|-------------|
| `relay register` | Create a new user account |
| `relay login` | Log in to an existing account |
| `relay logout` | Log out of the current session |
| `relay rooms` | List all available chat rooms |
| `relay rooms-create` | Create a new chat room |
| `relay join <room>` | Join a chat room and start messaging |

## Troubleshooting

### "I get an auth error"

- Make sure your `.env` file has the correct `SUPABASE_URL` and `SUPABASE_KEY` values
- Verify your Supabase project is active and the API is enabled
- Try logging out and logging back in: `relay logout` then `relay login`
- Check if your email has been confirmed (if email confirmation is enabled in Supabase)

### "Messages aren't appearing in real time"

- Make sure you've run the SQL to enable Realtime: `alter publication supabase_realtime add table messages;`
- In your Supabase Dashboard, go to Database → Replication and ensure the `messages` table has Realtime enabled
- Check your network connection
- Try leaving and rejoining the room

### "Room name already taken"

- Room names must be unique. Choose a different name for your room
- Run `relay rooms` to see existing room names

### "You must be logged in"

- Run `relay login` with your credentials, or `relay register` to create a new account

### "SUPABASE_URL and SUPABASE_KEY must be set"

- Create a `.env` file in the project root with your Supabase credentials
- Make sure the file is named exactly `.env` (not `.env.txt` or similar)

## License

MIT
