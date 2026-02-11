"""
Chat functionality for relay CLI.
Handles joining rooms and the async chat loop with real-time messaging.
"""

import asyncio
from datetime import datetime

import typer
from rich.console import Console
from rich.rule import Rule

from app.supabase_client import get_client
from app.session import is_logged_in, load_session


console = Console()

# Color palette for usernames
USERNAME_COLORS = ["cyan", "green", "yellow", "magenta", "blue", "red"]

# Cache for username colors
username_color_cache: dict[str, str] = {}

# Cache for user profiles to avoid repeated lookups
username_cache: dict[str, str] = {}


def get_username_from_id(supabase, user_id: str) -> str:
    """Fetch username for a user ID with caching."""
    if not user_id:
        return "Unknown User"
    if user_id in username_cache:
        return username_cache[user_id]
    
    try:
        profile_response = supabase.table("profiles").select("username").eq("id", user_id).execute()
        
        if profile_response.data and len(profile_response.data) > 0:
            username = profile_response.data[0].get("username", "Unknown User")
            username_cache[user_id] = username
            return username
        else:
            # Profile doesn't exist
            username_cache[user_id] = f"User-{user_id[:8]}"
            return username_cache[user_id]
    except Exception:
        # Fallback to showing partial user ID
        fallback = f"User-{user_id[:8]}"
        username_cache[user_id] = fallback
        return fallback


def preload_usernames(supabase, messages: list[dict]) -> None:
    """Preload usernames for message user_ids to avoid per-message lookups."""
    missing_ids = {
        msg.get("user_id") for msg in messages if msg.get("user_id")
    } - set(username_cache.keys())

    if not missing_ids:
        return

    try:
        profiles_response = supabase.table("profiles").select(
            "id, username"
        ).in_("id", list(missing_ids)).execute()

        for profile in profiles_response.data or []:
            user_id = profile.get("id")
            if not user_id:
                continue
            username = profile.get("username") or f"User-{user_id[:8]}"
            username_cache[user_id] = username
    except Exception:
        # Leave missing IDs to fall back per-message.
        pass


def get_username_color(username: str) -> str:
    """Get a consistent color for a username."""
    if username not in username_color_cache:
        color_index = hash(username) % len(USERNAME_COLORS)
        username_color_cache[username] = USERNAME_COLORS[color_index]
    return username_color_cache[username]


def render_message(username: str, content: str, created_at: str) -> None:
    """
    Render a chat message to the console.
    Format: [HH:MM]  username    content
    """
    # Parse and format timestamp
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        timestamp = dt.strftime("%H:%M")
    except Exception:
        timestamp = "--:--"
    
    # Get color for username
    color = get_username_color(username)
    
    # Print formatted message
    console.print(
        f"[dim][{timestamp}][/dim]  [{color}]{username}[/{color}]  {content}"
    )


async def input_loop(supabase, room_id: str, user_id: str) -> None:
    """
    Async task that reads user input and sends messages to the room.
    """
    loop = asyncio.get_event_loop()
    
    while True:
        try:
            # Read input in a non-blocking way
            text = await loop.run_in_executor(None, input, "")
            
            if text.strip():
                # Insert message into the database
                supabase.table("messages").insert({
                    "room_id": room_id,
                    "user_id": user_id,
                    "content": text
                }).execute()
        except EOFError:
            # Input stream closed
            break
        except Exception as e:
            console.print(f"[red]Failed to send message: {e}[/red]")


def handle_realtime_message(payload: dict, supabase) -> None:
    """
    Callback for handling incoming real-time messages.
    (Note: Currently using polling instead of realtime subscriptions)
    """
    pass


