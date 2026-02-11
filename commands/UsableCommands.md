# Relay CLI Commands

## Authentication

| Command | Description |
|---------|-------------|
| `relay register` | Create a new user account. Prompts for email, password, and username. |
| `relay login` | Log in to an existing account. Prompts for email and password. |
| `relay logout` | Log out of the current session and clear saved tokens. |
| `relay set-username` | Set or update your username (useful if registration didn't create a profile). |

## Rooms

| Command | Description |
|---------|-------------|
| `relay rooms` | List all available chat rooms in a formatted table. |
| `relay rooms-create` | Create a new chat room. Prompts for a room name. |

## Chat

| Command | Description |
|---------|-------------|
| `relay join <room-name>` | Join a chat room by name. Shows the last 20 messages then enters live chat mode. Press `Ctrl+C` to exit. |
