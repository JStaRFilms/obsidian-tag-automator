import os
import re
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Constants for better maintainability
MAX_TAGS_PER_FILE = 15
MAX_AI_RETRIES = 10
INITIAL_RETRY_DELAY = 1  # seconds
MAX_ALIAS_LENGTH_DIFF = 10

# Try to import the tag extractor, with fallback if not available
try:
    from tag_extractor import ObsidianTagExtractor
except ImportError:
    print("Warning: tag_extractor module not found. Some functionality may be limited.")
    ObsidianTagExtractor = None

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


class ObsidianTagAutomator:
    """
    Automates tag management within an Obsidian vault, including AI-driven tag suggestions,
    tag cleaning, aliasing, exclusion, renaming, merging, and validation.
    It interacts with Markdown files' YAML front matter to read and update tags,
    and uses a Gemini AI model for intelligent tag suggestions.
    """
    
    def __init__(self, vault_path, gemini_api_key=None):
        """
        Initializes the ObsidianTagAutomator with the vault path and an optional Gemini API key.
        
        Args:
            vault_path (str or Path): The root path of the Obsidian vault.
            gemini_api_key (str, optional): API key for Google Gemini. If not provided,
                                            AI tag suggestions will be unavailable.
        """
        # Load environment variables from .env in the project root if not already loaded
        if not os.getenv('GEMINI_API_KEY'):
            env_path = Path(__file__).parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
            
        self.vault_path = Path(vault_path)
        
        # Initialize tag extractor if available
        if ObsidianTagExtractor:
            self.tag_extractor = ObsidianTagExtractor(vault_path)
        else:
            # Create a minimal fallback tag extractor
            self.tag_extractor = type('FallbackTagExtractor', (), {
                'scan_vault': lambda: None,
                'save_tags_to_json': lambda x: None,
                'suggest_tags_for_content': lambda x, y: [],
                'tags': set()
            })()
        
        # Configure Gemini AI model if API key is provided or present in environment
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
        
        # Define paths for configuration and tag databases
        self.tags_database_path = self.vault_path / "tags_database.json"
        self.config_path = self.vault_path / "automator_config.json"
        
        # Load existing tag aliases and automator configuration
        self.tag_aliases = self._load_tag_aliases()
        self.config = self._load_config()
        
        # Initialize AI prompt and exclusion lists from configuration
        self.ai_prompt = self.config.get('ai_prompt', self._default_ai_prompt())
        # Ensure excluded_tags and excluded_paths are always sets for efficient lookups
        self.excluded_tags = set(self.config.get('excluded_tags', []))
        self.excluded_paths = set(self.config.get('excluded_paths', []))
        
        # Cache for all vault tags to avoid repeated scanning
        self._all_vault_tags_cache = None
        self._cache_timestamp = 0
    
    def _default_ai_prompt(self):
        """
        Returns the default AI prompt string used for generating tag suggestions.
        This prompt guides the Gemini model on how to analyze document content
        and suggest relevant, properly formatted tags from the vault's existing tags.
        """
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
    
    def _load_config(self):
        """
        Loads the automator configuration from `automator_config.json`.
        Initializes with empty lists for excluded tags and paths if the file does not exist.
        
        Returns:
            dict: The loaded configuration data.
        """
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
    
    def _save_config(self):
        """
        Saves the current automator configuration to `automator_config.json`.
        Ensures that `excluded_tags` and `excluded_paths` are saved as lists.
        """
        # Ensure excluded_tags and excluded_paths are saved as lists
        self.config['excluded_tags'] = list(self.excluded_tags)
        self.config['excluded_paths'] = list(self.excluded_paths)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except IOError as e:
            print(f"Error saving config file: {e}")
    
    def get_ai_prompt(self):
        """
        Retrieves the current AI prompt string used for tag suggestions.
        
        Returns:
            str: The current AI prompt.
        """
        return self.ai_prompt
    
    def set_ai_prompt(self, new_prompt):
        """
        Sets a new AI prompt string and saves it to the configuration file.
        
        Args:
            new_prompt (str): The new AI prompt string to be set.
        """
        self.ai_prompt = new_prompt
        self.config['ai_prompt'] = new_prompt
        self._save_config()
    
    def _generate_suggested_aliases(self):
        """
        Generates suggested tag aliases by comparing all existing tags in the vault.
        It identifies potential aliases where a longer tag contains a shorter tag,
        and the difference is primarily due to common prefixes, suffixes, or hyphens.
        
        Returns:
            dict: A dictionary where keys are suggested alias tags (longer forms)
                  and values are their corresponding canonical tags (shorter forms).
        """
        self._update_tag_database()  # Ensure tag database is fresh
        all_tags = self._load_tags_database()
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
                    if is_alias_candidate and len(longer_tag) - len(shorter_tag) <= MAX_ALIAS_LENGTH_DIFF:
                        # Ensure we don't overwrite a more specific alias if one already exists
                        if longer_tag not in suggested_aliases:
                            suggested_aliases[longer_tag] = shorter_tag
        
        return suggested_aliases
    
    def _generate_ai_suggested_aliases(self):
        """
        Uses AI to analyze existing tags and suggest potential aliases.
        This method sends the list of all tags to the AI and asks it to identify
        tags that could be aliases of each other (e.g., 'next-js' and 'nextjs').
        
        Returns:
            dict: A dictionary where keys are potential alias tags and values are their suggested canonical forms.
        """
        if not self.gemini_model:
            print("Gemini API not configured. Using heuristic-based alias suggestions.")
            return self._generate_suggested_aliases()  # Fall back to the original method
        
        all_tags = self._get_all_tags_from_vault()
        if not all_tags:
            print("No tags found in the vault to analyze for aliases.")
            return {}
        
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
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse the response as JSON
            try:
                suggested_aliases = json.loads(response_text)
                # Validate that the response is a dictionary
                if not isinstance(suggested_aliases, dict):
                    print("AI response is not a valid dictionary. Falling back to heuristic suggestions.")
                    return self._generate_suggested_aliases()
                
                # Clean the suggested aliases
                cleaned_aliases = {}
                for alias, canonical in suggested_aliases.items():
                    cleaned_alias = self._clean_tag_format(alias)
                    cleaned_canonical = self._clean_tag_format(canonical)
                    if cleaned_alias != cleaned_canonical:  # Don't alias a tag to itself
                        cleaned_aliases[cleaned_alias] = cleaned_canonical
                
                print(f"AI suggested {len(cleaned_aliases)} potential aliases.")
                return cleaned_aliases
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse AI response as JSON: {e}. Falling back to heuristic suggestions.")
                return self._generate_suggested_aliases()
                
        except Exception as e:
            print(f"Error getting AI suggested aliases: {e}. Falling back to heuristic suggestions.")
            return self._generate_suggested_aliases()

    def _save_tag_aliases(self, aliases):
        """
        Saves the provided tag aliases dictionary to `tag_aliases.json`.
        
        Args:
            aliases (dict): A dictionary where keys are alias tags (the forms to be replaced)
                            and values are their corresponding canonical tags (the preferred forms).
        """
        alias_path = self.vault_path / "tag_aliases.json"
        try:
            with open(alias_path, 'w', encoding='utf-8') as f:
                json.dump(aliases, f, indent=2)
            print(f"Suggested aliases saved to {alias_path}")
        except IOError as e:
            print(f"Error saving tag aliases: {e}")
    
    def _load_tag_aliases(self):
        """
        Loads the tag alias map from `tag_aliases.json`.
        Returns an empty dictionary if the file does not exist.
        
        Returns:
            dict: The loaded tag alias map.
        """
        alias_path = self.vault_path / "tag_aliases.json"
        if alias_path.exists():
            try:
                with open(alias_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tag aliases: {e}. Using empty aliases.")
        
        return {}
    
    def _apply_aliases(self, tags):
        """
        Applies defined tag aliases to a given list of tags.
        
        Args:
            tags (list): A list of tags (strings) to which aliases should be applied.
            
        Returns:
            list: A new list containing the tags after alias application.
        """
        aliased_tags = []
        for tag in tags:
            aliased_tags.append(self.tag_aliases.get(tag, tag))
        return aliased_tags
    
    def _clean_tag_format(self, tag_name):
        """
        Cleans a single tag name to ensure it adheres to Obsidian's recommended format.
        
        Args:
            tag_name (str): The original tag name string.
            
        Returns:
            str: The cleaned and formatted tag name.
        """
        cleaned_tag = tag_name.strip().lower()
        cleaned_tag = re.sub(r'\s+', '-', cleaned_tag)  # Replace spaces with hyphens
        cleaned_tag = re.sub(r'\.+', '', cleaned_tag)  # Remove periods
        return cleaned_tag
    
    def _load_tags_database(self):
        """
        Loads the existing tags database from `tags_database.json`.
        
        Returns:
            list: A list of tags (strings) from the database. Returns an empty list
                  if the file does not exist or is empty.
        """
        if self.tags_database_path.exists():
            try:
                with open(self.tags_database_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("tags", [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading tags database: {e}. Using empty database.")
        
        return []
    
    def _update_tag_database(self):
        """
        Updates the internal tag database by re-scanning the Obsidian vault.
        """
        print("Updating tag database...")
        if hasattr(self.tag_extractor, 'scan_vault') and hasattr(self.tag_extractor, 'save_tags_to_json'):
            self.tag_extractor.scan_vault()
            self.tag_extractor.save_tags_to_json(self.tags_database_path)
            # Invalidate cache
            self._all_vault_tags_cache = None
        print("Tag database updated.")
    
    def _extract_front_matter_and_content(self, file_path):
        """
        Extracts the YAML front matter block and the main content from a Markdown file.
        
        Args:
            file_path (Path): The path to the Markdown file.
            
        Returns:
            tuple: A tuple containing:
                   - str: The raw YAML front matter content (excluding the `---` delimiters),
                          or None if no front matter is found.
                   - str: The main content of the file, following the front matter (or the
                          entire content if no front matter is present).
        """
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
        """
        Parses a raw YAML front matter string into a dictionary using PyYAML.
        
        Args:
            front_matter_raw (str): The raw string content of the YAML front matter
                                    (without the `---` delimiters).
            
        Returns:
            dict: A dictionary representing the parsed front matter.
        """
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
        """
        Serializes a dictionary of front matter data back into a YAML front matter string
        using PyYAML.
        
        Args:
            data (dict): A dictionary containing the front matter keys and values.
            
        Returns:
            str: The formatted YAML front matter block, including the `---` delimiters.
        """
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
        """
        Helper method to properly indent multiline strings for YAML.
        
        Args:
            s (str): The string to indent.
            spaces (int): Number of spaces to use for indentation.
            
        Returns:
            str: The indented string.
        """
        indent = ' ' * spaces
        return '\n'.join(f"{indent}{line}" for line in s.split('\n'))
    
    def _get_ai_suggested_tags(self, file_content, existing_tags):
        """
        Analyzes the provided file content using the configured Gemini AI model
        to suggest relevant tags.
        
        Args:
            file_content (str): The main textual content of the Markdown file.
            existing_tags (list): A list of tags already present in the file's front matter.
            
        Returns:
            list: A list of cleaned, AI-suggested tags (strings) that are not
                  already in `existing_tags`. Returns an empty list if no
                  suggestions are generated or if the AI is not configured.
        """
        if not self.gemini_model:
            print("Gemini API not configured. Using basic tag suggestion.")
            if hasattr(self.tag_extractor, 'suggest_tags_for_content'):
                return self.tag_extractor.suggest_tags_for_content(file_content, existing_tags)
            return []
        
        all_existing_tags = self._get_all_tags_from_vault()
        # Prepare CSV strings for prompt placeholders
        all_existing_tags_csv = ", ".join(all_existing_tags)
        existing_tags_csv = ", ".join(existing_tags)
        
        # Use the configurable AI prompt with explicit placeholders
        prompt = self.ai_prompt.format(
            file_content=file_content,
            all_existing_tags_csv=all_existing_tags_csv,
            existing_tags_csv=existing_tags_csv
        )
        
        for attempt in range(MAX_AI_RETRIES):
            try:
                response = self.gemini_model.generate_content(prompt)
                suggested_tags_str = response.text.strip()
                
                # Post-process suggested tags to remove spaces and periods, and convert to lowercase
                processed_suggested_tags = []
                for tag in suggested_tags_str.split(','):
                    cleaned_tag = tag.strip().lower()
                    cleaned_tag = re.sub(r'\s+', '-', cleaned_tag)  # Replace spaces with hyphens
                    cleaned_tag = re.sub(r'\.+', '', cleaned_tag)  # Remove periods
                    if cleaned_tag and cleaned_tag not in existing_tags and cleaned_tag not in self.excluded_tags:
                        processed_suggested_tags.append(cleaned_tag)
                
                print(f"AI suggested tags: {processed_suggested_tags}")
                return processed_suggested_tags
                
            except (BlockedPromptException, StopCandidateException) as e:
                print(f"AI content generation blocked or stopped: {e}")
                if attempt < MAX_AI_RETRIES - 1:
                    delay = INITIAL_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{MAX_AI_RETRIES})...")
                    time.sleep(delay)
                else:
                    print(f"Max retries ({MAX_AI_RETRIES}) reached. Falling back to basic tag suggestion.")
                    if hasattr(self.tag_extractor, 'suggest_tags_for_content'):
                        return self.tag_extractor.suggest_tags_for_content(file_content, existing_tags)
                    return []
                    
            except Exception as e:
                print(f"Error getting AI suggested tags: {e}")
                if "429" in str(e) and hasattr(e, 'response') and hasattr(e.response, 'json'):
                    try:
                        error_details = e.response.json()
                        retry_delay_seconds = error_details.get('retry_delay', {}).get('seconds')
                        if retry_delay_seconds:
                            delay = int(retry_delay_seconds) + random.uniform(0, 0.5)
                            print(f"API suggested retry after {delay:.2f} seconds (attempt {attempt + 1}/{MAX_AI_RETRIES})...")
                            time.sleep(delay)
                            continue
                    except (json.JSONDecodeError, AttributeError, TypeError):
                        pass
                
                if attempt < MAX_AI_RETRIES - 1:
                    delay = INITIAL_RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{MAX_AI_RETRIES})...")
                    time.sleep(delay)
                else:
                    print(f"Max retries ({MAX_AI_RETRIES}) reached. Falling back to basic tag suggestion.")
                    if hasattr(self.tag_extractor, 'suggest_tags_for_content'):
                        return self.tag_extractor.suggest_tags_for_content(file_content, existing_tags)
                    return []
        
        # Should not be reached if max_retries is handled correctly, but as a safeguard
        if hasattr(self.tag_extractor, 'suggest_tags_for_content'):
            return self.tag_extractor.suggest_tags_for_content(file_content, existing_tags)
        return []
    
    def _get_all_tags_from_vault(self):
        """
        Scans the entire Obsidian vault to extract all unique, cleaned tags
        from the YAML front matter of Markdown files.
        Uses caching to improve performance for repeated calls.
        
        Returns:
            list: A sorted list of all unique, cleaned tags found across the vault.
        """
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
    
    def _should_skip_file(self, file_path, parsed_front_matter, re_tag_option):
        """
        Determines whether a given Markdown file should be skipped during the
        tagging process based on configured exclusion lists and the user's
        selected re-tagging option.
        
        Args:
            file_path (Path): The full path to the Markdown file being considered.
            parsed_front_matter (dict): The parsed YAML front matter of the file.
            re_tag_option (str): A string indicating the user's re-tagging preference.
            
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
                print(f"Skipping '{file_path}' as it is in the exclusion list.")
                return True
        
        # Check re-tagging options
        if re_tag_option == '1':  # Only process files that have NOT been AI-tagged before
            if parsed_front_matter.get('ai_processed'):
                print(f"Skipping '{file_path}' as it is already AI-processed and re-tagging option 1 is selected.")
                return True
                
        elif re_tag_option == '3':  # Only re-tag files that have existing tags but are NOT AI-tagged
            if parsed_front_matter.get('ai_processed') or not parsed_front_matter.get('tags'):
                print(f"Skipping '{file_path}' as it does not match re-tagging option 3 criteria.")
                return True
                
        elif re_tag_option == '4':  # Do NOT re-tag any files that already have tags
            if parsed_front_matter.get('tags'):
                print(f"Skipping '{file_path}' as it has existing tags and re-tagging option 4 is selected.")
                return True
                
        return False
    
    def process_file(self, file_path):
        """
        Processes a single Obsidian Markdown file to suggest and update its tags.
        
        Args:
            file_path (Path): The path to the Markdown file to be processed.
        """
        print(f"Processing file: {file_path}")
        
        # Extract front matter and content
        front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
        
        # Parse front matter if it exists, otherwise start with a new dict
        parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
        
        # Initialize tags from existing front matter or empty list
        existing_tags = set(parsed_front_matter.get('tags', []))
        
        # Get AI suggested tags
        ai_suggested_tags = self._get_ai_suggested_tags(main_content, list(existing_tags))
        
        # Apply aliases to AI suggested tags
        aliased_ai_suggested_tags = self._apply_aliases(ai_suggested_tags)
        
        # Combine existing and suggested tags, remove duplicates
        combined_tags = list(existing_tags)
        for tag in aliased_ai_suggested_tags:
            if tag not in combined_tags and tag not in self.excluded_tags:
                combined_tags.append(tag)
            if len(combined_tags) >= MAX_TAGS_PER_FILE:
                break
        
        updated_tags = sorted(list(set(combined_tags)))  # Ensure uniqueness and sort
        
        # If after combining and sorting, the list is still over the limit, truncate it
        if len(updated_tags) > MAX_TAGS_PER_FILE:
            updated_tags = updated_tags[:MAX_TAGS_PER_FILE]
        
        # Apply final cleaning to all tags before writing
        final_tags = [self._clean_tag_format(tag) for tag in updated_tags]
        final_tags = sorted(list(set(final_tags)))  # Ensure uniqueness and sort again after cleaning
        
        # Update front matter with new tags and mark as processed
        parsed_front_matter['tags'] = final_tags  # Use final_tags, not updated_tags
        parsed_front_matter['ai_processed'] = True
        
        # Serialize the updated front matter and write back to file
        updated_front_matter = self._serialize_front_matter(parsed_front_matter)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_front_matter)
            # Only add an extra newline if there's content to follow
            if main_content.strip():
                f.write('\n' + main_content.lstrip('\n'))
        
        print(f"Tags updated for {file_path}: {final_tags}")
    
    def _interactive_tag_review(self, file_path, current_tags, suggested_tags):
        """
        Presents current and AI-suggested tags to the user for interactive review.
        
        Args:
            file_path (Path): The path to the file being reviewed.
            current_tags (list): A list of tags currently in the file's front matter.
            suggested_tags (list): A list of tags suggested by the AI.
            
        Returns:
            list: The final list of tags after user interaction, or None if the user
                  chooses to skip the file.
        """
        print(f"\n--- Reviewing Tags for: {file_path.name} ---")
        print(f"Current Tags: {', '.join(current_tags)}")
        print(f"Suggested AI Tags: {', '.join(suggested_tags)}")
        combined_tags = sorted(list(set(current_tags + suggested_tags)))
        print(f"Combined Tags (before review): {', '.join(combined_tags)}")
        
        while True:
            action = input(
                "Actions: (a)ccept all, (r)eject all AI suggestions, (m)anually edit, (s)kip file: "
            ).strip().lower()
            
            if action == 'a':
                return combined_tags
                
            elif action == 'r':
                return current_tags  # Revert to only current tags
                
            elif action == 'm':
                while True:
                    edit_input = input(
                        f"Enter desired tags (comma-separated, e.g., tag1, tag2, new-tag) or 'cancel' to re-choose action: "
                    ).strip()
                    
                    if edit_input.lower() == 'cancel':
                        break
                    
                    edited_tags = [self._clean_tag_format(t) for t in edit_input.split(',') if t.strip()]
                    print(f"You entered: {', '.join(edited_tags)}")
                    confirm_edit = input("Confirm these tags? (yes/no): ").strip().lower()
                    
                    if confirm_edit == 'yes':
                        return sorted(list(set(edited_tags)))
                        
            elif action == 's':
                return None  # Signal to skip processing this file
                
            else:
                print("Invalid action. Please choose 'a', 'r', 'm', or 's'.")
    
    def _interactive_alias_review(self, suggested_aliases):
        """
        Presents a list of suggested tag aliases to the user for review and modification.
        The user can approve all, reject all, review individually, or modify suggestions.
        
        Args:
            suggested_aliases (dict): A dictionary where keys are potential alias tags
                                  and values are their suggested canonical forms.
        
        Returns:
            dict: A dictionary containing only the aliases that were approved by the user.
        """
        print("\n--- Reviewing Suggested Tag Aliases ---")
        approved_aliases = {}
        
        if not suggested_aliases:
            print("No aliases to review.")
            return {}
        
        # First, ask if the user wants to review all at once or individually
        print(f"\nFound {len(suggested_aliases)} suggested aliases.")
        print("Options:")
        print("  (a)ccept all - Accept all suggested aliases")
        print("  (r)eject all - Reject all suggested aliases")
        print("  (i)ndividual review - Review each alias individually")
        print("  (m)anual edit - Edit aliases in a JSON file")
        
        while True:
            choice = input("Choose an option (a/r/i/m): ").strip().lower()
            
            if choice == 'a':
                # Accept all aliases
                approved_aliases = suggested_aliases.copy()
                print(f"Accepted all {len(approved_aliases)} suggested aliases.")
                break
                
            elif choice == 'r':
                # Reject all aliases
                print("Rejected all suggested aliases.")
                break
                
            elif choice == 'i':
                # Review each alias individually
                for alias, canonical in suggested_aliases.items():
                    while True:
                        print(f"\nSuggested Alias: '{alias}' -> '{canonical}'")
                        choice = input("Actions: (a)pprove, (r)eject, (m)odify, (s)kip remaining: ").strip().lower()
                        
                        if choice == 'a':
                            approved_aliases[alias] = canonical
                            print(f"Approved: '{alias}' -> '{canonical}'")
                            break
                            
                        elif choice == 'r':
                            print(f"Rejected: '{alias}' -> '{canonical}'")
                            break
                            
                        elif choice == 'm':
                            new_alias = input(f"Enter new alias (current: '{alias}'): ").strip()
                            new_canonical = input(f"Enter new canonical (current: '{canonical}'): ").strip()
                            
                            if new_alias and new_canonical:
                                cleaned_alias = self._clean_tag_format(new_alias)
                                cleaned_canonical = self._clean_tag_format(new_canonical)
                                
                                if cleaned_alias != cleaned_canonical:  # Don't alias a tag to itself
                                    approved_aliases[cleaned_alias] = cleaned_canonical
                                    print(f"Modified and approved: '{cleaned_alias}' -> '{cleaned_canonical}'")
                                else:
                                    print("Cannot alias a tag to itself. Skipping.")
                            else:
                                print("Both alias and canonical must be specified. Skipping.")
                            break
                            
                        elif choice == 's':
                            print("Skipping remaining aliases.")
                            return approved_aliases  # Return what's approved so far
                            
                        else:
                            print("Invalid choice. Please enter 'a', 'r', 'm', or 's'.")
                break
                
            elif choice == 'm':
                # Provide the aliases in a format that can be easily edited
                alias_path = self.vault_path / "suggested_aliases_for_edit.json"
                try:
                    with open(alias_path, 'w', encoding='utf-8') as f:
                        json.dump(suggested_aliases, f, indent=2)
                    print(f"Suggested aliases saved to {alias_path}")
                    print("Edit this file in your preferred editor, then save and close it when done.")
                    input("Press Enter when you have finished editing the file...")
                    
                    # Load the edited aliases
                    try:
                        with open(alias_path, 'r', encoding='utf-8') as f:
                            edited_aliases = json.load(f)
                        
                        # Validate and clean the edited aliases
                        for alias, canonical in edited_aliases.items():
                            cleaned_alias = self._clean_tag_format(alias)
                            cleaned_canonical = self._clean_tag_format(canonical)
                            
                            if cleaned_alias != cleaned_canonical:  # Don't alias a tag to itself
                                approved_aliases[cleaned_alias] = cleaned_canonical
                        
                        print(f"Loaded {len(approved_aliases)} edited aliases.")
                        
                        # Clean up the temporary file
                        try:
                            os.remove(alias_path)
                            print("Temporary alias file removed.")
                        except OSError:
                            print(f"Warning: Could not remove temporary file {alias_path}")
                            
                    except (json.JSONDecodeError, IOError) as e:
                        print(f"Error loading edited aliases: {e}. No aliases will be saved.")
                        
                except IOError as e:
                    print(f"Error saving aliases for editing: {e}")
                break
                
            else:
                print("Invalid choice. Please enter 'a', 'r', 'i', or 'm'.")
        
        return approved_aliases
    
    def add_excluded_tag(self, tag):
        """
        Adds a tag to the automator's exclusion list.
        
        Args:
            tag (str): The tag name to add to the exclusion list.
        """
        cleaned_tag = self._clean_tag_format(tag)
        if cleaned_tag not in self.excluded_tags:
            self.excluded_tags.add(cleaned_tag)
            self._save_config()
            print(f"Tag '{cleaned_tag}' added to exclusion list.")
        else:
            print(f"Tag '{cleaned_tag}' is already in the exclusion list.")
    
    def remove_excluded_tag(self, tag):
        """
        Removes a tag from the automator's exclusion list.
        
        Args:
            tag (str): The tag name to remove from the exclusion list.
        """
        cleaned_tag = self._clean_tag_format(tag)
        if cleaned_tag in self.excluded_tags:
            self.excluded_tags.remove(cleaned_tag)
            self._save_config()
            print(f"Tag '{cleaned_tag}' removed from exclusion list.")
        else:
            print(f"Tag '{cleaned_tag}' not found in the exclusion list.")
    
    def add_excluded_path(self, path_str):
        """
        Adds a file or directory path to the automator's exclusion list.
        
        Args:
            path_str (str): The file or directory path to add. Can be absolute or relative
                            to the vault.
        """
        path_obj = Path(path_str)
        if not path_obj.is_absolute():
            path_obj = self.vault_path / path_str
        
        normalized_path = str(path_obj.relative_to(self.vault_path)).replace('\\', '/')
        
        if normalized_path not in self.excluded_paths:
            self.excluded_paths.add(normalized_path)
            self._save_config()
            print(f"Path '{normalized_path}' added to exclusion list.")
        else:
            print(f"Path '{normalized_path}' is already in the exclusion list.")
    
    def remove_excluded_path(self, path_str):
        """
        Removes a file or directory path from the automator's exclusion list.
        
        Args:
            path_str (str): The file or directory path to remove. Can be absolute or relative
                            to the vault.
        """
        path_obj = Path(path_str)
        if not path_obj.is_absolute():
            path_obj = self.vault_path / path_str
        
        normalized_path = str(path_obj.relative_to(self.vault_path)).replace('\\', '/')
        
        if normalized_path in self.excluded_paths:
            self.excluded_paths.remove(normalized_path)
            self._save_config()
            print(f"Path '{normalized_path}' removed from exclusion list.")
        else:
            print(f"Path '{normalized_path}' not found in the exclusion list.")
    
    def view_exclusions(self):
        """
        Prints the current lists of excluded tags and excluded file/directory paths.
        """
        print("\n--- Current Exclusions ---")
        print("Excluded Tags:")
        if self.excluded_tags:
            for tag in sorted(list(self.excluded_tags)):
                print(f"  - {tag}")
        else:
            print("  No tags excluded.")
        
        print("\nExcluded Paths:")
        if self.excluded_paths:
            for path in sorted(list(self.excluded_paths)):
                print(f"  - {path}")
        else:
            print("  No paths excluded.")
        print("--------------------------")
    
    def clear_tags(self, files_to_clear):
        """
        Clears all tags and the 'ai_processed' flag from the front matter of specified Markdown files.
        
        Args:
            files_to_clear (list): A list of `Path` objects representing the Markdown
                                   files from which tags should be cleared.
        """
        print("\nStarting tag clearing process...")
        for file_path in files_to_clear:
            if not file_path.exists():
                print(f"Warning: File not found - {file_path}. Skipping.")
                continue
                
            if not file_path.suffix.lower() == '.md':
                print(f"Warning: Skipping non-markdown file - {file_path}.")
                continue
            
            print(f"Clearing tags from: {file_path}")
            front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
            parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
            
            # Track if we made any changes
            changed = False
            
            # Remove tags if present
            if 'tags' in parsed_front_matter:
                del parsed_front_matter['tags']
                changed = True
            
            # Remove ai_processed flag if present
            if 'ai_processed' in parsed_front_matter:
                del parsed_front_matter['ai_processed']
                changed = True
            
            # Only update the file if changes were made
            if changed:
                # If front matter is now empty, don't write any front matter
                if not parsed_front_matter:
                    new_file_content = main_content.lstrip('\n')
                else:
                    # Otherwise, serialize the remaining front matter
                    new_front_matter_block = self._serialize_front_matter(parsed_front_matter)
                    new_file_content = new_front_matter_block + main_content
                
                # Write the updated content back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_file_content)
                
                print(f"Tags and AI processing flags cleared for {file_path}")
            else:
                print(f"No tags or AI processing flags found in {file_path}")
        
        print("\nTag clearing process complete.")
    
    def rename_tag(self, old_tag, new_tag):
        """
        Renames an `old_tag` to a `new_tag` across the entire Obsidian vault.
        
        Args:
            old_tag (str): The tag name to be renamed (case-insensitive, cleaned internally).
            new_tag (str): The new, desired tag name (case-insensitive, cleaned internally).
        """
        old_tag_clean = self._clean_tag_format(old_tag)
        new_tag_clean = self._clean_tag_format(new_tag)
        print(f"\nRenaming tag '{old_tag_clean}' to '{new_tag_clean}'...")
        
        # 1. Update tags in Markdown files
        files_modified_count = 0
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                    front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
                    parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
                    
                    if 'tags' in parsed_front_matter:
                        original_tags = set(parsed_front_matter['tags'])
                        updated_tags = set()
                        tag_changed_in_file = False
                        
                        for tag in original_tags:
                            if self._clean_tag_format(tag) == old_tag_clean:
                                updated_tags.add(new_tag_clean)
                                tag_changed_in_file = True
                            else:
                                updated_tags.add(tag)
                        
                        if tag_changed_in_file:
                            parsed_front_matter['tags'] = sorted(list(updated_tags))
                            new_front_matter_block = self._serialize_front_matter(parsed_front_matter)
                            new_file_content = new_front_matter_block + main_content
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_file_content)
                            
                            files_modified_count += 1
                            print(f"  Updated '{file_path}'")
        
        print(f"Renamed '{old_tag}' to '{new_tag}' in {files_modified_count} Markdown files.")
        
        # 2. Update tag_aliases.json
        self.tag_aliases = self._load_tag_aliases()  # Reload to get latest
        aliases_modified_count = 0
        new_aliases = {}
        
        for alias, canonical in self.tag_aliases.items():
            if alias.lower() == old_tag_clean:
                new_aliases[new_tag_clean] = canonical
                aliases_modified_count += 1
            elif canonical.lower() == old_tag_clean:
                new_aliases[alias] = new_tag_clean
                aliases_modified_count += 1
            else:
                new_aliases[alias] = canonical
        
        self._save_tag_aliases(new_aliases)
        print(f"Updated {aliases_modified_count} entries in tag_aliases.json.")
        
        # 3. Update tags_database.json
        self._update_tag_database()  # Re-scan vault to reflect changes
        print("Tag database updated to reflect tag rename.")
        print(f"Tag '{old_tag}' successfully renamed to '{new_tag}' everywhere.")
    
    def merge_tags(self, source_tag, target_tag):
        """
        Merges a `source_tag` into a `target_tag` across the entire Obsidian vault.
        
        Args:
            source_tag (str): The tag name to be merged (will be replaced).
            target_tag (str): The tag name to merge into (the canonical tag).
        """
        source_tag_clean = self._clean_tag_format(source_tag)
        target_tag_clean = self._clean_tag_format(target_tag)
        print(f"\nMerging tag '{source_tag_clean}' into '{target_tag_clean}'...")
        
        # 1. Update tags in Markdown files
        files_modified_count = 0
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                    front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
                    parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
                    
                    if 'tags' in parsed_front_matter:
                        original_tags = set(parsed_front_matter['tags'])
                        updated_tags = set()
                        tag_changed_in_file = False
                        
                        for tag in original_tags:
                            if self._clean_tag_format(tag) == source_tag_clean:
                                updated_tags.add(target_tag_clean)
                                tag_changed_in_file = True
                            else:
                                updated_tags.add(tag)
                        
                        if tag_changed_in_file:
                            parsed_front_matter['tags'] = sorted(list(updated_tags))
                            new_front_matter_block = self._serialize_front_matter(parsed_front_matter)
                            new_file_content = new_front_matter_block + main_content
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_file_content)
                            
                            files_modified_count += 1
                            print(f"  Updated '{file_path}'")
        
        print(f"Merged '{source_tag}' into '{target_tag}' in {files_modified_count} Markdown files.")
        
        # 2. Update tag_aliases.json
        self.tag_aliases = self._load_tag_aliases()  # Reload to get latest
        aliases_modified_count = 0
        new_aliases = {}
        
        for alias, canonical in self.tag_aliases.items():
            if alias.lower() == source_tag_clean:
                # If source_tag was an alias, remove it
                aliases_modified_count += 1
                continue
            elif canonical.lower() == source_tag_clean:
                new_aliases[alias] = target_tag_clean
                aliases_modified_count += 1
            else:
                new_aliases[alias] = canonical
        
        self._save_tag_aliases(new_aliases)
        print(f"Updated {aliases_modified_count} entries in tag_aliases.json.")
        
        # 3. Update tags_database.json
        self._update_tag_database()  # Re-scan vault to reflect changes
        print("Tag database updated to reflect tag merge.")
        print(f"Tag '{source_tag}' successfully merged into '{target_tag}' everywhere.")
    
    def validate_tags(self):
        """
        Validates tags across all Markdown files in the vault.
        """
        print("\n--- Starting Tag Validation ---")
        self._update_tag_database()  # Ensure the database is up-to-date
        all_known_tags = set(self._load_tags_database())
        orphan_tags_found = {}  # {file_path: [orphan_tag1, ...]}
        malformed_tags_found = {}  # {file_path: [malformed_tag1, ...]}
        
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                    front_matter_raw, _ = self._extract_front_matter_and_content(file_path)
                    parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
                    
                    file_tags = set(parsed_front_matter.get('tags', []))
                    
                    current_file_orphans = []
                    current_file_malformed = []
                    
                    for tag in file_tags:
                        # Check for malformed tags
                        if ' ' in tag or '.' in tag:
                            current_file_malformed.append(tag)
                        
                        # Check for orphan tags (case-insensitive comparison)
                        if tag.lower() not in [t.lower() for t in all_known_tags]:
                            current_file_orphans.append(tag)
                    
                    if current_file_orphans:
                        orphan_tags_found[str(file_path.relative_to(self.vault_path))] = current_file_orphans
                    if current_file_malformed:
                        malformed_tags_found[str(file_path.relative_to(self.vault_path))] = current_file_malformed
        
        print("\n--- Validation Results ---")
        if not orphan_tags_found and not malformed_tags_found:
            print("No orphan or malformed tags found. Your vault tags are clean!")
        else:
            if orphan_tags_found:
                print("\nOrphan Tags Found (tags in files not in tags_database.json):")
                for file_path_str, tags in orphan_tags_found.items():
                    print(f"  File: {file_path_str}")
                    for tag in tags:
                        print(f"    - {tag}")
            
            if malformed_tags_found:
                print("\nMalformed Tags Found (tags containing spaces or periods):")
                for file_path_str, tags in malformed_tags_found.items():
                    print(f"  File: {file_path_str}")
                    for tag in tags:
                        print(f"    - {tag}")
        
        print("\n--- Tag Validation Complete ---")
    
    def run_automator(self, files_to_tag, re_tag_option):
        """
        Executes the main tag automation process on a specified set of Markdown files.
        
        Args:
            files_to_tag (list): A list of `Path` objects for the Markdown files to process.
            re_tag_option (str): A string representing the user's choice for re-tagging behavior.
        """
        # Initial full scan to populate the in-memory tag set and the JSON database
        self._update_tag_database()
        
        for file_path in files_to_tag:
            if not file_path.exists():
                print(f"Warning: File not found - {file_path}. Skipping.")
                continue
                
            if not file_path.suffix.lower() == '.md':
                print(f"Warning: Skipping non-markdown file - {file_path}.")
                continue
            
            front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
            parsed_front_matter = self._parse_front_matter(front_matter_raw) if front_matter_raw else {}
            
            if self._should_skip_file(file_path, parsed_front_matter, re_tag_option):
                continue
            
            # Call process_file, but also handle interactive review if enabled
            if re_tag_option == '5':  # Interactive review option
                existing_tags = set(parsed_front_matter.get('tags', []))
                ai_suggested_tags = self._get_ai_suggested_tags(main_content, list(existing_tags))
                aliased_ai_suggested_tags = self._apply_aliases(ai_suggested_tags)
                
                final_tags_after_review = self._interactive_tag_review(
                    file_path, list(existing_tags), aliased_ai_suggested_tags
                )
                
                if final_tags_after_review is None:  # User chose to skip
                    print(f"Skipping '{file_path}' due to user choice.")
                    continue
                else:
                    # Update front matter with reviewed tags
                    parsed_front_matter['tags'] = sorted(list(set([self._clean_tag_format(tag) for tag in final_tags_after_review])))
                    parsed_front_matter['ai_processed'] = True
                    new_front_matter_block = self._serialize_front_matter(parsed_front_matter)
                    new_file_content = new_front_matter_block + main_content
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_file_content)
                    
                    print(f"Tags updated for {file_path}: {parsed_front_matter['tags']}")
            else:
                self.process_file(file_path)
            
            # After processing a file, update the in-memory tag set with any newly added tags
            current_file_tags = self._parse_front_matter(self._extract_front_matter_and_content(file_path)[0]).get('tags', [])
            self.tag_extractor.tags.update(current_file_tags)
        
        print("\nTagging process complete for all specified files.")
        
        final_scan_choice = input("Do you want to run a final full scan to update the tags database? (yes/no): ").strip().lower()
        if final_scan_choice == 'yes':
            self._update_tag_database()
            print("Final tag database update complete.")
        else:
            print("Skipping final tag database update.")


# Example usage (for testing purposes)
if __name__ == "__main__":
    VAULT_PATH = r"e:\Creator_Command_Hub_Obsidian"
    
    # Instantiate without passing an API key explicitly. The constructor will
    # read GEMINI_API_KEY from the environment if available.
    automator = ObsidianTagAutomator(VAULT_PATH)
    
    while True:
        print("\nObsidian Tag Automator")
        print("----------------------")
        
        print("\nMain Menu:")
        print("  1. Run Tagging Automator (process Markdown files)")
        print("  2. Generate and Review Suggested Tag Aliases")
        print("  3. Clear Tags from Files")
        print("  4. Rename/Refactor a Tag")
        print("  5. Merge Tags")
        print("  6. Configure AI Prompt")
        print("  7. Manage Tag/File Exclusions")
        print("  8. Interactive Tag Review and Approval")
        print("  9. Interactive Alias Review and Approval")
        print("  10. Validate Tags (Find Orphans and Malformed Tags)")
        print("  11. Exit")
        
        main_choice = input("Enter your choice (1-11): ").strip()
        
        # Helper function to get files based on user choice
        def _get_files_from_user_choice(vault_path, prompt_message):
            print(f"\n{prompt_message}")
            print("1. Process specific Markdown files (enter paths manually)")
            print("2. Process ALL Markdown files in the vault")
            print("3. Process all Markdown files within a specific directory")
            
            choice = input("Enter your file selection choice (1, 2, or 3): ").strip()
            files_selected = []
            
            if choice == '1':
                while True:
                    file_input = input("Enter the path to a Markdown file (relative to vault, or full path), or 'done' to finish: ").strip()
                    if file_input.lower() == 'done':
                        break
                    
                    # Strip quotes if present
                    if file_input.startswith('"') and file_input.endswith('"'):
                        file_input = file_input[1:-1]
                    if file_input.startswith("'") and file_input.endswith("'"):
                        file_input = file_input[1:-1]
                    
                    file_path = Path(file_input)
                    if not file_path.is_absolute():
                        file_path = Path(vault_path) / file_input
                    
                    if file_path.exists() and file_path.suffix.lower() == '.md':
                        files_selected.append(file_path)
                    else:
                        print(f"Invalid file path or not a Markdown file: '{file_input}'. Please try again.")
                
                if not files_selected:
                    print("No files selected. Returning to main menu.")
                    
            elif choice == '2':
                print("Scanning vault for all Markdown files...")
                for root, _, files in os.walk(vault_path):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                            files_selected.append(file_path)
                print(f"Found {len(files_selected)} Markdown files.")
                
            elif choice == '3':
                while True:
                    dir_input = input("Enter the path to the directory (relative to vault, or full path): ").strip()
                    
                    # Strip quotes if present
                    if dir_input.startswith('"') and dir_input.endswith('"'):
                        dir_input = dir_input[1:-1]
                    if dir_input.startswith("'") and dir_input.endswith("'"):
                        dir_input = dir_input[1:-1]
                    
                    dir_path = Path(dir_input)
                    if not dir_path.is_absolute():
                        dir_path = Path(vault_path) / dir_input
                    
                    if dir_path.is_dir():
                        print(f"Scanning directory '{dir_path}' for Markdown files...")
                        for root, _, files in os.walk(dir_path):
                            for file in files:
                                file_path = Path(root) / file
                                if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                                    files_selected.append(file_path)
                        print(f"Found {len(files_selected)} Markdown files in '{dir_path}'.")
                        break
                    else:
                        print(f"Invalid directory path: '{dir_input}'. Please try again.")
                
                if not files_selected:
                    print("No Markdown files found in the specified directory. Returning to main menu.")
            else:
                print("Invalid choice. Returning to main menu.")
                
            return files_selected
        
        if main_choice == '1':
            print("\nRe-tagging options:")
            print("  1. Only process files that have NOT been AI-tagged before (no 'ai_processed' flag).")
            print("  2. Re-tag ALL files, including those previously AI-tagged.")
            print("  3. Only re-tag files that have existing tags but are NOT AI-tagged.")
            print("  4. Do NOT re-tag any files that already have tags.")
            print("  5. Interactive Tag Review and Approval (for AI-suggested tags)")
            
            re_tag_option = input("Enter your re-tagging choice (1, 2, 3, 4, or 5): ").strip()
            files_to_process = _get_files_from_user_choice(VAULT_PATH, "Choose files to process:")
            
            if files_to_process:
                automator.run_automator(files_to_process, re_tag_option)
            
            # After running automator, ask if user wants to continue or exit
            continue_choice = input("\nTagging process finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
            
        elif main_choice == '2':
            print("\nGenerating suggested tag aliases...")
            automator._update_tag_database()  # Ensure tag database is fresh
            
            # Ask user whether to use AI or heuristic-based suggestions
            use_ai = "yes"
            if automator.gemini_model:
                use_ai = input("Use AI to suggest aliases? (yes/no, default: yes): ").strip().lower()
                if not use_ai:
                    use_ai = "yes"
            
            if use_ai == "yes" and automator.gemini_model:
                suggested_aliases = automator._generate_ai_suggested_aliases()
            else:
                suggested_aliases = automator._generate_suggested_aliases()
            
            if suggested_aliases:
                # Call interactive alias review
                approved_aliases = automator._interactive_alias_review(suggested_aliases)
                
                if approved_aliases:
                    # Merge approved aliases with existing ones
                    current_aliases = automator._load_tag_aliases()
                    current_aliases.update(approved_aliases)
                    automator._save_tag_aliases(current_aliases)
                    print(f"Approved {len(approved_aliases)} tag aliases. Saved to tag_aliases.json.")
                else:
                    print("No aliases approved or saved.")
            else:
                print("No new tag aliases suggested based on the current tag database.")
            
            # After generating aliases, ask if user wants to continue or exit
            continue_choice = input("\nAlias generation finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '3':
            files_to_clear = _get_files_from_user_choice(VAULT_PATH, "Choose scope for clearing tags:")
            if files_to_clear:
                automator.clear_tags(files_to_clear)
            
            continue_choice = input("\nTag clearing process finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '4':
            print("\nTag Renaming/Refactoring Tool")
            old_tag = input("Enter the tag to rename (old tag): ").strip().lower()
            new_tag = input("Enter the new tag name: ").strip().lower()
            
            if not old_tag or not new_tag:
                print("Old tag and new tag cannot be empty. Returning to main menu.")
            elif old_tag == new_tag:
                print("Old tag and new tag are the same. No renaming needed. Returning to main menu.")
            else:
                automator.rename_tag(old_tag, new_tag)
            
            continue_choice = input("\nTag renaming process finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '5':
            print("\nTag Merging Tool")
            source_tag = input("Enter the tag to merge FROM (source tag): ").strip().lower()
            target_tag = input("Enter the tag to merge INTO (target tag): ").strip().lower()
            
            if not source_tag or not target_tag:
                print("Source tag and target tag cannot be empty. Returning to main menu.")
            elif source_tag == target_tag:
                print("Source tag and target tag are the same. No merging needed. Returning to main menu.")
            else:
                automator.merge_tags(source_tag, target_tag)
            
            continue_choice = input("\nTag merging process finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '6':
            print("\nConfigure AI Prompt")
            print("Current AI Prompt (first 200 chars):")
            print(automator.get_ai_prompt()[:200] + "...")
            
            new_prompt_choice = input("Do you want to set a new custom AI prompt? (yes/no): ").strip().lower()
            if new_prompt_choice == 'yes':
                print("Enter your new custom AI prompt. Type 'END_PROMPT' on a new line to finish.")
                new_prompt_lines = []
                while True:
                    line = input()
                    if line == 'END_PROMPT':
                        break
                    new_prompt_lines.append(line)
                new_prompt = "\n".join(new_prompt_lines)
                automator.set_ai_prompt(new_prompt)
                print("AI prompt updated.")
            else:
                print("AI prompt not changed.")
            
            continue_choice = input("\nAI prompt configuration finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '7':
            print("\nManage Tag/File Exclusions")
            print("1. Add Tag to Exclusion List")
            print("2. Remove Tag from Exclusion List")
            print("3. Add File/Directory to Exclusion List")
            print("4. Remove File/Directory from Exclusion List")
            print("5. View Current Exclusions")
            
            exclusion_choice = input("Enter your choice (1-5): ").strip()
            
            if exclusion_choice == '1':
                tag_to_add = input("Enter tag to add to exclusion list: ").strip().lower()
                automator.add_excluded_tag(tag_to_add)
            elif exclusion_choice == '2':
                tag_to_remove = input("Enter tag to remove from exclusion list: ").strip().lower()
                automator.remove_excluded_tag(tag_to_remove)
            elif exclusion_choice == '3':
                path_to_add = input("Enter file or directory path to add to exclusion list: ").strip()
                automator.add_excluded_path(path_to_add)
            elif exclusion_choice == '4':
                path_to_remove = input("Enter file or directory path to remove from exclusion list: ").strip()
                automator.remove_excluded_path(path_to_remove)
            elif exclusion_choice == '5':
                automator.view_exclusions()
            else:
                print("Invalid choice. Returning to main menu.")
            
            continue_choice = input("\nExclusion management finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '8':  # Interactive tag review
            files_to_review = _get_files_from_user_choice(VAULT_PATH, "Interactive Tag Review and Approval")
            if files_to_review:
                for file_path in files_to_review:
                    if not file_path.exists() or not file_path.suffix.lower() == '.md':
                        print(f"Skipping invalid file: {file_path}")
                        continue
                    
                    front_matter_raw, main_content = automator._extract_front_matter_and_content(file_path)
                    parsed_front_matter = automator._parse_front_matter(front_matter_raw) if front_matter_raw else {}
                    existing_tags = set(parsed_front_matter.get('tags', []))
                    ai_suggested_tags = automator._get_ai_suggested_tags(main_content, list(existing_tags))
                    aliased_ai_suggested_tags = automator._apply_aliases(ai_suggested_tags)
                    
                    final_tags_after_review = automator._interactive_tag_review(
                        file_path, list(existing_tags), aliased_ai_suggested_tags
                    )
                    
                    if final_tags_after_review is None:  # User chose to skip
                        print(f"Skipping '{file_path}' due to user choice.")
                        continue
                    else:
                        parsed_front_matter['tags'] = sorted(list(set([automator._clean_tag_format(tag) for tag in final_tags_after_review])))
                        parsed_front_matter['ai_processed'] = True
                        new_front_matter_block = automator._serialize_front_matter(parsed_front_matter)
                        new_file_content = new_front_matter_block + main_content
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_file_content)
                        
                        print(f"Tags updated for {file_path}: {parsed_front_matter['tags']}")
            
            continue_choice = input("\nInteractive tag review finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '9':  # Interactive alias review
            print("\nInteractive Alias Review and Approval")
            automator._update_tag_database()  # Ensure tag database is fresh
            suggested_aliases = automator._generate_suggested_aliases()
            
            if suggested_aliases:
                approved_aliases = automator._interactive_alias_review(suggested_aliases)
                
                if approved_aliases:
                    current_aliases = automator._load_tag_aliases()
                    current_aliases.update(approved_aliases)
                    automator._save_tag_aliases(current_aliases)
                    print("Approved tag aliases saved/updated in tag_aliases.json.")
                else:
                    print("No aliases approved or saved.")
            else:
                print("No new tag aliases suggested based on the current tag database.")
            
            continue_choice = input("\nInteractive alias review finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '10':  # Tag validation
            automator.validate_tags()
            continue_choice = input("\nTag validation finished. Do you want to return to the main menu or exit? (menu/exit): ").strip().lower()
            if continue_choice == 'exit':
                print("Exiting Tag Automator.")
                break  # Exit the main loop
        
        elif main_choice == '11':  # Exit
            print("Exiting Tag Automator.")
            break  # Exit the main loop
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, or 11.")
