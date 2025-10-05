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
            menu_table.add_row("6", "AI-powered tag analysis")
            menu_table.add_row("7", "Validate tags")
            menu_table.add_row("8", "View vault statistics")
            menu_table.add_row("9", "Configuration")
            menu_table.add_row("10", "Update tag database")
            menu_table.add_row("11", "Remove all tags from folder")
            menu_table.add_row("12", "Load and apply saved suggestions")
            menu_table.add_row("0", "Exit")

            self.console.print(menu_table)

            choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "0"])

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
                self._ai_tag_analysis_menu()
            elif choice == "7":
                self._display_vault_stats()
            elif choice == "8":
                self._configuration_menu()
            elif choice == "9":
                self._update_tag_database()
            elif choice == "10":
                self._remove_all_tags_from_folder_interactive()
            elif choice == "12":
                self._load_and_apply_saved_suggestions()
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
            # Get all markdown files, filtering based on re-tagging option and excluded paths
            file_paths = []
            for root, _, files in os.walk(self.automator.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                        # Check if file should be processed based on re-tagging option and excluded paths
                        if not self.automator._should_skip_file(file_path, re_tag_option):
                            file_paths.append(file_path)
        else:
            # Ask for specific files or patterns
            pattern = Prompt.ask("Enter file pattern (e.g., *.md, notes/*.md)")

            file_paths = []
            for root, _, files in os.walk(self.automator.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.match(pattern) and '.obsidian' not in file_path.parts:
                        # Check if file should be processed based on re-tagging option and excluded paths
                        if not self.automator._should_skip_file(file_path, re_tag_option):
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
            console=self.console
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
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

        # Display menu options
        self.console.print("\n[yellow]Available Methods:[/yellow]")
        self.console.print("1. Heuristic-based alias detection")
        self.console.print("2. AI-powered alias detection")

        # Ask for method
        method = Prompt.ask("\nChoose method", choices=["1", "2"], default="1")

        if method == "1":
            result = self.automator.generate_suggested_aliases()
        else:
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
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
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
    
    def _ai_tag_analysis_menu(self):
        """AI-powered tag analysis menu."""
        while True:
            self.console.print(Panel("[bold cyan]AI-Powered Tag Analysis[/bold cyan]"))

            analysis_table = Table(show_header=False, box=None)
            analysis_table.add_column("Option", style="green", width=3)
            analysis_table.add_column("Description", style="white")

            analysis_table.add_row("1", "AI-suggested tag merges (semantic analysis)")
            analysis_table.add_row("2", "AI-suggested tag deletions (identify redundant tags)")
            analysis_table.add_row("3", "Back to main menu")

            self.console.print(analysis_table)

            choice = Prompt.ask("\nSelect an analysis type", choices=["1", "2", "3"])

            if choice == "1":
                self._ai_suggested_merges()
            elif choice == "2":
                self._ai_suggested_deletions()
            elif choice == "3":
                break

    def _ai_suggested_merges(self):
        """Handle AI-suggested tag merges."""
        self.console.print(Panel("[bold cyan]AI-Suggested Tag Merges[/bold cyan]"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing tags for semantic merges...", total=None)
            result = self.automator.generate_ai_suggested_merges()
            progress.update(task, completed=True)

        if result['success']:
            merges = result['suggested_merges']
            if merges:
                self.console.print(f"\n[green]✓ {result['message']}[/green]")

                # Display suggested merges
                merge_table = Table(title="AI-Suggested Tag Merges")
                merge_table.add_column("From Tag", style="yellow")
                merge_table.add_column("→", style="white", justify="center")
                merge_table.add_column("To Tag", style="green")

                for from_tag, to_tag in merges.items():
                    merge_table.add_row(from_tag, "→", to_tag)

                self.console.print(merge_table)

                # Ask user what to do
                self.console.print("\n[yellow]Options:[/yellow]")
                self.console.print("1. Apply all merges")
                self.console.print("2. Select which merges to apply")
                self.console.print("3. Save to file for later review/editing")
                self.console.print("4. Skip (do nothing)")

                choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4"])

                if choice == "1":
                    # Apply all merges
                    for from_tag, to_tag in merges.items():
                        merge_result = self.automator.merge_tags([from_tag], to_tag)
                        if merge_result['success']:
                            self.console.print(f"[green]✓ Merged '{from_tag}' → '{to_tag}'[/green]")
                        else:
                            self.console.print(f"[red]✗ Failed to merge '{from_tag}': {merge_result['message']}[/red]")

                elif choice == "2":
                    # Interactive selection
                    selected_merges = {}
                    for from_tag, to_tag in merges.items():
                        if Confirm.ask(f"Apply merge: '{from_tag}' → '{to_tag}'?"):
                            selected_merges[from_tag] = to_tag

                    if selected_merges:
                        for from_tag, to_tag in selected_merges.items():
                            merge_result = self.automator.merge_tags([from_tag], to_tag)
                            if merge_result['success']:
                                self.console.print(f"[green]✓ Merged '{from_tag}' → '{to_tag}'[/green]")
                            else:
                                self.console.print(f"[red]✗ Failed to merge '{from_tag}': {merge_result['message']}[/red]")
                    else:
                        self.console.print("[yellow]No merges selected.[/yellow]")

                elif choice == "3":
                    # Save to file
                    import json
                    from datetime import datetime

                    filename = f"ai_merge_suggestions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    filepath = self.automator.vault_path / filename

                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump({
                                "timestamp": datetime.now().isoformat(),
                                "type": "merge_suggestions",
                                "suggestions": merges
                            }, f, indent=2)

                        self.console.print(f"[green]✓ Suggestions saved to: {filepath}[/green]")
                        self.console.print("[blue]You can edit this file and use option 10 in the main menu to apply selected suggestions.[/blue]")

                    except Exception as e:
                        self.console.print(f"[red]✗ Failed to save file: {e}[/red]")

                else:  # choice == "4"
                    self.console.print("[yellow]Merges not applied.[/yellow]")
            else:
                self.console.print("[yellow]No tag merges suggested.[/yellow]")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")

    def _ai_suggested_deletions(self):
        """Handle AI-suggested tag deletions."""
        self.console.print(Panel("[bold cyan]AI-Suggested Tag Deletions[/bold cyan]"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing tags for potential deletions...", total=None)
            result = self.automator.generate_ai_suggested_deletions()
            progress.update(task, completed=True)

        if result['success']:
            deletions = result['suggested_deletions']
            if deletions:
                self.console.print(f"\n[green]✓ {result['message']}[/green]")

                # Display suggested deletions
                deletion_table = Table(title="AI-Suggested Tag Deletions")
                deletion_table.add_column("Tag to Delete", style="red")

                for tag in deletions:
                    deletion_table.add_row(tag)

                self.console.print(deletion_table)

                # Ask user what to do
                self.console.print("\n[yellow]Options:[/yellow]")
                self.console.print("1. Delete all suggested tags")
                self.console.print("2. Select which tags to delete")
                self.console.print("3. Save to file for later review/editing")
                self.console.print("4. Skip (do nothing)")

                choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4"])

                if choice == "1":
                    # Delete all tags
                    delete_result = self.automator.delete_tags(deletions)
                    if delete_result['success']:
                        self.console.print(f"[green]✓ {delete_result['message']}[/green]")
                    else:
                        self.console.print(f"[red]✗ Failed to delete tags: {delete_result['message']}[/red]")

                elif choice == "2":
                    # Interactive selection
                    selected_deletions = []
                    for tag in deletions:
                        if Confirm.ask(f"Delete tag: '{tag}'?"):
                            selected_deletions.append(tag)

                    if selected_deletions:
                        delete_result = self.automator.delete_tags(selected_deletions)
                        if delete_result['success']:
                            self.console.print(f"[green]✓ {delete_result['message']}[/green]")
                        else:
                            self.console.print(f"[red]✗ Failed to delete tags: {delete_result['message']}[/red]")
                    else:
                        self.console.print("[yellow]No tags selected for deletion.[/yellow]")

                elif choice == "3":
                    # Save to file
                    import json
                    from datetime import datetime

                    filename = f"ai_deletion_suggestions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    filepath = self.automator.vault_path / filename

                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump({
                                "timestamp": datetime.now().isoformat(),
                                "type": "deletion_suggestions",
                                "suggestions": deletions
                            }, f, indent=2)

                        self.console.print(f"[green]✓ Suggestions saved to: {filepath}[/green]")
                        self.console.print("[blue]You can edit this file and use option 10 in the main menu to apply selected suggestions.[/blue]")

                    except Exception as e:
                        self.console.print(f"[red]✗ Failed to save file: {e}[/red]")

                else:  # choice == "4"
                    self.console.print("[yellow]Tags not deleted.[/yellow]")
            else:
                self.console.print("[yellow]No tag deletions suggested.[/yellow]")
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

        # Display menu options
        self.console.print("\n[yellow]Available Actions:[/yellow]")
        self.console.print("1. Add tags to exclude")
        self.console.print("2. Remove tags from exclusion")
        self.console.print("3. Back to configuration menu")

        action = Prompt.ask("\nSelect an action", choices=["1", "2", "3"])

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

        # Display menu options
        self.console.print("\n[yellow]Available Actions:[/yellow]")
        self.console.print("1. Add paths to exclude")
        self.console.print("2. Remove paths from exclusion")
        self.console.print("3. Back to configuration menu")

        action = Prompt.ask("\nSelect an action", choices=["1", "2", "3"])

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
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                *Progress.get_default_columns(),
                console=self.console
            ) as progress:
                task = progress.add_task("[cyan]Scanning vault...", total=None)
                self.automator.update_tag_database()
                progress.update(task, completed=True)

            self.console.print("[green]✓ Tag database updated successfully[/green]")

    def _remove_all_tags_from_folder_interactive(self):
        """Interactive removal of all tags from files in a folder."""
        self.console.print(Panel("[bold cyan]Remove All Tags from Folder[/bold cyan]"))

        # Ask for folder path
        folder_path = Prompt.ask("Enter folder path (relative to vault root, e.g., 'notes' or 'projects/work')")

        # Confirm
        if not Confirm.ask(f"Remove ALL tags from ALL files in folder '{folder_path}' and its subfolders?"):
            return

        # Process
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            *Progress.get_default_columns(),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Removing tags from folder...", total=None)
            result = self.automator.remove_all_tags_from_folder(folder_path)
            progress.update(task, completed=True)

        if result['success']:
            self.console.print(f"[green]✓ {result['message']}[/green]")
        else:
            self.console.print(f"[red]✗ {result['message']}[/red]")
    
    def _load_and_apply_saved_suggestions(self):
        """Load and apply saved suggestions from JSON files."""
        self.console.print(Panel("[bold cyan]Load and Apply Saved Suggestions[/bold cyan]"))

        # Find all suggestion files in the vault
        suggestion_files = []
        for file_path in self.automator.vault_path.rglob("*.json"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'type' in data and 'suggestions' in data:
                            if data['type'] in ['merge_suggestions', 'deletion_suggestions']:
                                suggestion_files.append(file_path)
                except (json.JSONDecodeError, IOError, KeyError):
                    continue

        if not suggestion_files:
            self.console.print("[yellow]No saved suggestion files found in your vault.[/yellow]")
            self.console.print("[blue]Save suggestions using option 3 in the AI analysis menus first.[/blue]")
            return

        # Display available files
        self.console.print("[green]Found suggestion files:[/green]")
        file_table = Table(show_header=False, box=None)
        file_table.add_column("Index", style="green", width=3)
        file_table.add_column("Filename", style="cyan")
        file_table.add_column("Type", style="yellow")
        file_table.add_column("Timestamp", style="white")

        for i, file_path in enumerate(suggestion_files, 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    suggestion_type = data.get('type', 'unknown')
                    timestamp = data.get('timestamp', 'unknown')
                    # Format timestamp
                    if timestamp != 'unknown':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass

                    type_display = "Tag Merges" if suggestion_type == "merge_suggestions" else "Tag Deletions" if suggestion_type == "deletion_suggestions" else suggestion_type
                    file_table.add_row(str(i), file_path.name, type_display, timestamp)
            except:
                file_table.add_row(str(i), file_path.name, "Error reading file", "")

        self.console.print(file_table)

        # Ask user to select a file
        if len(suggestion_files) == 1:
            choice = "1"
        else:
            choice = Prompt.ask(f"\nSelect a file to load (1-{len(suggestion_files)})", choices=[str(i) for i in range(1, len(suggestion_files) + 1)])

        selected_file = suggestion_files[int(choice) - 1]

        # Load the selected file
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            suggestion_type = data.get('type')
            suggestions = data.get('suggestions', {})

            if suggestion_type == 'merge_suggestions':
                self._apply_loaded_merge_suggestions(suggestions, selected_file.name)
            elif suggestion_type == 'deletion_suggestions':
                self._apply_loaded_deletion_suggestions(suggestions, selected_file.name)
            else:
                self.console.print(f"[red]Unknown suggestion type: {suggestion_type}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error loading file: {e}[/red]")

    def _apply_loaded_merge_suggestions(self, merges, filename):
        """Apply loaded merge suggestions."""
        self.console.print(f"\n[bold cyan]Loaded Merge Suggestions from {filename}[/bold cyan]")

        if not merges:
            self.console.print("[yellow]No merge suggestions found in file.[/yellow]")
            return

        # Display suggestions
        merge_table = Table(title="Loaded Merge Suggestions")
        merge_table.add_column("From Tag", style="yellow")
        merge_table.add_column("→", style="white", justify="center")
        merge_table.add_column("To Tag", style="green")

        for from_tag, to_tag in merges.items():
            merge_table.add_row(from_tag, "→", to_tag)

        self.console.print(merge_table)

        # Ask user what to do
        self.console.print("\n[yellow]Options:[/yellow]")
        self.console.print("1. Apply all merges")
        self.console.print("2. Select which merges to apply")
        self.console.print("3. Edit suggestions before applying")
        self.console.print("4. Skip (do nothing)")

        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4"])

        if choice == "1":
            # Apply all merges
            for from_tag, to_tag in merges.items():
                merge_result = self.automator.merge_tags([from_tag], to_tag)
                if merge_result['success']:
                    self.console.print(f"[green]✓ Merged '{from_tag}' → '{to_tag}'[/green]")
                else:
                    self.console.print(f"[red]✗ Failed to merge '{from_tag}': {merge_result['message']}[/red]")

        elif choice == "2":
            # Interactive selection
            selected_merges = {}
            for from_tag, to_tag in merges.items():
                if Confirm.ask(f"Apply merge: '{from_tag}' → '{to_tag}'?"):
                    selected_merges[from_tag] = to_tag

            if selected_merges:
                for from_tag, to_tag in selected_merges.items():
                    merge_result = self.automator.merge_tags([from_tag], to_tag)
                    if merge_result['success']:
                        self.console.print(f"[green]✓ Merged '{from_tag}' → '{to_tag}'[/green]")
                    else:
                        self.console.print(f"[red]✗ Failed to merge '{from_tag}': {merge_result['message']}[/red]")
            else:
                self.console.print("[yellow]No merges selected.[/yellow]")

        elif choice == "3":
            # Edit mode - allow user to modify suggestions
            self.console.print("[yellow]Edit mode: You can modify the suggestions before applying.[/yellow]")
            self.console.print("[blue]Current suggestions are shown above. You can:[/blue]")
            self.console.print("  • Remove unwanted merges by selecting 'No' when prompted")
            self.console.print("  • Or use option 2 above to selectively apply")

            # Fall back to selective application
            selected_merges = {}
            for from_tag, to_tag in merges.items():
                if Confirm.ask(f"Keep this merge: '{from_tag}' → '{to_tag}'?"):
                    selected_merges[from_tag] = to_tag

            if selected_merges:
                for from_tag, to_tag in selected_merges.items():
                    merge_result = self.automator.merge_tags([from_tag], to_tag)
                    if merge_result['success']:
                        self.console.print(f"[green]✓ Merged '{from_tag}' → '{to_tag}'[/green]")
                    else:
                        self.console.print(f"[red]✗ Failed to merge '{from_tag}': {merge_result['message']}[/red]")
            else:
                self.console.print("[yellow]No merges selected.[/yellow]")

        else:  # choice == "4"
            self.console.print("[yellow]Suggestions not applied.[/yellow]")

    def _apply_loaded_deletion_suggestions(self, deletions, filename):
        """Apply loaded deletion suggestions."""
        self.console.print(f"\n[bold cyan]Loaded Deletion Suggestions from {filename}[/bold cyan]")

        if not deletions:
            self.console.print("[yellow]No deletion suggestions found in file.[/yellow]")
            return

        # Display suggestions
        deletion_table = Table(title="Loaded Deletion Suggestions")
        deletion_table.add_column("Tag to Delete", style="red")

        for tag in deletions:
            deletion_table.add_row(tag)

        self.console.print(deletion_table)

        # Ask user what to do
        self.console.print("\n[yellow]Options:[/yellow]")
        self.console.print("1. Delete all suggested tags")
        self.console.print("2. Select which tags to delete")
        self.console.print("3. Edit suggestions before applying")
        self.console.print("4. Skip (do nothing)")

        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4"])

        if choice == "1":
            # Delete all tags
            delete_result = self.automator.delete_tags(deletions)
            if delete_result['success']:
                self.console.print(f"[green]✓ {delete_result['message']}[/green]")
            else:
                self.console.print(f"[red]✗ Failed to delete tags: {delete_result['message']}[/red]")

        elif choice == "2":
            # Interactive selection
            selected_deletions = []
            for tag in deletions:
                if Confirm.ask(f"Delete tag: '{tag}'?"):
                    selected_deletions.append(tag)

            if selected_deletions:
                delete_result = self.automator.delete_tags(selected_deletions)
                if delete_result['success']:
                    self.console.print(f"[green]✓ {delete_result['message']}[/green]")
                else:
                    self.console.print(f"[red]✗ Failed to delete tags: {delete_result['message']}[/red]")
            else:
                self.console.print("[yellow]No tags selected for deletion.[/yellow]")

        elif choice == "3":
            # Edit mode
            self.console.print("[yellow]Edit mode: You can modify the suggestions before applying.[/yellow]")
            self.console.print("[blue]Current suggestions are shown above. You can:[/blue]")
            self.console.print("  • Remove unwanted deletions by selecting 'No' when prompted")
            self.console.print("  • Or use option 2 above to selectively apply")

            # Fall back to selective application
            selected_deletions = []
            for tag in deletions:
                if Confirm.ask(f"Keep this deletion: '{tag}'?"):
                    selected_deletions.append(tag)

            if selected_deletions:
                delete_result = self.automator.delete_tags(selected_deletions)
                if delete_result['success']:
                    self.console.print(f"[green]✓ {delete_result['message']}[/green]")
                else:
                    self.console.print(f"[red]✗ Failed to delete tags: {delete_result['message']}[/red]")
            else:
                self.console.print("[yellow]No deletions selected.[/yellow]")

        else:  # choice == "4"
            self.console.print("[yellow]Suggestions not applied.[/yellow]")

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
