"""
Room management commands for relay CLI.
Handles listing and creating rooms.
"""

from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table

from app.supabase_client import get_client
from app.session import is_logged_in, load_session


console = Console()


def list_rooms() -> None:
    """List all chat rooms."""
    try:
        if not is_logged_in():
            console.print("[yellow]You must be logged in to view rooms.[/yellow]")
            console.print("Run [bold]relay login[/bold] or [bold]relay register[/bold] first.")
            raise typer.Exit(1)
        
        # Get Supabase client
        supabase = get_client()
        
        # Query rooms
        response = supabase.table("rooms").select(
            "name, created_at, created_by"
        ).order("created_at", desc=False).execute()
        
        rooms = response.data
        
        if not rooms:
            console.print("[dim]No rooms exist yet.[/dim]")
            console.print("Create one with [bold]relay rooms-create[/bold]")
            return
        
        # Build the table
        table = Table(title="Chat Rooms")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Created By", style="green")
        table.add_column("Created At", style="dim")
        
        for room in rooms:
            name = room.get("name", "Unknown")
            
            # Get creator username by looking up the profile
            created_by_id = room.get("created_by")
            if not created_by_id:
                created_by = "System"
            else:
                try:
                    profile_response = supabase.table("profiles").select("username").eq("id", created_by_id).execute()
                    if profile_response.data and len(profile_response.data) > 0:
                        created_by = profile_response.data[0].get("username", f"User-{created_by_id[:8]}")
                    else:
                        created_by = f"User-{created_by_id[:8]}"
                except Exception:
                    created_by = f"User-{created_by_id[:8]}"
            
            # Format the created_at timestamp
            created_at_str = room.get("created_at", "")
            if created_at_str:
                try:
                    dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    created_at = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    created_at = created_at_str[:16]
            else:
                created_at = "Unknown"
            
            table.add_row(name, created_by, created_at)
        
        console.print(table)
    
    except typer.Exit:
        raise
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to list rooms: {e}[/red]")
        raise typer.Exit(1)


def create(room_name: str = typer.Argument(None, help="Name of the room to create")) -> None:
    """Create a new chat room."""
    try:
        if not is_logged_in():
            console.print("[yellow]You must be logged in to create rooms.[/yellow]")
            console.print("Run [bold]relay login[/bold] or [bold]relay register[/bold] first.")
            raise typer.Exit(1)
        
        # Get user ID from session
        session = load_session()
        user_id = session.get("user_id")
        
        if not user_id:
            console.print("[red]Session error. Please log in again.[/red]")
            raise typer.Exit(1)
        
        # Prompt for room name if not provided
        if not room_name:
            room_name = typer.prompt("Room name")
        
        if not room_name.strip():
            console.print("[red]Room name cannot be empty.[/red]")
            raise typer.Exit(1)
        
        # Get Supabase client
        supabase = get_client()
        
        # Create the room
        supabase.table("rooms").insert({
            "name": room_name.strip(),
            "created_by": user_id
        }).execute()
        
        console.print(f"[green]Room [bold]{room_name}[/bold] created successfully![/green]")
        console.print(f"Join it with [bold]relay join {room_name}[/bold]")
    
    except typer.Exit:
        raise
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        error_msg = str(e).lower()
        if "unique" in error_msg or "duplicate" in error_msg:
            console.print(f"[red]A room named '{room_name}' already exists. Please choose a different name.[/red]")
        else:
            console.print(f"[red]Failed to create room: {e}[/red]")
        raise typer.Exit(1)
