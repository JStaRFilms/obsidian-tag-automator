

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

Now I'll continue with the remaining core files and then move to the interfaces. Let me know when you're ready for the next part.