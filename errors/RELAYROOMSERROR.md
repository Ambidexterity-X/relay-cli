# RELAY ROOMS ERROR 1
Usage: relay rooms-create [OPTIONS]                  
                                                      
 Create a new chat room.                              
                                                      
╭──────── Traceback (most recent call last) ─────────╮
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/bin/relay:8 in  │
│ <module>                                           │
│                                                    │
│   5 from app.main import app                       │
│   6 if __name__ == '__main__':                     │
│   7 │   sys.argv[0] = sys.argv[0].removesuffix('.e │
│ ❱ 8 │   sys.exit(app())                            │
│   9                                                │
│                                                    │
│ ╭──────────────────── locals ────────────────────╮ │
│ │ __annotations__ = {}                           │ │
│ │    __builtins__ = <module 'builtins'           │ │
│ │                   (built-in)>                  │ │
│ │      __cached__ = None                         │ │
│ │         __doc__ = 'exec\'                      │ │
│ │                   "/home/ambidexterityx/Ambid… │ │
│ │                   Codex/Projects/relay-cli/ap… │ │
│ │        __file__ = '/home/ambidexterityx/Ambid… │ │
│ │                   Codex/Projects/relay-cli/ap… │ │
│ │      __loader__ = <_frozen_importlib_external… │ │
│ │                   object at 0x7e7ef1f9ae50>    │ │
│ │        __name__ = '__main__'                   │ │
│ │     __package__ = None                         │ │
│ │        __spec__ = None                         │ │
│ │             app = <typer.main.Typer object at  │ │
│ │                   0x7e7ef1a90d90>              │ │
│ │             sys = <module 'sys' (built-in)>    │ │
│ ╰────────────────────────────────────────────────╯ │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/main.py:326 in __call__        │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/main.py:309 in __call__        │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:1485 in __call__       │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/core.py:723 in main            │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/core.py:193 in _main           │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:1871 in invoke         │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:1216 in make_context   │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:1227 in parse_args     │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:2578 in                │
│ handle_parse_result                                │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:3313 in process_value  │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:2448 in process_value  │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/decorators.py:539 in show_help │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:750 in get_help        │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/click/core.py:1094 in get_help       │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/core.py:674 in format_help     │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/rich_utils.py:601 in           │
│ rich_format_help                                   │
│                                                    │
│ /home/ambidexterityx/Ambidexterity                 │
│ Codex/Projects/relay-cli/app/.venv/lib/python3.11/ │
│ site-packages/typer/rich_utils.py:370 in           │
│ _print_options_panel                               │
╰────────────────────────────────────────────────────╯
TypeError: Parameter.make_metavar() missing 1 required
positional argument: 'ctx'
