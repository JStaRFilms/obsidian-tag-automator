I'll help you implement the web UI for your Obsidian Tag Automator step by step. Let's start by creating the project structure and implementing the core components.

## Step 1: Project Structure Setup

First, let's create the folder structure as planned:

```
obsidian-tag-automator/
├── core/
│   ├── __init__.py
│   ├── automator_core.py
│   ├── tag_processor.py
│   ├── ai_integration.py
│   └── config_manager.py
├── interfaces/
│   ├── __init__.py
│   ├── cli_interface.py
│   └── web_interface.py
├── web/
│   ├── app.py
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       ├── index.html
│       └── components/
├── tag_automator_cli.py
├── requirements.txt
└── README.md
```

## Step 2: Core Module Implementation

Let's start with the core module. I'll create each file one by one.

### File: `core/__init__.py`
```python
# Core module for Obsidian Tag Automator
```

### File: `core/config_manager.py`
```python
import os
import json
from pathlib import Path

class ConfigManager:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.config_path = self.vault_path / "automator_config.json"
        self.config = self._load_config()

    def _load_config(self):
        """Load the automator configuration from `automator_config.json`."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    # Ensure exclusion lists are sets for efficient lookup
                    config_data['excluded_tags'] = list(set(config_data.get('excluded_tags', [])))
                    config_data['excluded_paths'] = list(set(config_data.get('excluded_paths', [])))
                    return config_data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}. Using default configuration.")
        
        return {'excluded_tags': [], 'excluded_paths': []}  # Initialize with empty lists if no config

    def save_config(self):
        """Save the current automator configuration to `automator_config.json`."""
        # Ensure excluded_tags and excluded_paths are saved as lists
        self.config['excluded_tags'] = list(self.config.get('excluded_tags', []))
        self.config['excluded_paths'] = list(self.config.get('excluded_paths', []))
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except IOError as e:
            print(f"Error saving config file: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
```

### File: `core/ai_integration.py`
```python
import os
import time
import random
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# Try to import Google Generative AI, with fallback classes if not available
try:
    import google.generativeai as genai
    from google.generativeai.types import BlockedPromptException, StopCandidateException
except ImportError:
    genai = None
    print("Warning: google-generativeai package not installed. AI tag suggestions will not be available.")
    
    # Define fallback exception classes
    class BlockedPromptException(Exception):
        pass
    
    class StopCandidateException(Exception):
        pass

class AIIntegration:
    def __init__(self, vault_path, gemini_api_key=None):
        self.vault_path = Path(vault_path)
        
        # Load environment variables from .env in the project root if not already loaded
        if not os.getenv('GEMINI_API_KEY'):
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
        
        if not gemini_api_key:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            
        if gemini_api_key and genai is not None:
            try:
                genai.configure(api_key=gemini_api_key)
                # Using gemini-2.5-flash-lite as it's generally available and cost-effective
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash-lite')
            except Exception as e:
                self.gemini_model = None
                print(f"Warning: Failed to configure Gemini API: {e}. AI tag suggestions will not be available.")
        elif gemini_api_key and genai is None:
            self.gemini_model = None
            print("Warning: google-generativeai package not installed. AI tag suggestions will not be available.")
        else:
            self.gemini_model = None
            print("Warning: Gemini API key not provided. AI tag suggestions will not be available.")
        
        # Constants
        self.MAX_AI_RETRIES = 10
        self.INITIAL_RETRY_DELAY = 1  # seconds

    def _default_ai_prompt(self):
        """Returns the default AI prompt string used for generating tag suggestions."""
        return """
You are an AI assistant for tagging Obsidian Markdown files. Your goal is to suggest relevant tags for a given document.
Document content:
---
{file_content}
---
Existing tags in the vault:
{all_existing_tags_csv}
Tags already present in this file (do NOT repeat these):
{existing_tags_csv}
Instructions:
- Suggest up to 15 highly relevant tags.
- Prefer tags from the existing vault list when suitable; otherwise propose concise, descriptive new tags.
- IMPORTANT: Tags must be lowercase, no spaces or periods. Use hyphens for multi-word tags (e.g., nextjs, ai-integration).
- Return ONLY a comma-separated list of tags. No extra text.
"""

    def get_ai_suggested_tags(self, file_content, existing_tags, all_existing_tags, ai_prompt=None):
        """
        Analyzes the provided file content using the configured Gemini AI model
        to suggest relevant tags.
        """
        if not self.gemini_model:
            print("Gemini API not configured. No AI suggestions available.")
            return []
        
        if ai_prompt is None:
            ai_prompt = self._default_ai_prompt()
        
        # Prepare CSV strings for prompt placeholders
        all_existing_tags_csv = ", ".join(all_existing_tags)
        existing_tags_csv = ", ".join(existing_tags)
        
        prompt = ai_prompt.format(
            file_content=file_content,
            all_existing_tags_csv=all_existing_tags_csv,
            existing_tags_csv=existing_tags_csv
        )
        
        for attempt in range(self.MAX_AI_RETRIES):
            try:
                response = self.gemini_model.generate_content(prompt)
                suggested_tags_str = response.text.strip()
                
                # Post-process suggested tags to remove spaces and periods, and convert to lowercase
                processed_suggested_tags = []
                for tag in suggested_tags_str.split(','):
                    cleaned_tag = tag.strip().lower()
                    cleaned_tag = re.sub(r'\s+', '-', cleaned_tag)  # Replace spaces with hyphens
                    cleaned_tag = re.sub(r'\.+', '', cleaned_tag)  # Remove periods
                    if cleaned_tag:
                        processed_suggested_tags.append(cleaned_tag)
                
                return processed_suggested_tags
                
            except (BlockedPromptException, StopCandidateException) as e:
                print(f"AI content generation blocked or stopped: {e}")
                if attempt < self.MAX_AI_RETRIES - 1:
                    delay = self.INITIAL_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{self.MAX_AI_RETRIES})...")
                    time.sleep(delay)
                else:
                    print(f"Max retries ({self.MAX_AI_RETRIES}) reached. No AI suggestions available.")
                    return []
                    
            except Exception as e:
                print(f"Error getting AI suggested tags: {e}")
                if "429" in str(e) and hasattr(e, 'response') and hasattr(e.response, 'json'):
                    try:
                        error_details = e.response.json()
                        retry_delay_seconds = error_details.get('retry_delay', {}).get('seconds')
                        if retry_delay_seconds:
                            delay = int(retry_delay_seconds) + random.uniform(0, 0.5)
                            print(f"API suggested retry after {delay:.2f} seconds (attempt {attempt + 1}/{self.MAX_AI_RETRIES})...")
                            time.sleep(delay)
                            continue
                    except (json.JSONDecodeError, AttributeError, TypeError):
                        pass
                
                if attempt < self.MAX_AI_RETRIES - 1:
                    delay = self.INITIAL_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{self.MAX_AI_RETRIES})...")
                    time.sleep(delay)
                else:
                    print(f"Max retries ({self.MAX_AI_RETRIES}) reached. No AI suggestions available.")
                    return []
        
        return []
```

