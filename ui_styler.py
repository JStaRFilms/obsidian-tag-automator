# ui_styler.py
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
import time

# Define a custom theme for that "agentic" look
custom_theme = Theme({
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold cyan",
    "highlight": "bold magenta",
    "title": "bold blue underline",
    "menu": "cyan",
    "prompt": "green"
})

console = Console(theme=custom_theme)

class AgenticUI:
    def __init__(self):
        self.console = console
    
    def display_title(self, title):
        self.console.print(Panel(f"[title]{title}[/title]", style="info", expand=False))
    
    def display_menu(self, options):
        table = Table(show_header=False, box=None, expand=False)
        table.add_column("Option", style="menu", width=5)
        table.add_column("Description", style="white")
        
        for i, option in enumerate(options, 1):
            table.add_row(str(i), option)
        
        self.console.print(table)
    
    def display_success(self, message):
        self.console.print(f"[success]✓[/success] {message}")
    
    def display_error(self, message):
        self.console.print(f"[error]✗[/error] {message}")
    
    def display_warning(self, message):
        self.console.print(f"[warning]⚠[/warning] {message}")
    
    def display_info(self, message):
        self.console.print(f"[info]ℹ[/info] {message}")
    
    def display_progress(self, task_name, total):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            self.console
        )
    
    def get_user_choice(self, prompt, options=None):
        if options:
            return Prompt.ask(f"[prompt]{prompt}[/prompt]", choices=options)
        return Prompt.ask(f"[prompt]{prompt}[/prompt]")
    
    def confirm_action(self, prompt):
        return Confirm.ask(f"[prompt]{prompt}[/prompt]")
    
    def display_tag_table(self, title, tags):
        table = Table(title=title)
        table.add_column("Tag", style="highlight")
        
        for tag in tags:
            table.add_row(tag)
        
        self.console.print(table)
    
    def display_file_processing(self, file_path, status):
        if status == "processing":
            self.console.print(f"[info]Processing:[/info] {file_path}")
        elif status == "success":
            self.console.print(f"[success]Completed:[/success] {file_path}")
        elif status == "skipped":
            self.console.print(f"[warning]Skipped:[/warning] {file_path}")
