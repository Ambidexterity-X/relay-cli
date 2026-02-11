"""
Main entry point for the relay CLI application.
"""

import typer

from app import auth, rooms, chat, profile


app = typer.Typer(
    help="relay — a terminal chat app powered by Supabase",
    no_args_is_help=True
)

# Register auth commands
app.command("register")(auth.register)
app.command("login")(auth.login)
app.command("logout")(auth.logout)

# Register profile commands
app.command("set-username")(profile.set_username)

# Register room commands
app.command("rooms")(rooms.list_rooms)
app.command("rooms-create")(rooms.create)

# Register chat commands
app.command("join")(chat.join)


if __name__ == "__main__":
    app()
