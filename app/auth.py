"""
Authentication commands for relay CLI.
Handles register, login, and logout functionality.
"""

import typer
from rich.console import Console

from app.supabase_client import get_client
from app.session import save_session, clear_session, is_logged_in


console = Console()


def register() -> None:
    """Register a new user account."""
    try:
        # Prompt for user details
        email = typer.prompt("Email")
        password = typer.prompt("Password", hide_input=True)
        confirm_password = typer.prompt("Confirm password", hide_input=True)
        
        if password != confirm_password:
            console.print("[red]Passwords do not match.[/red]")
            raise typer.Exit(1)
        
        username = typer.prompt("Username")
        
        # Get Supabase client
        supabase = get_client()
        
        # Step 1: Sign up the user
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not response.user:
            console.print("[red]Registration failed. Please try again.[/red]")
            raise typer.Exit(1)
        
        user_id = response.user.id
        
        # Step 2: Sign in immediately to get a valid authenticated session
        sign_in_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not sign_in_response.session:
            console.print("[red]Account created but login failed. Please try 'relay login'[/red]")
            raise typer.Exit(1)
        
        # Step 3: Save session first so the client can use the authenticated token
        save_session(
            access_token=sign_in_response.session.access_token,
            refresh_token=sign_in_response.session.refresh_token,
            user_id=user_id
        )
        
        # Step 4: Reinitialize client to pick up the authenticated session
        supabase = get_client()
        
        # Step 5: Insert profile with authenticated session
        try:
            result = supabase.table("profiles").insert({
                "id": user_id,
                "username": username
            }).execute()
            
            # Verify the profile was created
            if not result.data:
                console.print("[red]Failed to create profile. Please try logging in again.[/red]")
                raise typer.Exit(1)
                
        except Exception as e:
            error_msg = str(e).lower()
            if "unique" in error_msg or "duplicate" in error_msg:
                console.print(f"[red]Username '{username}' is already taken. Please choose a different username.[/red]")
                raise typer.Exit(1)
            else:
                console.print(f"[red]Failed to create profile: {e}[/red]")
                console.print("[yellow]Your account was created but without a profile. Use 'relay set-username' to fix this.[/yellow]")
                raise typer.Exit(1)
        
        console.print(f"[green]Successfully registered and logged in as [bold]{username}[/bold]![/green]")
    
    except typer.Exit:
        raise
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "already exists" in error_msg:
            console.print("[red]An account with this email already exists.[/red]")
        else:
            console.print(f"[red]Registration failed: {e}[/red]")
        raise typer.Exit(1)


def login() -> None:
    """Log in to an existing account."""
    try:
        # Prompt for credentials
        email = typer.prompt("Email")
        password = typer.prompt("Password", hide_input=True)
        
        # Get Supabase client
        supabase = get_client()
        
        # Sign in
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not response.user or not response.session:
            console.print("[red]Login failed. Please check your credentials.[/red]")
            raise typer.Exit(1)
        
        user = response.user
        session = response.session
        
        # Save session
        save_session(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user_id=user.id
        )
        
        # Try to get username for a friendlier message
        try:
            profile = supabase.table("profiles").select("username").eq("id", user.id).single().execute()
            username = profile.data.get("username", email)
        except Exception:
            username = email
        
        console.print(f"[green]Successfully logged in as [bold]{username}[/bold]![/green]")
    
    except typer.Exit:
        raise
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        error_msg = str(e).lower()
        if "invalid" in error_msg or "credentials" in error_msg:
            console.print("[red]Invalid email or password.[/red]")
        else:
            console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)


def logout() -> None:
    """Log out of the current session."""
    try:
        if not is_logged_in():
            console.print("[yellow]You are not logged in.[/yellow]")
            return
        
        # Get Supabase client and sign out
        supabase = get_client()
        
        try:
            supabase.auth.sign_out()
        except Exception:
            # Even if sign_out fails on the server, we still clear local session
            pass
        
        # Clear local session
        clear_session()
        
        console.print("[green]Successfully logged out.[/green]")
    
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Logout failed: {e}[/red]")
        raise typer.Exit(1)
