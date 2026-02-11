"""
Profile management commands for relay CLI.
"""

import typer
from rich.console import Console

from app.supabase_client import get_client
from app.session import is_logged_in, load_session


console = Console()


def set_username(username: str = typer.Argument(None, help="Your desired username")) -> None:
    """Set or update your username."""
    try:
        if not is_logged_in():
            console.print("[yellow]You must be logged in to set your username.[/yellow]")
            console.print("Run [bold]relay login[/bold] first.")
            raise typer.Exit(1)
        
        # Get user ID from session
        session = load_session()
        user_id = session.get("user_id")
        
        if not user_id:
            console.print("[red]Session error. Please log in again.[/red]")
            raise typer.Exit(1)
        
        # Get Supabase client
        supabase = get_client()
        
        # Check if profile exists
        existing_profile = supabase.table("profiles").select("username").eq("id", user_id).execute()
        
        action = "update" if existing_profile.data else "create"
        
        # Prompt for new username if not provided
        if not username:
            username = typer.prompt("Enter your username")
        
        if not username.strip():
            console.print("[red]Username cannot be empty.[/red]")
            raise typer.Exit(1)
        
        # Insert or update profile
        try:
            if action == "create":
                supabase.table("profiles").insert({
                    "id": user_id,
                    "username": username.strip()
                }).execute()
                console.print(f"[green]Username set to [bold]{username}[/bold]![/green]")
            else:
                supabase.table("profiles").update({
                    "username": username.strip()
                }).eq("id", user_id).execute()
                console.print(f"[green]Username updated to [bold]{username}[/bold]![/green]")
        except Exception as e:
            error_msg = str(e).lower()
            if "unique" in error_msg or "duplicate" in error_msg:
                console.print(f"[red]Username '{username}' is already taken. Please choose a different username.[/red]")
            else:
                console.print(f"[red]Failed to set username: {e}[/red]")
            raise typer.Exit(1)
    
    except typer.Exit:
        raise
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Operation failed: {e}[/red]")
        raise typer.Exit(1)