### File: `core/tag_processor.py`
```python
import os
import re
import json
import yaml
import time
from pathlib import Path

class TagProcessor:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.tags_database_path = self.vault_path / "tags_database.json"
        self.tag_aliases_path = self.vault_path / "tag_aliases.json"
        self._all_vault_tags_cache = None
        self._cache_timestamp = 0

    def _load_tag_aliases(self):
        """Loads the tag alias map from `tag_aliases.json`."""
        if self.tag_aliases_path.exists():
            try:
                with open(self.tag_aliases_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tag aliases: {e}. Using empty aliases.")
        return {}

    def _save_tag_aliases(self, aliases):
        """Saves the provided tag aliases dictionary to `tag_aliases.json`."""
        try:
            with open(self.tag_aliases_path, 'w', encoding='utf-8') as f:
                json.dump(aliases, f, indent=2)
            print(f"Suggested aliases saved to {self.tag_aliases_path}")
        except IOError as e:
            print(f"Error saving tag aliases: {e}")

    def _clean_tag_format(self, tag_name):
        """Cleans a single tag name to ensure it adheres to Obsidian's recommended format."""
        cleaned_tag = tag_name.strip().lower()
        cleaned_tag = re.sub(r'\s+', '-', cleaned_tag)  # Replace spaces with hyphens
        cleaned_tag = re.sub(r'\.+', '', cleaned_tag)  # Remove periods
        return cleaned_tag

    def _apply_aliases(self, tags):
        """Applies defined tag aliases to a given list of tags."""
        aliases = self._load_tag_aliases()
        aliased_tags = []
        for tag in tags:
            aliased_tags.append(aliases.get(tag, tag))
        return aliased_tags

    def _extract_front_matter_and_content(self, file_path):
        """Extracts the YAML front matter block and the main content from a Markdown file."""
        try:
            # Read file with error handling for encoding issues
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encodings if UTF-8 fails
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading file {file_path} with fallback encoding: {e}")
                    return None, ""
            
            # Handle empty file
            if not content.strip():
                return None, ""
            
            # Check if the file starts with front matter delimiters
            if not content.lstrip().startswith('---'):
                return None, content
                
            # Find the first line break after the opening ---
            first_newline = content.find('\n')
            if first_newline == -1:
                return None, content  # No newline after opening ---
                
            # Find the end of the front matter (next --- after the first line)
            end_pos = content.find('\n---', first_newline + 1)
            
            # If no closing --- is found, treat as no front matter
            if end_pos == -1:
                return None, content
                
            # Extract front matter and content
            front_matter_raw = content[first_newline + 1:end_pos].strip()
            main_content = content[end_pos + 5:].lstrip('\n')
            
            # If front matter is empty or contains only whitespace, treat as no front matter
            if not front_matter_raw.strip():
                return None, content
                
            # Basic validation: check if the front matter looks like YAML
            has_valid_yaml = (
                ':' in front_matter_raw or  # Has at least one key-value pair
                front_matter_raw.strip() == '{}' or  # Empty dict
                front_matter_raw.strip() == '[]' or  # Empty array
                front_matter_raw.strip() == '~'  # Null value
            )
            
            if not has_valid_yaml:
                print(f"Warning: File {file_path} has malformed front matter. Treating as no front matter.")
                return None, content
                
            return front_matter_raw, main_content
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            # Try to return the content if we have it, otherwise empty string
            return None, content if 'content' in locals() else ""

    def _parse_front_matter(self, front_matter_raw):
        """Parses a raw YAML front matter string into a dictionary using PyYAML."""
        if not front_matter_raw:
            return {}
            
        # Pre-process the front matter to handle common issues
        try:
            # Remove any Markdown formatting that might be in the front matter
            cleaned = re.sub(r'\*\*([^\*]+)\*\*', r'\1', front_matter_raw)  # Remove **bold**
            cleaned = re.sub(r'\*([^\*]+)\*', r'\1', cleaned)  # Remove *italic*
            cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # Remove `code`
            
            # Handle template placeholders like {{date:YYYY-MM-DD}}
            cleaned = re.sub(r'\{\{[^}]*\}\}', '', cleaned)
            
            # Remove any lines that start with | (tables)
            cleaned = '\n'.join(line for line in cleaned.split('\n') if not line.strip().startswith('|'))
            
            # Try to parse the cleaned YAML
            parsed_data = yaml.safe_load(cleaned)
            
            # If parsing yields None or a non-dict, return an empty dict
            if not isinstance(parsed_data, dict):
                return {}
                
            # Ensure 'tags' is always a list, even if parsed as a single string
            if 'tags' in parsed_data:
                if isinstance(parsed_data['tags'], str):
                    # Handle string tags by splitting on commas and cleaning each tag
                    tags = [t.strip() for t in parsed_data['tags'].split(',') if t.strip()]
                    parsed_data['tags'] = tags
                elif not isinstance(parsed_data['tags'], list):
                    parsed_data['tags'] = [str(parsed_data['tags'])]
                    
            return parsed_data
            
        except yaml.YAMLError as e:
            # If we hit a YAML error, try to extract just the tags if they exist
            try:
                # Look for tags: in the front matter
                tags_match = re.search(r'^tags:\s*\[([^\]]*)\]', front_matter_raw, re.MULTILINE)
                if tags_match:
                    tags_str = tags_match.group(1)
                    tags = [t.strip(" '\"") for t in tags_str.split(',') if t.strip()]
                    return {'tags': tags}
                    
                # Look for tags: followed by a list on the next line
                tags_match = re.search(r'^tags:\s*$\s*((?:-\s*[^\n]+\n?)+)', front_matter_raw, re.MULTILINE)
                if tags_match:
                    tags_block = tags_match.group(1)
                    tags = [line.strip(" -\n'\"") for line in tags_block.split('\n') if line.strip()]
                    return {'tags': tags}
                    
            except Exception:
                pass
                
            # If we get here, we couldn't parse anything useful
            print(f"Warning: Could not parse front matter. Using empty front matter. Error: {str(e)[:100]}")
            return {}
            
        except Exception as e:
            print(f"Unexpected error parsing front matter: {e}")
            return {}

    def _serialize_front_matter(self, data):
        """Serializes a dictionary of front matter data back into a YAML front matter string."""
        if not data:
            return "---\n---\n"
            
        # Create a safe copy to avoid modifying the original
        safe_data = {}
        
        for key, value in data.items():
            # Handle None values
            if value is None:
                safe_data[key] = ""
            # Handle boolean values
            elif key == 'ai_processed':
                safe_data[key] = bool(value)
            # Handle tags list
            elif key == 'tags':
                if not isinstance(value, list):
                    value = [str(value)]
                # Clean each tag
                safe_data[key] = [self._clean_tag_format(tag) for tag in value if tag]
            # Handle string values
            elif isinstance(value, str):
                # Check if string contains newlines
                if '\n' in value:
                    # Use literal block style for multiline strings
                    safe_data[key] = f"|\n{self._indent_string(value, 2)}"
                else:
                    # Escape special YAML characters
                    safe_value = value.replace('"', '\\"')
                    safe_data[key] = safe_value
            # Handle other types (int, float, bool, etc.)
            else:
                safe_data[key] = value
                
        try:
            # Dump to YAML with specific formatting
            yaml_string = yaml.dump(
                safe_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,  # Preserve key order
                width=float("inf"),  # Prevent line wrapping
                explicit_start=False,
                explicit_end=False
            )
            
            # Clean up any double quotes that might have been added unnecessarily
            yaml_string = yaml_string.replace('\\"', '"')
            
            # Ensure proper line endings and clean up any empty lines
            yaml_lines = [line for line in yaml_string.splitlines() if line.strip()]
            
            return f"---\n" + "\n".join(yaml_lines) + "\n---\n"
            
        except Exception as e:
            print(f"Error serializing front matter: {e}")
            # Fallback to simple string representation if YAML serialization fails
            return f"---\n{str(safe_data)}\n---\n"

    def _indent_string(self, s, spaces=4):
        """Helper method to properly indent multiline strings for YAML."""
        indent = ' ' * spaces
        return '\n'.join(f"{indent}{line}" for line in s.split('\n'))

    def _get_all_tags_from_vault(self):
        """Scans the entire Obsidian vault to extract all unique, cleaned tags."""
        # Use cached data if available and recent (less than 5 minutes old)
        current_time = time.time()
        if self._all_vault_tags_cache and (current_time - self._cache_timestamp < 300):
            return self._all_vault_tags_cache
        
        all_vault_tags = set()
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                    front_matter_raw, _ = self._extract_front_matter_and_content(file_path)
                    if front_matter_raw:
                        parsed_front_matter = self._parse_front_matter(front_matter_raw)
                        file_tags = parsed_front_matter.get('tags', [])
                        for tag in file_tags:
                            all_vault_tags.add(self._clean_tag_format(tag))
        
        # Update cache
        self._all_vault_tags_cache = sorted(list(all_vault_tags))
        self._cache_timestamp = current_time
        
        return self._all_vault_tags_cache

    def _update_tag_database(self):
        """Updates the internal tag database by re-scanning the Obsidian vault."""
        print("Updating tag database...")
        all_tags = self._get_all_tags_from_vault()
        try:
            with open(self.tags_database_path, 'w', encoding='utf-8') as f:
                json.dump({"tags": all_tags}, f, indent=2)
            print("Tag database updated.")
        except IOError as e:
            print(f"Error saving tags database: {e}")

    def _load_tags_database(self):
        """Loads the existing tags database from `tags_database.json`."""
        if self.tags_database_path.exists():
            try:
                with open(self.tags_database_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("tags", [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tags database: {e}. Using empty database.")
        return []

    def process_file_tags(self, file_path, ai_suggested_tags, existing_tags, excluded_tags):
        """Process tags for a single file: combine existing and suggested tags, apply aliases, and clean."""
        # Apply aliases to AI suggested tags
        aliased_ai_suggested_tags = self._apply_aliases(ai_suggested_tags)
        
        # Combine existing and suggested tags, remove duplicates
        combined_tags = list(existing_tags)
        for tag in aliased_ai_suggested_tags:
            if tag not in combined_tags and tag not in excluded_tags:
                combined_tags.append(tag)
        
        # Sort and ensure uniqueness
        updated_tags = sorted(list(set(combined_tags)))
        
        # Apply final cleaning to all tags
        final_tags = [self._clean_tag_format(tag) for tag in updated_tags]
        final_tags = sorted(list(set(final_tags)))
        
        return final_tags

    def write_file_with_updated_tags(self, file_path, final_tags, main_content, existing_front_matter=None):
        """Write the file with updated tags in the front matter."""
        # Parse existing front matter or create new
        if existing_front_matter is None:
            front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
            parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
        else:
            parsed_front_matter = existing_front_matter
        
        # Update front matter with new tags and mark as processed
        parsed_front_matter['tags'] = final_tags
        parsed_front_matter['ai_processed'] = True
        
        # Serialize the updated front matter
        updated_front_matter = self._serialize_front_matter(parsed_front_matter)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_front_matter)
            # Only add an extra newline if there's content to follow
            if main_content.strip():
                f.write('\n' + main_content.lstrip('\n'))
```

