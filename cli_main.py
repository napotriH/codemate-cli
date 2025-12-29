#!/usr/bin/env python3
import click
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from cli_agent import CLIAgent

console = Console()

@click.command()
def main():
    """CodeMate CLI - Advanced AI Assistant"""
    
    console.print(Panel.fit(
        "[bold blue]CodeMate CLI[/bold blue]\n"
        "[dim]Advanced AI Assistant with Full File System Access[/dim]\n"
        f"[yellow]Workspace: {os.getcwd()}[/yellow]\n"
        "[green]Ready to help with coding, file management, and project analysis[/green]",
        border_style="blue"
    ))
    
    agent = CLIAgent()
    
    console.print("\n[bold green]What I can do:[/bold green]")
    console.print("• [cyan]Create & modify files:[/cyan] 'Create a REST API in Flask'")
    console.print("• [cyan]Read & analyze code:[/cyan] 'Explain the main.py file'")
    console.print("• [cyan]Debug & optimize:[/cyan] 'Fix the bug in calculator.py'")
    console.print("• [cyan]Project management:[/cyan] 'Show me the project structure'")
    console.print("• [cyan]Code review:[/cyan] 'Review my Python code for improvements'")
    console.print("\n[bold yellow]Quick Commands:[/bold yellow]")
    console.print("• [green]/search <text>[/green] - Search in all files")
    console.print("• [green]/git[/green] - Show Git status")
    console.print("• [green]/run <file>[/green] - Execute code file")
    console.print("• [green]/backup[/green] - Create project backup")
    console.print("• [green]/info[/green] - Show project information")
    console.print("• [green]/files[/green] - List files")
    console.print("\n[bold magenta]Batch Operations:[/bold magenta]")
    console.print("• [cyan]/batch replace <old> <new>[/cyan] - Replace text in all files")
    console.print("• [cyan]/batch rename <old> <new>[/cyan] - Rename functions/classes")
    console.print("• [cyan]/batch pattern <type>[/cyan] - Apply design pattern (singleton, factory)")
    console.print("• [cyan]/batch create <type>[/cyan] - Create project structure (flask, fastapi, react)")
    console.print("\n[bold red]Debug & Testing:[/bold red]")
    console.print("• [red]/debug <file>[/red] - Analyze code for issues")
    console.print("• [red]/profile <file>[/red] - Performance profiling")
    console.print("• [red]/fix <file>[/red] - Suggest optimizations")
    console.print("• [red]/test [pattern][/red] - Run tests (default: test_*.py)")
    console.print("\n[bold blue]Integrations:[/bold blue]")
    console.print("• [blue]/cmd <command>[/blue] - Execute terminal command")
    console.print("• [blue]/preview <file>[/blue] - Preview HTML/Markdown/JSON")
    console.print("• [blue]/check <file>[/blue] - Real-time syntax checking")
    console.print("• [blue]/monitor <file> [seconds][/blue] - Monitor file changes (default: 30s)")
    console.print("\n[bold purple]Version Control:[/bold purple]")
    console.print("• [purple]/undo <file>[/purple] - Undo last changes to file")
    console.print("• [purple]/history <file>[/purple] - Show file modification history")
    console.print("• [purple]/restore <file> <version>[/purple] - Restore specific version")
    console.print("\n[dim]Commands: /clear (reset), /quit (exit)[/dim]\n")
    
    try:
        while True:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]", default="")
            
            if not user_input.strip():
                continue
                
            if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                console.print("[yellow]Goodbye! Happy coding! 🚀[/yellow]")
                break
            elif user_input.lower() == '/clear':
                agent.clear_conversation()
                console.print("[yellow]✨ Conversation cleared. Fresh start![/yellow]\n")
                continue
            elif user_input.lower() == '/files':
                agent.list_files()
                continue
            elif user_input.lower().startswith('/search '):
                search_term = user_input[8:].strip()
                agent.search_in_files(search_term)
                continue
            elif user_input.lower() == '/git':
                agent.git_status()
                continue
            elif user_input.lower().startswith('/run '):
                filepath = user_input[5:].strip()
                agent.run_file(filepath)
                continue
            elif user_input.lower() == '/backup':
                agent.backup_project()
                continue
            elif user_input.lower() == '/info':
                project_info = agent.detect_project_type()
                deps = agent.analyze_dependencies()
                
                console.print(Panel.fit(
                    f"[bold cyan]Project Information[/bold cyan]\n"
                    f"Type: [yellow]{project_info['type']}[/yellow]\n"
                    f"Language: [green]{project_info['language']}[/green]\n"
                    f"Framework: [magenta]{project_info.get('framework', 'None')}[/magenta]\n"
                    f"Dependencies: [dim]{len(deps['main']) + len(deps['python'])} total[/dim]",
                    border_style="cyan"
                ))
                continue
            elif user_input.lower().startswith('/batch '):
                parts = user_input[7:].split(' ', 2)
                if len(parts) >= 3 and parts[0] == 'replace':
                    old_text, new_text = parts[1], parts[2]
                    agent.batch_modify_files("*", old_text, new_text)
                elif len(parts) >= 3 and parts[0] == 'rename':
                    old_name, new_name = parts[1], parts[2]
                    agent.refactor_rename(old_name, new_name)
                elif len(parts) >= 2 and parts[0] == 'pattern':
                    pattern_type = parts[1]
                    agent.apply_design_pattern(pattern_type)
                elif len(parts) >= 2 and parts[0] == 'create':
                    structure_type = parts[1]
                    agent.batch_create_structure(structure_type)
                else:
                    console.print("[yellow]Usage: /batch [replace|rename|pattern|create] <args>[/yellow]")
                continue
            elif user_input.lower().startswith('/debug '):
                filepath = user_input[7:].strip()
                agent.debug_code(filepath)
                continue
            elif user_input.lower().startswith('/profile '):
                filepath = user_input[9:].strip()
                agent.run_with_profiling(filepath)
                continue
            elif user_input.lower().startswith('/fix '):
                filepath = user_input[5:].strip()
                agent.suggest_fixes(filepath)
                continue
            elif user_input.lower().startswith('/test'):
                pattern = user_input[5:].strip() if len(user_input) > 5 else "test_*.py"
                agent.test_runner(pattern)
                continue
            elif user_input.lower().startswith('/cmd '):
                command = user_input[5:].strip()
                agent.terminal_command(command)
                continue
            elif user_input.lower().startswith('/preview '):
                filepath = user_input[9:].strip()
                agent.preview_file(filepath)
                continue
            elif user_input.lower().startswith('/check '):
                filepath = user_input[7:].strip()
                agent.syntax_check_realtime(filepath)
                continue
            elif user_input.lower().startswith('/monitor '):
                parts = user_input[9:].split()
                filepath = parts[0]
                duration = int(parts[1]) if len(parts) > 1 else 30
                agent.live_file_monitor(filepath, duration)
                continue
            elif user_input.lower().startswith('/undo '):
                filepath = user_input[6:].strip()
                agent.undo_file_changes(filepath)
                continue
            elif user_input.lower().startswith('/history '):
                filepath = user_input[9:].strip()
                agent.show_file_history(filepath)
                continue
            elif user_input.lower().startswith('/restore '):
                parts = user_input[9:].split()
                if len(parts) >= 2:
                    filepath, version = parts[0], int(parts[1])
                    agent.restore_file_version(filepath, version)
                else:
                    console.print("[yellow]Usage: /restore <file> <version_number>[/yellow]")
                continue
            
            console.print("\n[bold magenta]CodeMate[/bold magenta]:")
            
            # Streaming response
            response_text = ""
            with Live("", refresh_per_second=10, console=console) as live:
                for chunk in agent.send_message_stream(user_input):
                    response_text += chunk
                    live.update(Markdown(response_text))
            
            console.print()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye! Happy coding! 🚀[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")

if __name__ == "__main__":
    main()