async def chat_loop(supabase, room_id: str, user_id: str) -> None:
    """
    Main async function that runs the input and listen tasks concurrently.
    Periodically polls for new messages while allowing user input.
    """
    
    try:
        console.print("[dim]Type your message and press Enter to send. Press Ctrl+C to exit.[/dim]")
        console.print()
        
        # Track the last message timestamp to avoid showing duplicates
        last_message_time = None
        
        # Create tasks for input and message polling
        input_task = asyncio.create_task(input_loop(supabase, room_id, user_id))
        
        async def poll_messages():
            """Poll for new messages every 2 seconds."""
            nonlocal last_message_time
            
            try:
                while True:
                    await asyncio.sleep(2)
                    
                    # Fetch new messages since last check
                    query = supabase.table("messages").select(
                        "content, created_at, user_id, profiles(username)"
                    ).eq("room_id", room_id).order("created_at", desc=False)
                    
                    if last_message_time:
                        query = query.gt("created_at", last_message_time)
                    
                    try:
                        messages_response = query.execute()
                        messages = messages_response.data
                    except Exception:
                        # Fallback for schemas without a messages->profiles relationship
                        fallback_query = supabase.table("messages").select(
                            "content, created_at, user_id"
                        ).eq("room_id", room_id).order("created_at", desc=False)
                        if last_message_time:
                            fallback_query = fallback_query.gt("created_at", last_message_time)
                        messages_response = fallback_query.execute()
                        messages = messages_response.data
                    
                    preload_usernames(supabase, messages)

                    for msg in messages:
                        user_id_msg = msg.get("user_id")
                        profile = msg.get("profiles") or {}
                        username = profile.get("username") or username_cache.get(
                            user_id_msg
                        ) or get_username_from_id(supabase, user_id_msg)
                        
                        content = msg.get("content", "")
                        created_at = msg.get("created_at", "")
                        render_message(username, content, created_at)
                        
                        # Update the last message time
                        last_message_time = created_at
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
        
        poll_task = asyncio.create_task(poll_messages())
        
        # Wait for either task to complete
        await asyncio.gather(input_task, poll_task)
        
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass


def join(room_name: str = typer.Argument(..., help="Name of the room to join")) -> None:
    """Join a chat room and start chatting."""
    try:
        # Check if user is logged in
        if not is_logged_in():
            console.print("[yellow]You must be logged in to join rooms.[/yellow]")
            console.print("Run [bold]relay login[/bold] or [bold]relay register[/bold] first.")
            raise typer.Exit(1)
        
        # Get user ID from session
        session = load_session()
        user_id = session.get("user_id")
        
        if not user_id:
            console.print("[red]Session error. Please log in again.[/red]")
            raise typer.Exit(1)
        
        # Get Supabase client
        supabase = get_client()
        
        # Look up the room
        room_response = supabase.table("rooms").select("id, name").eq("name", room_name).execute()
        
        if not room_response.data:
            console.print(f"[red]Room '{room_name}' not found.[/red]")
            console.print("Run [bold]relay rooms[/bold] to see available rooms.")
            raise typer.Exit(1)
        
        room = room_response.data[0]
        room_id = room["id"]
        
        console.print(f"\n[bold cyan]Joined room: {room_name}[/bold cyan]\n")
        
        # Fetch last 20 messages
        try:
            messages_response = supabase.table("messages").select(
                "content, created_at, user_id, profiles(username)"
            ).eq("room_id", room_id).order("created_at", desc=False).limit(20).execute()
        except Exception:
            # Fallback for schemas without a messages->profiles relationship
            messages_response = supabase.table("messages").select(
                "content, created_at, user_id"
            ).eq("room_id", room_id).order("created_at", desc=False).limit(20).execute()
        
        messages = messages_response.data
        
        if messages:
            console.print("[dim]--- Recent messages ---[/dim]")
            preload_usernames(supabase, messages)

            for msg in messages:
                # Get username by looking up the profile
                user_id_msg = msg.get("user_id")
                profile = msg.get("profiles") or {}
                username = profile.get("username") or username_cache.get(
                    user_id_msg
                ) or get_username_from_id(supabase, user_id_msg)
                
                content = msg.get("content", "")
                created_at = msg.get("created_at", "")
                render_message(username, content, created_at)
        else:
            console.print("[dim]No messages yet. Be the first to say something![/dim]")
        
        # Print separator
        console.print()
        console.print(Rule("Live Chat", style="cyan"))
        console.print()
        
        # Start the async chat loop
        try:
            asyncio.run(chat_loop(supabase, room_id, user_id))
        except KeyboardInterrupt:
            pass
        
        console.print()
        console.print(f"[dim]Left room: {room_name}[/dim]")
    
    except typer.Exit:
        raise
    except KeyboardInterrupt:
        console.print()
        console.print("[dim]Goodbye![/dim]")
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to join room: {e}[/red]")
        raise typer.Exit(1)
