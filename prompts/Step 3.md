Great! Now let's create the interface adapters. We'll start with the CLI interface and then move to the web interface.

## Step 3: Interface Adapters

### File: `interfaces/__init__.py`
```python
# Interface adapters for Obsidian Tag Automator
```

### File: `interfaces/cli_interface.py`
```python
import os
import json
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from core.automator_core import ObsidianTagAutomatorCore

class ObsidianTagAutomatorCLI:
    """
    CLI interface for the Obsidian Tag Automator.
    Wraps the core functionality with rich UI elements and interactive prompts.
    """
    
    def __init__(self, vault_path=None, gemini_api_key=None):
        """
        Initialize the CLI interface.
        
        Args:
            vault_path (str or Path, optional): Path to the Obsidian vault.
            gemini_api_key (str, optional): Gemini API key for AI suggestions.
        """
        self.console = Console()
        
        # Detect vault path if not provided
        if vault_path is None:
            vault_path = self._detect_vault_path()
        
        # Initialize the core automator
        self.automator = ObsidianTagAutomatorCore(vault_path, gemini_api_key)
        
        # Display welcome message
        self._display_welcome()
    
    def _detect_vault_path(self):
        """Attempts to detect the Obsidian vault path."""
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / ".obsidian").exists():
                return cwd
            cwd = cwd.parent
        
        self.console.print("[yellow]Obsidian vault path not detected.[/yellow]")
        vault_path = Prompt.ask("Please enter the path to your Obsidian vault")
        return Path(vault_path)
    
    def _display_welcome(self):
        """Display welcome message and system status."""
        self.console.print(Panel.fit(
            "[bold blue]Obsidian Tag Automator[/bold blue]\n"
            "[green]AI-powered tag management for your knowledge base[/green]",
            title="Welcome"
        ))
        
        # Display system status
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Setting", style="cyan")
        status_table.add_column("Value", style="white")
        
        status_table.add_row("Vault Path", str(self.automator.vault_path))
        status_table.add_row("AI Status", "✅ Online" if self.automator.ai_integration.gemini_model else "❌ Offline")
        
        # Get vault stats
        stats_result = self.automator.get_vault_stats()
        if stats_result['success']:
            stats = stats_result['stats']
            status_table.add_row("Total Files", str(stats['total_files']))
            status_table.add_row("Tagged Files", str(stats['tagged_files']))
            status_table.add_row("Unique Tags", str(stats['total_tags']))
        
        self.console.print(status_table)
        self.console.print()
    
    def display_main_menu(self):
        """Display the main menu and handle user selection."""
        while True:
            self.console.print(Panel("[bold cyan]Main Menu[/bold cyan]"))
            
            menu_table = Table(show_header=False, box=None)
            menu_table.add_column("Option", style="green", width=3)
            menu_table.add_column("Description", style="white")
            
            menu_table.add_row("1", "Process files with AI suggestions")
            menu_table.add_row("2", "Rename tags")
            menu_table.add_row("3", "Merge tags")
            menu_table.add_row("4", "Delete tags")
            menu_table.add_row("5", "Generate tag aliases")
            menu_table.add_row("6", "Validate tags")
            menu_table.add_row("7", "View vault statistics")
            menu_table.add_row("8", "Configuration")
            menu_table.add_row("9", "Update tag database")
            menu_table.add_row("0", "Exit")
            
            self.console.print(menu_table)
            
            choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
            
            if choice == "1":
                self._process_files_interactive()
            elif choice == "2":
                self._rename_tags_interactive()
            elif choice == "3":
                self._merge_tags_interactive()
            elif choice == "4":
                self._delete_tags_interactive()
            elif choice == "5":
                self._generate_aliases_interactive()
            elif choice == "6":
                self._validate_tags_interactive()
            elif choice == "7":
                self._display_vault_stats()
            elif choice == "8":
                self._configuration_menu()
            elif choice == "9":
                self._update_tag_database()
            elif choice == "0":
                self.console.print("[green]Goodbye![/green]")
                break
    
    def _process_files_interactive(self):
        """Interactive file processing."""
        self.console.print(Panel("[bold cyan]Process Files[/bold cyan]"))
        
        # Ask for processing options
        self.console.print("\n[yellow]Re-tagging Options:[/yellow]")
        self.console.print("1. Only process files that have NOT been AI-tagged before")
        self.console.print("2. Process all files")
        self.console.print("3. Only re-tag files that have existing tags but are NOT AI-tagged")
        self.console.print("4. Do NOT re-tag any files that already have tags")
        
        re_tag_option = Prompt.ask("Select re-tagging option", choices=["1", "2", "3", "4"])
        
        # Ask for files to process
        process_all = Confirm.ask("Process all files in vault?")
        
        if process_all:
            # Get all markdown files
            file_paths = []
            for root, _, files in os.walk(self.automator.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                        file_paths.append(file_path)
        else:
            # Ask for specific files or patterns
            pattern = Prompt.ask("Enter file pattern (e.g., *.md, notes/*.md)")
            
            file_paths = []
            for root, _, files in os.walk(self.automator.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.match(pattern) and '.obsidian' not in file_path.parts:
                        file_paths.append(file_path)
        
        if not file_paths:
            self.console.print("[red]No files found matching the pattern.[/red]")
            return
        
        self.console.print(f"\n[green]Found {len(file_paths)} files to process.[/green]")
        
        if not Confirm.ask("Continue?"):
            return
        
        # Process files with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            self.console
        ) as progress:
            task = progress.add_task("[cyan]Processing files...", total=len(file_paths))
            
            options = {'re_tag_option': re_tag_option}
            batch_size = 10  # Process files in batches to avoid overwhelming the system
            
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]
                result = self.automator.process_multiple_files(batch, options)
                
                for file_result in result['file_results']:
                    if file_result['success']:
                        if file_result['message'].startswith('File skipped'):
                            progress.console.print(f"[yellow]⚠ Skipped: {file_result['file_path']}[/yellow]")
                        else:
                            progress.console.print(f"[green]✓ Processed: {file_result['file_path']}[/green]")
                    else:
                        progress.console.print(f"[red]✗ Failed: {file_result['file_path']} - {file_result['message']}[/red]")
                
                progress.update(task, advance=len(batch))
        
        self.console.print("\n[green]File processing completed![/green]")
    
    def _rename_tags_interactive(self):
        """Interactive tag renaming."""
        self.console.print(Panel("[bold cyan]Rename Tags[/bold cyan]"))
        
        # Get all tags
        all_tags = self.automator.get_all_tags()
        if not all_tags:
            self.console.print("[red]No tags found in the vault.[/red]")
            return
        
        # Display tags
        self._display_tags_table(all_tags, "Available Tags")
        
        # Get old tag
        old_tag = Prompt.ask("Enter the tag to rename")
        if old_tag not in all_tags:
            self.console.print(f"[red]Tag '{old_tag}' not found.[/red]")
            return
        
        # Get new tag
        new_tag = Prompt.ask("Enter the new tag name")
        
        # Confirm
        if not Confirm.ask(f"Rename '{old_tag}' to '{new_tag}' in all files?"):
            return
        
        # Process
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), self.console) as progress:
            task = progress.add_task("[cyan]Renaming tag...", total=None)
            result = self.automator.rename_tag(old_tag, new_tag)
            progress.update(task, completed=True)
        
        if result['success']:
            self.console.print(f"[green]✓ {result['message']}[/green]")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _merge_tags_interactive(self):
        """Interactive tag merging."""
        self.console.print(Panel("[bold cyan]Merge Tags[/bold cyan]"))
        
        # Get all tags
        all_tags = self.automator.get_all_tags()
        if not all_tags:
            self.console.print("[red]No tags found in the vault.[/red]")
            return
        
        # Display tags
        self._display_tags_table(all_tags, "Available Tags")
        
        # Get tags to merge
        tags_input = Prompt.ask("Enter tags to merge (comma-separated)")
        tags_to_merge = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Validate tags
        invalid_tags = [tag for tag in tags_to_merge if tag not in all_tags]
        if invalid_tags:
            self.console.print(f"[red]Invalid tags: {', '.join(invalid_tags)}[/red]")
            return
        
        # Get new tag name
        new_tag_name = Prompt.ask("Enter the new unified tag name")
        
        # Confirm
        if not Confirm.ask(f"Merge {len(tags_to_merge)} tags into '{new_tag_name}' in all files?"):
            return
        
        # Process
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), self.console) as progress:
            task = progress.add_task("[cyan]Merging tags...", total=None)
            result = self.automator.merge_tags(tags_to_merge, new_tag_name)
            progress.update(task, completed=True)
        
        if result['success']:
            self.console.print(f"[green]✓ {result['message']}[/green]")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _delete_tags_interactive(self):
        """Interactive tag deletion."""
        self.console.print(Panel("[bold cyan]Delete Tags[/bold cyan]"))
        
        # Get all tags
        all_tags = self.automator.get_all_tags()
        if not all_tags:
            self.console.print("[red]No tags found in the vault.[/red]")
            return
        
        # Display tags
        self._display_tags_table(all_tags, "Available Tags")
        
        # Get tags to delete
        tags_input = Prompt.ask("Enter tags to delete (comma-separated)")
        tags_to_delete = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        
        # Validate tags
        invalid_tags = [tag for tag in tags_to_delete if tag not in all_tags]
        if invalid_tags:
            self.console.print(f"[red]Invalid tags: {', '.join(invalid_tags)}[/red]")
            return
        
        # Confirm
        if not Confirm.ask(f"Delete {len(tags_to_delete)} tags from all files?"):
            return
        
        # Process
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), self.console) as progress:
            task = progress.add_task("[cyan]Deleting tags...", total=None)
            result = self.automator.delete_tags(tags_to_delete)
            progress.update(task, completed=True)
        
        if result['success']:
            self.console.print(f"[green]✓ {result['message']}[/green]")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _generate_aliases_interactive(self):
        """Interactive alias generation."""
        self.console.print(Panel("[bold cyan]Generate Tag Aliases[/bold cyan]"))
        
        # Ask for method
        method = Prompt.ask("Choose method", choices=["1", "2"], 
                           default="1",
                           show_choices=False,
                           show_default=False)
        
        if method == "1":
            self.console.print("1. Heuristic-based alias detection")
            result = self.automator.generate_suggested_aliases()
        else:
            self.console.print("2. AI-powered alias detection")
            result = self.automator.generate_ai_suggested_aliases()
        
        if result['success']:
            aliases = result['suggested_aliases']
            if aliases:
                self.console.print(f"\n[green]✓ {result['message']}[/green]")
                
                # Display aliases
                alias_table = Table(title="Suggested Aliases")
                alias_table.add_column("Alias", style="yellow")
                alias_table.add_column("Canonical", style="green")
                
                for alias, canonical in aliases.items():
                    alias_table.add_row(alias, canonical)
                
                self.console.print(alias_table)
                
                # Ask to save
                if Confirm.ask("Save these aliases?"):
                    self.automator.set_tag_aliases(aliases)
                    self.console.print("[green]✓ Aliases saved successfully[/green]")
            else:
                self.console.print("[yellow]No aliases suggested.[/yellow]")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _validate_tags_interactive(self):
        """Interactive tag validation."""
        self.console.print(Panel("[bold cyan]Validate Tags[/bold cyan]"))
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), self.console) as progress:
            task = progress.add_task("[cyan]Validating tags...", total=None)
            result = self.automator.validate_tags()
            progress.update(task, completed=True)
        
        if result['success']:
            report = result['validation_report']
            
            # Display summary
            summary_table = Table(show_header=False, box=None)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            
            summary_table.add_row("Total Tags", str(report['total_tags']))
            summary_table.add_row("Malformed Tags", str(len(report['malformed_tags'])))
            summary_table.add_row("Duplicate Groups", str(len(report['duplicate_tags'])))
            summary_table.add_row("Orphaned Tags", str(len(report['orphaned_tags'])))
            
            self.console.print(summary_table)
            
            # Display details if issues found
            if report['malformed_tags']:
                self.console.print("\n[red]Malformed Tags:[/red]")
                self._display_tags_table(report['malformed_tags'], "Tags with spaces, periods, or uppercase")
            
            if report['duplicate_tags']:
                self.console.print("\n[yellow]Duplicate Tag Groups:[/yellow]")
                for group in report['duplicate_tags']:
                    self.console.print(f"  • {', '.join(group)}")
            
            if report['orphaned_tags']:
                self.console.print("\n[blue]Orphaned Tags (used in only 1 file):[/blue]")
                self._display_tags_table(report['orphaned_tags'][:10], "First 10 orphaned tags")
                if len(report['orphaned_tags']) > 10:
                    self.console.print(f"  ... and {len(report['orphaned_tags']) - 10} more")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _display_vault_stats(self):
        """Display vault statistics."""
        self.console.print(Panel("[bold cyan]Vault Statistics[/bold cyan]"))
        
        result = self.automator.get_vault_stats()
        if result['success']:
            stats = result['stats']
            
            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")
            stats_table.add_column("Percentage", style="green")
            
            total_files = stats['total_files']
            tagged_pct = (stats['tagged_files'] / total_files * 100) if total_files > 0 else 0
            untagged_pct = (stats['untagged_files'] / total_files * 100) if total_files > 0 else 0
            ai_pct = (stats['ai_processed_files'] / total_files * 100) if total_files > 0 else 0
            
            stats_table.add_row("Total Files", str(stats['total_files']), "")
            stats_table.add_row("Tagged Files", str(stats['tagged_files']), f"{tagged_pct:.1f}%")
            stats_table.add_row("Untagged Files", str(stats['untagged_files']), f"{untagged_pct:.1f}%")
            stats_table.add_row("AI-Processed Files", str(stats['ai_processed_files']), f"{ai_pct:.1f}%")
            stats_table.add_row("Unique Tags", str(stats['total_tags']), "")
            
            self.console.print(stats_table)
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _configuration_menu(self):
        """Configuration menu."""
        while True:
            self.console.print(Panel("[bold cyan]Configuration[/bold cyan]"))
            
            config_table = Table(show_header=False, box=None)
            config_table.add_column("Option", style="green", width=3)
            config_table.add_column("Description", style="white")
            
            config_table.add_row("1", "View current configuration")
            config_table.add_row("2", "Edit AI prompt")
            config_table.add_row("3", "Manage excluded tags")
            config_table.add_row("4", "Manage excluded paths")
            config_table.add_row("5", "Back to main menu")
            
            self.console.print(config_table)
            
            choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self._view_configuration()
            elif choice == "2":
                self._edit_ai_prompt()
            elif choice == "3":
                self._manage_excluded_tags()
            elif choice == "4":
                self._manage_excluded_paths()
            elif choice == "5":
                break
    
    def _view_configuration(self):
        """View current configuration."""
        self.console.print(Panel("[bold cyan]Current Configuration[/bold cyan]"))
        
        config = self.automator.get_config()
        
        config_table = Table(show_header=False, box=None)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        
        for key, value in config.items():
            if isinstance(value, list):
                config_table.add_row(key, ", ".join(value))
            else:
                config_table.add_row(key, str(value))
        
        self.console.print(config_table)
        Prompt.ask("Press Enter to continue")
    
    def _edit_ai_prompt(self):
        """Edit AI prompt."""
        self.console.print(Panel("[bold cyan]Edit AI Prompt[/bold cyan]"))
        
        current_prompt = self.automator.get_ai_prompt()
        self.console.print("[yellow]Current AI prompt:[/yellow]")
        self.console.print(Panel(current_prompt, title="Current Prompt", border_style="blue"))
        
        if Confirm.ask("Edit the AI prompt?"):
            new_prompt = Prompt.ask("Enter new AI prompt (press Enter to keep current)", default=current_prompt)
            if new_prompt != current_prompt:
                self.automator.set_ai_prompt(new_prompt)
                self.console.print("[green]✓ AI prompt updated successfully[/green]")
    
    def _manage_excluded_tags(self):
        """Manage excluded tags."""
        self.console.print(Panel("[bold cyan]Manage Excluded Tags[/bold cyan]"))
        
        current_excluded = list(self.automator.excluded_tags)
        if current_excluded:
            self.console.print("[yellow]Currently excluded tags:[/yellow]")
            self._display_tags_table(current_excluded, "Excluded Tags")
        else:
            self.console.print("[yellow]No tags are currently excluded.[/yellow]")
        
        action = Prompt.ask("Action", choices=["1", "2", "3"], 
                           default="1",
                           show_choices=False,
                           show_default=False)
        
        if action == "1":  # Add tags
            tags_input = Prompt.ask("Enter tags to exclude (comma-separated)")
            new_excluded = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            current_excluded.extend(new_excluded)
            current_excluded = list(set(current_excluded))  # Remove duplicates
            
        elif action == "2":  # Remove tags
            if current_excluded:
                tags_input = Prompt.ask("Enter tags to remove from exclusion (comma-separated)")
                tags_to_remove = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                current_excluded = [tag for tag in current_excluded if tag not in tags_to_remove]
            else:
                self.console.print("[yellow]No tags to remove.[/yellow]")
                return
        
        elif action == "3":  # Back
            return
        
        # Update configuration
        self.automator.update_config({'excluded_tags': current_excluded})
        self.console.print("[green]✓ Excluded tags updated successfully[/green]")
    
    def _manage_excluded_paths(self):
        """Manage excluded paths."""
        self.console.print(Panel("[bold cyan]Manage Excluded Paths[/bold cyan]"))
        
        current_excluded = list(self.automator.excluded_paths)
        if current_excluded:
            self.console.print("[yellow]Currently excluded paths:[/yellow]")
            for path in current_excluded:
                self.console.print(f"  • {path}")
        else:
            self.console.print("[yellow]No paths are currently excluded.[/yellow]")
        
        action = Prompt.ask("Action", choices=["1", "2", "3"], 
                           default="1",
                           show_choices=False,
                           show_default=False)
        
        if action == "1":  # Add paths
            paths_input = Prompt.ask("Enter paths to exclude (comma-separated)")
            new_excluded = [path.strip() for path in paths_input.split(',') if path.strip()]
            current_excluded.extend(new_excluded)
            current_excluded = list(set(current_excluded))  # Remove duplicates
            
        elif action == "2":  # Remove paths
            if current_excluded:
                paths_input = Prompt.ask("Enter paths to remove from exclusion (comma-separated)")
                paths_to_remove = [path.strip() for path in paths_input.split(',') if path.strip()]
                current_excluded = [path for path in current_excluded if path not in paths_to_remove]
            else:
                self.console.print("[yellow]No paths to remove.[/yellow]")
                return
        
        elif action == "3":  # Back
            return
        
        # Update configuration
        self.automator.update_config({'excluded_paths': current_excluded})
        self.console.print("[green]✓ Excluded paths updated successfully[/green]")
    
    def _update_tag_database(self):
        """Update the tag database."""
        self.console.print(Panel("[bold cyan]Update Tag Database[/bold cyan]"))
        
        if Confirm.ask("This will rescan your entire vault for tags. Continue?"):
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), self.console) as progress:
                task = progress.add_task("[cyan]Scanning vault...", total=None)
                self.automator.update_tag_database()
                progress.update(task, completed=True)
            
            self.console.print("[green]✓ Tag database updated successfully[/green]")
    
    def _display_tags_table(self, tags, title):
        """Display a table of tags."""
        if not tags:
            self.console.print("[yellow]No tags to display.[/yellow]")
            return
        
        # Create columns for better display
        columns = 3
        table = Table(title=title, show_header=False, box=None)
        
        for i in range(columns):
            table.add_column(f"Tag {i+1}", style="cyan")
        
        # Add tags to table
        for i in range(0, len(tags), columns):
            row = tags[i:i+columns]
            while len(row) < columns:
                row.append("")
            table.add_row(*row)
        
        self.console.print(table)

def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="Obsidian Tag Automator CLI")
    parser.add_argument("-v", "--vault-path", help="Path to the Obsidian vault")
    parser.add_argument("-k", "--gemini-api-key", help="Gemini API key for AI tag suggestions")
    
    args = parser.parse_args()
    
    # Initialize and run the CLI
    cli = ObsidianTagAutomatorCLI(args.vault_path, args.gemini_api_key)
    cli.display_main_menu()

if __name__ == "__main__":
    main()
```