### File: `core/automator_core.py`
```python
import os
import json
from pathlib import Path
from .config_manager import ConfigManager
from .ai_integration import AIIntegration
from .tag_processor import TagProcessor

class ObsidianTagAutomatorCore:
    """
    Core business logic for Obsidian Tag Automator.
    This class contains all the functionality without any UI dependencies.
    """
    
    def __init__(self, vault_path, gemini_api_key=None):
        """
        Initializes the ObsidianTagAutomator with the vault path and an optional Gemini API key.
        
        Args:
            vault_path (str or Path): The root path of the Obsidian vault.
            gemini_api_key (str, optional): API key for Google Gemini. If not provided,
                                            AI tag suggestions will be unavailable.
        """
        self.vault_path = Path(vault_path)
        
        # Initialize components
        self.config_manager = ConfigManager(vault_path)
        self.ai_integration = AIIntegration(vault_path, gemini_api_key)
        self.tag_processor = TagProcessor(vault_path)
        
        # Load configuration
        self.excluded_tags = set(self.config_manager.get('excluded_tags', []))
        self.excluded_paths = set(self.config_manager.get('excluded_paths', []))
        self.ai_prompt = self.config_manager.get('ai_prompt', self.ai_integration._default_ai_prompt())
        
        # Constants
        self.MAX_TAGS_PER_FILE = 15
        self.MAX_ALIAS_LENGTH_DIFF = 10

    def get_vault_path(self):
        """Returns the vault path."""
        return str(self.vault_path)

    def get_config(self):
        """Returns the current configuration."""
        return self.config_manager.config

    def update_config(self, new_config):
        """Updates the configuration with new values."""
        self.config_manager.config.update(new_config)
        self.config_manager.save_config()
        # Update internal state
        self.excluded_tags = set(self.config_manager.get('excluded_tags', []))
        self.excluded_paths = set(self.config_manager.get('excluded_paths', []))
        self.ai_prompt = self.config_manager.get('ai_prompt', self.ai_integration._default_ai_prompt())

    def get_ai_prompt(self):
        """Returns the current AI prompt."""
        return self.ai_prompt

    def set_ai_prompt(self, new_prompt):
        """Sets a new AI prompt and saves it to configuration."""
        self.ai_prompt = new_prompt
        self.config_manager.set('ai_prompt', new_prompt)

    def get_all_tags(self):
        """Returns all unique tags from the vault."""
        return self.tag_processor._get_all_tags_from_vault()

    def get_tag_aliases(self):
        """Returns the current tag aliases."""
        return self.tag_processor._load_tag_aliases()

    def set_tag_aliases(self, aliases):
        """Sets new tag aliases."""
        self.tag_processor._save_tag_aliases(aliases)

    def update_tag_database(self):
        """Updates the tag database by scanning the vault."""
        self.tag_processor._update_tag_database()

    def process_file(self, file_path, options=None):
        """
        Processes a single Obsidian Markdown file to suggest and update its tags.
        
        Args:
            file_path (str or Path): The path to the Markdown file to be processed.
            options (dict, optional): Processing options like re_tag_option, interactive, etc.
            
        Returns:
            dict: Result containing success status, message, and processed tags.
        """
        if options is None:
            options = {}
        
        file_path = Path(file_path)
        result = {
            'success': False,
            'message': '',
            'tags_added': [],
            'tags_removed': [],
            'final_tags': [],
            'file_path': str(file_path)
        }
        
        try:
            # Check if file should be skipped
            if self._should_skip_file(file_path, options.get('re_tag_option')):
                result['message'] = f"File skipped: {file_path}"
                result['success'] = True  # Not an error, just skipped
                return result
            
            # Extract front matter and content
            front_matter_raw, main_content = self.tag_processor._extract_front_matter_and_content(file_path)
            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw) if front_matter_raw else {}
            
            # Get existing tags
            existing_tags = set(parsed_front_matter.get('tags', []))
            original_tags = set(existing_tags)
            
            # Get AI suggested tags
            all_existing_tags = self.get_all_tags()
            ai_suggested_tags = self.ai_integration.get_ai_suggested_tags(
                main_content, list(existing_tags), all_existing_tags, self.ai_prompt
            )
            
            # Process tags (combine, apply aliases, clean)
            final_tags = self.tag_processor.process_file_tags(
                file_path, ai_suggested_tags, list(existing_tags), self.excluded_tags
            )
            
            # Limit to maximum tags per file
            if len(final_tags) > self.MAX_TAGS_PER_FILE:
                final_tags = final_tags[:self.MAX_TAGS_PER_FILE]
            
            # Write updated tags to file
            self.tag_processor.write_file_with_updated_tags(file_path, final_tags, main_content, parsed_front_matter)
            
            # Calculate what changed
            final_tags_set = set(final_tags)
            result['tags_added'] = list(final_tags_set - original_tags)
            result['tags_removed'] = list(original_tags - final_tags_set)
            result['final_tags'] = final_tags
            result['success'] = True
            result['message'] = f"Successfully processed {file_path}"
            
        except Exception as e:
            result['message'] = f"Error processing {file_path}: {str(e)}"
            result['success'] = False
        
        return result

    def process_multiple_files(self, file_paths, options=None):
        """
        Processes multiple files with progress tracking.
        
        Args:
            file_paths (list): List of file paths to process.
            options (dict, optional): Processing options.
            
        Returns:
            dict: Result containing overall success and individual file results.
        """
        if options is None:
            options = {}
        
        results = {
            'success': True,
            'total_files': len(file_paths),
            'processed_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'file_results': [],
            'total_tags_added': 0,
            'total_tags_removed': 0
        }
        
        for file_path in file_paths:
            file_result = self.process_file(file_path, options)
            results['file_results'].append(file_result)
            
            if file_result['success']:
                if file_result['message'].startswith('File skipped'):
                    results['skipped_files'] += 1
                else:
                    results['processed_files'] += 1
                    results['total_tags_added'] += len(file_result['tags_added'])
                    results['total_tags_removed'] += len(file_result['tags_removed'])
            else:
                results['failed_files'] += 1
                results['success'] = False
        
        return results

    def rename_tag(self, old_tag, new_tag):
        """
        Renames a tag across all files in the vault.
        
        Args:
            old_tag (str): The tag to be renamed.
            new_tag (str): The new tag name.
            
        Returns:
            dict: Result containing success status and files modified.
        """
        old_tag = self.tag_processor._clean_tag_format(old_tag)
        new_tag = self.tag_processor._clean_tag_format(new_tag)
        
        if old_tag == new_tag:
            return {
                'success': False,
                'message': 'Old and new tag names are the same',
                'files_modified': 0
            }
        
        result = {
            'success': True,
            'message': '',
            'files_modified': 0,
            'files_processed': 0,
            'failed_files': []
        }
        
        try:
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                        result['files_processed'] += 1
                        
                        try:
                            front_matter_raw, main_content = self.tag_processor._extract_front_matter_and_content(file_path)
                            if not front_matter_raw:
                                continue
                            
                            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw)
                            file_tags = parsed_front_matter.get('tags', [])
                            
                            # Check if file contains the old tag
                            if old_tag in file_tags:
                                # Replace the tag
                                updated_tags = [new_tag if tag == old_tag else tag for tag in file_tags]
                                parsed_front_matter['tags'] = updated_tags
                                
                                # Write back to file
                                self.tag_processor.write_file_with_updated_tags(file_path, updated_tags, main_content, parsed_front_matter)
                                result['files_modified'] += 1
                                
                        except Exception as e:
                            result['failed_files'].append({
                                'file_path': str(file_path),
                                'error': str(e)
                            })
            
            result['message'] = f"Renamed '{old_tag}' to '{new_tag}' in {result['files_modified']} files"
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"Error renaming tag: {str(e)}"
        
        return result

    def merge_tags(self, tags_to_merge, new_tag_name):
        """
        Merges multiple tags into a single tag across all files.
        
        Args:
            tags_to_merge (list): List of tags to merge.
            new_tag_name (str): The new unified tag name.
            
        Returns:
            dict: Result containing success status and files modified.
        """
        new_tag_name = self.tag_processor._clean_tag_format(new_tag_name)
        tags_to_merge = [self.tag_processor._clean_tag_format(tag) for tag in tags_to_merge]
        
        if new_tag_name in tags_to_merge:
            return {
                'success': False,
                'message': 'New tag name cannot be one of the tags to merge',
                'files_modified': 0
            }
        
        result = {
            'success': True,
            'message': '',
            'files_modified': 0,
            'files_processed': 0,
            'failed_files': []
        }
        
        try:
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                        result['files_processed'] += 1
                        
                        try:
                            front_matter_raw, main_content = self.tag_processor._extract_front_matter_and_content(file_path)
                            if not front_matter_raw:
                                continue
                            
                            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw)
                            file_tags = parsed_front_matter.get('tags', [])
                            
                            # Check if file contains any of the tags to merge
                            tags_to_replace = [tag for tag in file_tags if tag in tags_to_merge]
                            if tags_to_replace:
                                # Replace tags and ensure no duplicates
                                updated_tags = [new_tag_name if tag in tags_to_merge else tag for tag in file_tags]
                                updated_tags = list(set(updated_tags))  # Remove duplicates
                                
                                parsed_front_matter['tags'] = updated_tags
                                
                                # Write back to file
                                self.tag_processor.write_file_with_updated_tags(file_path, updated_tags, main_content, parsed_front_matter)
                                result['files_modified'] += 1
                                
                        except Exception as e:
                            result['failed_files'].append({
                                'file_path': str(file_path),
                                'error': str(e)
                            })
            
            result['message'] = f"Merged {len(tags_to_merge)} tags into '{new_tag_name}' in {result['files_modified']} files"
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"Error merging tags: {str(e)}"
        
        return result

    def delete_tags(self, tags_to_delete):
        """
        Deletes specified tags from all files in the vault.
        
        Args:
            tags_to_delete (list): List of tags to delete.
            
        Returns:
            dict: Result containing success status and files modified.
        """
        tags_to_delete = [self.tag_processor._clean_tag_format(tag) for tag in tags_to_delete]
        
        result = {
            'success': True,
            'message': '',
            'files_modified': 0,
            'files_processed': 0,
            'failed_files': []
        }
        
        try:
            for root, _, files in os.walk(self.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                        result['files_processed'] += 1
                        
                        try:
                            front_matter_raw, main_content = self.tag_processor._extract_front_matter_and_content(file_path)
                            if not front_matter_raw:
                                continue
                            
                            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw)
                            file_tags = parsed_front_matter.get('tags', [])
                            
                            # Check if file contains any of the tags to delete
                            tags_to_remove = [tag for tag in file_tags if tag in tags_to_delete]
                            if tags_to_remove:
                                # Remove the tags
                                updated_tags = [tag for tag in file_tags if tag not in tags_to_delete]
                                
                                parsed_front_matter['tags'] = updated_tags
                                
                                # Write back to file
                                self.tag_processor.write_file_with_updated_tags(file_path, updated_tags, main_content, parsed_front_matter)
                                result['files_modified'] += 1
                                
                        except Exception as e:
                            result['failed_files'].append({
                                'file_path': str(file_path),
                                'error': str(e)
                            })
            
            result['message'] = f"Deleted {len(tags_to_delete)} tags from {result['files_modified']} files"
            
        except Exception as e:
            result['success'] = False
            result['message'] = f"Error deleting tags: {str(e)}"
        
        return result

    def generate_suggested_aliases(self):
        """
        Generates suggested tag aliases by comparing all existing tags in the vault.
        
        Returns:
            dict: Result containing suggested aliases.
        """
        all_tags = self.get_all_tags()
        suggested_aliases = {}
        
        # Sort tags by length to process shorter tags first as potential canonical forms
        sorted_tags = sorted(all_tags, key=len)
        common_affixes = [
            '-ai', '-app', '-tool', '-system', '-bot', '-google', '-microsoft', '-openai', '-js', '-dev', '-web',
            'google-', 'microsoft-', 'apple-', 'amazon-', 'aws-', 'azure-', 'ibm-', 'meta-', 'open-', 'gen-', 'ai-', 'web-', 'dev-',
            'data-', 'tech-', 'design-', 'video-', 'content-', 'marketing-', 'business-', 'personal-', 'project-', 'creative-'
        ]
        
        for i, shorter_tag in enumerate(sorted_tags):
            for j, longer_tag in enumerate(sorted_tags):
                if i >= j:  # Ensure longer_tag is actually longer or different
                    continue
                    
                # Check if shorter_tag is a substring of longer_tag
                if shorter_tag in longer_tag:
                    # Calculate the parts before and after the shorter_tag
                    parts = longer_tag.split(shorter_tag, 1)  # Split only on the first occurrence
                    prefix = parts[0]
                    suffix = parts[1] if len(parts) > 1 else ''
                    
                    # Check if the prefix or suffix is a common affix or just a hyphen
                    is_alias_candidate = False
                    
                    # Case 1: Shorter tag is at the beginning (no prefix)
                    if not prefix:
                        if not suffix or suffix.startswith('-') or suffix in common_affixes:
                            is_alias_candidate = True
                    # Case 2: Shorter tag is at the end (no suffix)
                    elif not suffix:
                        if not prefix or prefix.endswith('-') or prefix in common_affixes:
                            is_alias_candidate = True
                    # Case 3: Shorter tag is in the middle (both prefix and suffix)
                    else:
                        if (prefix.endswith('-') or prefix in common_affixes) and \
                           (suffix.startswith('-') or suffix in common_affixes):
                            is_alias_candidate = True
                    
                    # Add a length difference constraint to avoid overly broad matches
                    if is_alias_candidate and len(longer_tag) - len(shorter_tag) <= self.MAX_ALIAS_LENGTH_DIFF:
                        # Ensure we don't overwrite a more specific alias if one already exists
                        if longer_tag not in suggested_aliases:
                            suggested_aliases[longer_tag] = shorter_tag
        
        return {
            'success': True,
            'message': f"Generated {len(suggested_aliases)} suggested aliases",
            'suggested_aliases': suggested_aliases
        }

    def generate_ai_suggested_aliases(self):
        """
        Uses AI to analyze existing tags and suggest potential aliases.
        
        Returns:
            dict: Result containing AI-suggested aliases.
        """
        if not self.ai_integration.gemini_model:
            return {
                'success': False,
                'message': 'Gemini API not configured. Using heuristic-based alias suggestions.',
                'suggested_aliases': self.generate_suggested_aliases()['suggested_aliases']
            }
        
        all_tags = self.get_all_tags()
        if not all_tags:
            return {
                'success': False,
                'message': 'No tags found in the vault to analyze for aliases.',
                'suggested_aliases': {}
            }
        
        # Create a prompt for the AI to suggest aliases
        prompt = f"""
You are an AI assistant for identifying tag aliases in an Obsidian vault. Your goal is to analyze the list of tags and suggest aliases where multiple tags represent the same concept.
Here is the list of all tags in the vault:
{', '.join(all_tags)}
Instructions:
1. Identify tags that are variations of each other (e.g., 'nextjs', 'next-js', 'next.js').
2. For each group of related tags, choose the most concise and standard form as the canonical tag.
3. Return a JSON object where keys are the alias tags and values are their canonical tags.
4. Only suggest aliases where you are confident they represent the same concept.
5. Format your response as a valid JSON object only, with no additional text.
Example response format:
{{
  "next-js": "nextjs",
  "react.js": "reactjs",
  "ai-tools": "aitools"
}}
"""
        
        try:
            response = self.ai_integration.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse the response as JSON
            try:
                suggested_aliases = json.loads(response_text)
                # Validate that the response is a dictionary
                if not isinstance(suggested_aliases, dict):
                    return {
                        'success': False,
                        'message': 'AI response is not a valid dictionary. Falling back to heuristic suggestions.',
                        'suggested_aliases': self.generate_suggested_aliases()['suggested_aliases']
                    }
                
                # Clean the suggested aliases
                cleaned_aliases = {}
                for alias, canonical in suggested_aliases.items():
                    cleaned_alias = self.tag_processor._clean_tag_format(alias)
                    cleaned_canonical = self.tag_processor._clean_tag_format(canonical)
                    if cleaned_alias != cleaned_canonical:  # Don't alias a tag to itself
                        cleaned_aliases[cleaned_alias] = cleaned_canonical
                
                return {
                    'success': True,
                    'message': f"AI suggested {len(cleaned_aliases)} potential aliases.",
                    'suggested_aliases': cleaned_aliases
                }
                
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'message': f'Failed to parse AI response as JSON: {e}. Falling back to heuristic suggestions.',
                    'suggested_aliases': self.generate_suggested_aliases()['suggested_aliases']
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting AI suggested aliases: {e}. Falling back to heuristic suggestions.',
                'suggested_aliases': self.generate_suggested_aliases()['suggested_aliases']
            }

    def validate_tags(self):
        """
        Validates all tags in the vault and returns a report of issues.
        
        Returns:
            dict: Result containing validation report.
        """
        all_tags = self.get_all_tags()
        validation_report = {
            'total_tags': len(all_tags),
            'invalid_tags': [],
            'duplicate_tags': [],
            'orphaned_tags': [],
            'malformed_tags': []
        }
        
        # Check for malformed tags (spaces, periods, uppercase)
        for tag in all_tags:
            if ' ' in tag or '.' in tag or tag != tag.lower():
                validation_report['malformed_tags'].append(tag)
        
        # Check for duplicate tags (case-insensitive)
        tag_counts = {}
        for tag in all_tags:
            lower_tag = tag.lower()
            tag_counts[lower_tag] = tag_counts.get(lower_tag, 0) + 1
        
        for lower_tag, count in tag_counts.items():
            if count > 1:
                # Find all variations of this tag
                variations = [tag for tag in all_tags if tag.lower() == lower_tag]
                validation_report['duplicate_tags'].append(variations)
        
        # Check for orphaned tags (tags that appear in very few files)
        tag_usage = {}
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                    try:
                        front_matter_raw, _ = self.tag_processor._extract_front_matter_and_content(file_path)
                        if front_matter_raw:
                            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw)
                            file_tags = parsed_front_matter.get('tags', [])
                            for tag in file_tags:
                                cleaned_tag = self.tag_processor._clean_tag_format(tag)
                                tag_usage[cleaned_tag] = tag_usage.get(cleaned_tag, 0) + 1
                    except Exception:
                        continue
        
        # Consider tags used in only 1 file as potentially orphaned
        for tag, usage_count in tag_usage.items():
            if usage_count == 1:
                validation_report['orphaned_tags'].append(tag)
        
        return {
            'success': True,
            'message': 'Tag validation completed',
            'validation_report': validation_report
        }

    def get_vault_stats(self):
        """
        Returns statistics about the vault.
        
        Returns:
            dict: Vault statistics.
        """
        stats = {
            'total_files': 0,
            'tagged_files': 0,
            'untagged_files': 0,
            'total_tags': 0,
            'ai_processed_files': 0
        }
        
        all_tags = set()
        
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                    stats['total_files'] += 1
                    
                    try:
                        front_matter_raw, _ = self.tag_processor._extract_front_matter_and_content(file_path)
                        if front_matter_raw:
                            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw)
                            file_tags = parsed_front_matter.get('tags', [])
                            
                            if file_tags:
                                stats['tagged_files'] += 1
                                all_tags.update(file_tags)
                            else:
                                stats['untagged_files'] += 1
                            
                            if parsed_front_matter.get('ai_processed'):
                                stats['ai_processed_files'] += 1
                        else:
                            stats['untagged_files'] += 1
                    except Exception:
                        stats['untagged_files'] += 1
        
        stats['total_tags'] = len(all_tags)
        
        return {
            'success': True,
            'message': 'Vault statistics retrieved',
            'stats': stats
        }

    def _should_skip_file(self, file_path, re_tag_option):
        """
        Determines whether a given Markdown file should be skipped during the tagging process.
        
        Args:
            file_path (Path): The full path to the Markdown file being considered.
            re_tag_option (str): A string indicating the re-tagging preference.
            
        Returns:
            bool: True if the file should be skipped, False otherwise.
        """
        # Check if file path is excluded
        relative_file_path = str(file_path.relative_to(self.vault_path)).replace('\\', '/')
        relative_file_path_parts = relative_file_path.split('/')
        
        for excluded_path_str in self.excluded_paths:
            excluded_path_parts = excluded_path_str.split('/')
            # Check if the excluded path is a prefix of the file path's components
            if len(relative_file_path_parts) >= len(excluded_path_parts) and \
               relative_file_path_parts[:len(excluded_path_parts)] == excluded_path_parts:
                return True
        
        # Get front matter to check re-tagging options
        front_matter_raw, _ = self.tag_processor._extract_front_matter_and_content(file_path)
        parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw) if front_matter_raw else {}
        
        # Check re-tagging options
        if re_tag_option == '1':  # Only process files that have NOT been AI-tagged before
            if parsed_front_matter.get('ai_processed'):
                return True
                
        elif re_tag_option == '3':  # Only re-tag files that have existing tags but are NOT AI-tagged
            if parsed_front_matter.get('ai_processed') or not parsed_front_matter.get('tags'):
                return True
                
        elif re_tag_option == '4':  # Do NOT re-tag any files that already have tags
            if parsed_front_matter.get('tags'):
                return True
                
        return False
```

Now let's move to the interface adapters. Let me know when you're ready for the next part!