### File: `interfaces/web_interface.py`
```python
import os
import json
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import time
from datetime import datetime

from core.automator_core import ObsidianTagAutomatorCore

class ObsidianTagAutomatorWeb:
    """
    Web interface for the Obsidian Tag Automator.
    Provides REST API endpoints and serves the web frontend.
    """
    
    def __init__(self, vault_path=None, gemini_api_key=None):
        """
        Initialize the web interface.
        
        Args:
            vault_path (str or Path, optional): Path to the Obsidian vault.
            gemini_api_key (str, optional): Gemini API key for AI suggestions.
        """
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='../web/templates',
                        static_folder='../web/static')
        CORS(self.app)
        
        # Configure Flask
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # Initialize the core automator
        if vault_path is None:
            vault_path = self._detect_vault_path()
        
        self.automator = ObsidianTagAutomatorCore(vault_path, gemini_api_key)
        
        # Background task tracking
        self.background_tasks = {}
        
        # Register routes
        self._register_routes()
        
        # Start background task cleaner
        self._start_task_cleaner()
    
    def _detect_vault_path(self):
        """Detect the Obsidian vault path."""
        # Try to get from environment variable
        env_path = os.getenv('OBSIDIAN_VAULT_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Try to detect from current directory
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / ".obsidian").exists():
                return cwd
            cwd = cwd.parent
        
        # Default to current directory
        return Path.cwd()
    
    def _register_routes(self):
        """Register all Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard."""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status and vault information."""
            try:
                stats_result = self.automator.get_vault_stats()
                config = self.automator.get_config()
                
                response = {
                    'success': True,
                    'vault_path': str(self.automator.vault_path),
                    'ai_status': bool(self.automator.ai_integration.gemini_model),
                    'stats': stats_result['stats'] if stats_result['success'] else {},
                    'config': {
                        'excluded_tags_count': len(config.get('excluded_tags', [])),
                        'excluded_paths_count': len(config.get('excluded_paths', [])),
                        'ai_prompt_configured': bool(config.get('ai_prompt'))
                    }
                }
                return jsonify(response)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/files')
        def get_files():
            """Get list of markdown files in the vault."""
            try:
                files = []
                for root, _, file_names in os.walk(self.automator.vault_path):
                    for file_name in file_names:
                        if file_name.endswith('.md') and '.obsidian' not in root:
                            file_path = Path(root) / file_name
                            relative_path = file_path.relative_to(self.automator.vault_path)
                            files.append({
                                'name': file_name,
                                'path': str(relative_path),
                                'full_path': str(file_path),
                                'size': file_path.stat().st_size,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
                
                return jsonify({'success': True, 'files': files})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/tags')
        def get_tags():
            """Get all tags from the vault."""
            try:
                tags = self.automator.get_all_tags()
                return jsonify({'success': True, 'tags': tags})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/process-file', methods=['POST'])
        def process_file():
            """Process a single file."""
            try:
                data = request.get_json()
                file_path = data.get('file_path')
                options = data.get('options', {})
                
                if not file_path:
                    return jsonify({'success': False, 'error': 'File path is required'}), 400
                
                result = self.automator.process_file(file_path, options)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/process-multiple-files', methods=['POST'])
        def process_multiple_files():
            """Process multiple files as a background task."""
            try:
                data = request.get_json()
                file_paths = data.get('file_paths', [])
                options = data.get('options', {})
                
                if not file_paths:
                    return jsonify({'success': False, 'error': 'File paths are required'}), 400
                
                # Create background task
                task_id = str(uuid.uuid4())
                self.background_tasks[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'total': len(file_paths),
                    'result': None,
                    'start_time': datetime.now().isoformat()
                }
                
                # Start background thread
                thread = threading.Thread(
                    target=self._process_files_background,
                    args=(task_id, file_paths, options)
                )
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'File processing started'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/task-status/<task_id>')
        def get_task_status(task_id):
            """Get status of a background task."""
            try:
                if task_id not in self.background_tasks:
                    return jsonify({'success': False, 'error': 'Task not found'}), 404
                
                task = self.background_tasks[task_id]
                return jsonify({
                    'success': True,
                    'task': task
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/rename-tag', methods=['POST'])
        def rename_tag():
            """Rename a tag across all files."""
            try:
                data = request.get_json()
                old_tag = data.get('old_tag')
                new_tag = data.get('new_tag')
                
                if not old_tag or not new_tag:
                    return jsonify({'success': False, 'error': 'Both old_tag and new_tag are required'}), 400
                
                result = self.automator.rename_tag(old_tag, new_tag)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/merge-tags', methods=['POST'])
        def merge_tags():
            """Merge multiple tags into one."""
            try:
                data = request.get_json()
                tags_to_merge = data.get('tags_to_merge', [])
                new_tag_name = data.get('new_tag_name')
                
                if not tags_to_merge or not new_tag_name:
                    return jsonify({'success': False, 'error': 'tags_to_merge and new_tag_name are required'}), 400
                
                result = self.automator.merge_tags(tags_to_merge, new_tag_name)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/delete-tags', methods=['POST'])
        def delete_tags():
            """Delete specified tags from all files."""
            try:
                data = request.get_json()
                tags_to_delete = data.get('tags_to_delete', [])
                
                if not tags_to_delete:
                    return jsonify({'success': False, 'error': 'tags_to_delete is required'}), 400
                
                result = self.automator.delete_tags(tags_to_delete)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/generate-aliases', methods=['POST'])
        def generate_aliases():
            """Generate tag aliases."""
            try:
                data = request.get_json()
                method = data.get('method', 'heuristic')  # 'heuristic' or 'ai'
                
                if method == 'ai':
                    result = self.automator.generate_ai_suggested_aliases()
                else:
                    result = self.automator.generate_suggested_aliases()
                
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/save-aliases', methods=['POST'])
        def save_aliases():
            """Save tag aliases."""
            try:
                data = request.get_json()
                aliases = data.get('aliases', {})
                
                self.automator.set_tag_aliases(aliases)
                return jsonify({'success': True, 'message': 'Aliases saved successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get-aliases')
        def get_aliases():
            """Get current tag aliases."""
            try:
                aliases = self.automator.get_tag_aliases()
                return jsonify({'success': True, 'aliases': aliases})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/validate-tags')
        def validate_tags():
            """Validate all tags in the vault."""
            try:
                result = self.automator.validate_tags()
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/vault-stats')
        def vault_stats():
            """Get vault statistics."""
            try:
                result = self.automator.get_vault_stats()
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update-tag-database', methods=['POST'])
        def update_tag_database():
            """Update the tag database."""
            try:
                # Create background task
                task_id = str(uuid.uuid4())
                self.background_tasks[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'total': 100,  # Arbitrary total for progress
                    'result': None,
                    'start_time': datetime.now().isoformat()
                }
                
                # Start background thread
                thread = threading.Thread(
                    target=self._update_database_background,
                    args=(task_id,)
                )
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Tag database update started'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/config')
        def get_config():
            """Get current configuration."""
            try:
                config = self.automator.get_config()
                return jsonify({'success': True, 'config': config})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update-config', methods=['POST'])
        def update_config():
            """Update configuration."""
            try:
                data = request.get_json()
                new_config = data.get('config', {})
                
                self.automator.update_config(new_config)
                return jsonify({'success': True, 'message': 'Configuration updated successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/ai-prompt')
        def get_ai_prompt():
            """Get current AI prompt."""
            try:
                prompt = self.automator.get_ai_prompt()
                return jsonify({'success': True, 'prompt': prompt})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update-ai-prompt', methods=['POST'])
        def update_ai_prompt():
            """Update AI prompt."""
            try:
                data = request.get_json()
                new_prompt = data.get('prompt')
                
                if not new_prompt:
                    return jsonify({'success': False, 'error': 'Prompt is required'}), 400
                
                self.automator.set_ai_prompt(new_prompt)
                return jsonify({'success': True, 'message': 'AI prompt updated successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/file-content/<path:file_path>')
        def get_file_content(file_path):
            """Get content of a specific file."""
            try:
                # Security: Ensure file path is within vault
                full_path = self.automator.vault_path / file_path
                if not full_path.exists() or not str(full_path).startswith(str(self.automator.vault_path)):
                    return jsonify({'success': False, 'error': 'File not found or access denied'}), 404
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return jsonify({'success': True, 'content': content})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def _process_files_background(self, task_id, file_paths, options):
        """Process files in the background."""
        try:
            total_files = len(file_paths)
            processed_files = 0
            
            # Process files in batches to show progress
            batch_size = 5
            results = []
            
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]
                batch_result = self.automator.process_multiple_files(batch, options)
                results.extend(batch_result['file_results'])
                processed_files += len(batch)
                
                # Update progress
                self.background_tasks[task_id]['progress'] = (processed_files / total_files) * 100
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)
            
            # Task completed
            self.background_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'result': {
                    'total_files': total_files,
                    'processed_files': processed_files,
                    'results': results
                },
                'end_time': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.background_tasks[task_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
    
    def _update_database_background(self, task_id):
        """Update tag database in the background."""
        try:
            # Simulate progress
            for progress in range(0, 101, 10):
                self.background_tasks[task_id]['progress'] = progress
                time.sleep(0.2)
            
            # Actual update
            self.automator.update_tag_database()
            
            # Task completed
            self.background_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'result': {'message': 'Tag database updated successfully'},
                'end_time': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.background_tasks[task_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
    
    def _start_task_cleaner(self):
        """Start background thread to clean up old tasks."""
        def cleaner():
            while True:
                time.sleep(300)  # Clean every 5 minutes
                current_time = datetime.now()
                
                # Remove tasks older than 1 hour
                tasks_to_remove = []
                for task_id, task in self.background_tasks.items():
                    task_time = datetime.fromisoformat(task['start_time'])
                    if (current_time - task_time).total_seconds() > 3600:
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.background_tasks[task_id]
        
        thread = threading.Thread(target=cleaner)
        thread.daemon = True
        thread.start()
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the Flask application."""
        print(f"Starting Obsidian Tag Automator Web Interface...")
        print(f"Vault path: {self.automator.vault_path}")
        print(f"Access at: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def create_web_app(vault_path=None, gemini_api_key=None):
    """Factory function to create the web app."""
    web_interface = ObsidianTagAutomatorWeb(vault_path, gemini_api_key)
    return web_interface.app

if __name__ == '__main__':
    # Command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Obsidian Tag Automator Web Interface")
    parser.add_argument("-v", "--vault-path", help="Path to the Obsidian vault")
    parser.add_argument("-k", "--gemini-api-key", help="Gemini API key for AI tag suggestions")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create and run the web app
    web_app = ObsidianTagAutomatorWeb(args.vault_path, args.gemini_api_key)
    web_app.run(host=args.host, port=args.port, debug=args.debug)
```

Now let me know when you're ready for the web frontend files! We'll create the HTML templates and JavaScript files next.