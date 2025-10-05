import os
import json
from pathlib import Path
from datetime import datetime
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
        
        # Cache for expensive operations
        self._vault_stats_cache = None
        self._vault_stats_cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes cache TTL

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

    def remove_all_tags_from_folder(self, folder_path):
        """
        Removes all tags from all Markdown files in a specific folder and its subfolders.

        Args:
            folder_path (str or Path): Path to the folder (relative to vault root or absolute)

        Returns:
            dict: Result containing success status and files modified.
        """
        # Normalize the folder path to be relative to vault root
        folder_path = Path(folder_path)
        if folder_path.is_absolute():
            try:
                folder_path = folder_path.relative_to(self.vault_path)
            except ValueError:
                return {
                    'success': False,
                    'message': f'Folder path {folder_path} is not within the vault {self.vault_path}',
                    'files_modified': 0
                }

        # Ensure the folder exists
        full_folder_path = self.vault_path / folder_path
        if not full_folder_path.exists() or not full_folder_path.is_dir():
            return {
                'success': False,
                'message': f'Folder {full_folder_path} does not exist or is not a directory',
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
            # Walk through the specified folder
            for root, _, files in os.walk(full_folder_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() == '.md' and '.obsidian' not in file_path.parts:
                        result['files_processed'] += 1

                        try:
                            front_matter_raw, main_content = self.tag_processor._extract_front_matter_and_content(file_path)
                            if not front_matter_raw:
                                continue  # No front matter to modify

                            parsed_front_matter = self.tag_processor._parse_front_matter(front_matter_raw)

                            # Check if file has tags
                            if 'tags' in parsed_front_matter and parsed_front_matter['tags']:
                                # Remove all tags
                                parsed_front_matter['tags'] = []

                                # Also remove ai_processed flag so files can be re-tagged normally
                                if 'ai_processed' in parsed_front_matter:
                                    del parsed_front_matter['ai_processed']

                                # Write back to file
                                self.tag_processor.write_file_with_updated_tags(file_path, [], main_content, parsed_front_matter)
                                result['files_modified'] += 1

                        except Exception as e:
                            result['failed_files'].append({
                                'file_path': str(file_path),
                                'error': str(e)
                            })

            result['message'] = f"Removed all tags from {result['files_modified']} files in folder '{folder_path}'"

        except Exception as e:
            result['success'] = False
            result['message'] = f"Error removing tags from folder: {str(e)}"

        return result

    def generate_ai_suggested_merges(self):
        """
        Uses AI to analyze existing tags and suggest semantic merges (not just aliases).

        Returns:
            dict: Result containing AI-suggested merges.
        """
        if not self.ai_integration.gemini_model:
            return {
                'success': False,
                'message': 'Gemini API not configured. Cannot generate AI-suggested merges.',
                'suggested_merges': {}
            }

        all_tags = self.get_all_tags()
        if len(all_tags) < 2:
            return {
                'success': False,
                'message': 'Need at least 2 tags to suggest merges.',
                'suggested_merges': {}
            }

        # Create a prompt for the AI to suggest tag merges
        prompt = f"""
You are an AI assistant for analyzing tag semantics in an Obsidian vault. Your goal is to identify tags that represent the same or very similar concepts and should be merged.

Here is the list of all tags in the vault:
{', '.join(sorted(all_tags))}

Instructions:
1. Identify groups of tags that represent the same concept (e.g., 'javascript', 'js', 'ecmascript' could all merge to 'javascript').
2. For each group, choose the most standard/professional/canonical tag name as the target.
3. Return a JSON object where each key is a tag to be merged FROM, and each value is the tag to merge TO.
4. Only suggest merges where you are highly confident the tags represent the same concept.
5. Do not suggest merging tags that are truly different concepts.
6. Format your response as a valid JSON object only, with no additional text.

Example response format:
{{
  "js": "javascript",
  "ecmascript": "javascript",
  "py": "python",
  "c-sharp": "csharp",
  "c++": "cpp"
}}
"""

        try:
            response = self.ai_integration.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # Debug: Log the raw response
            print(f"DEBUG: AI response length: {len(response_text)}")
            if len(response_text) < 200:
                print(f"DEBUG: AI response content: '{response_text}'")
            else:
                print(f"DEBUG: AI response preview: '{response_text[:200]}...'")

            # Clean markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            # Try to parse the response as JSON
            try:
                suggested_merges = json.loads(response_text)
                # Validate that the response is a dictionary
                if not isinstance(suggested_merges, dict):
                    return {
                        'success': False,
                        'message': 'AI response is not a valid dictionary.',
                        'suggested_merges': {}
                    }

                # Clean and validate the suggested merges
                cleaned_merges = {}
                for from_tag, to_tag in suggested_merges.items():
                    cleaned_from = self.tag_processor._clean_tag_format(from_tag)
                    cleaned_to = self.tag_processor._clean_tag_format(to_tag)

                    # Validate that both tags exist and are different
                    if (cleaned_from in all_tags and cleaned_to in all_tags and
                        cleaned_from != cleaned_to):
                        cleaned_merges[cleaned_from] = cleaned_to

                return {
                    'success': True,
                    'message': f"AI suggested {len(cleaned_merges)} tag merges.",
                    'suggested_merges': cleaned_merges
                }

            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'message': f'Failed to parse AI response as JSON: {e}',
                    'suggested_merges': {}
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting AI suggested merges: {e}',
                'suggested_merges': {}
            }

    def generate_ai_suggested_deletions(self):
        """
        Uses AI to analyze existing tags and suggest which ones should be deleted as redundant or low-value.

        Returns:
            dict: Result containing AI-suggested deletions.
        """
        if not self.ai_integration.gemini_model:
            return {
                'success': False,
                'message': 'Gemini API not configured. Cannot generate AI-suggested deletions.',
                'suggested_deletions': []
            }

        all_tags = self.get_all_tags()
        if not all_tags:
            return {
                'success': False,
                'message': 'No tags found to analyze.',
                'suggested_deletions': []
            }

        # Get tag usage statistics
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

        # Create usage info for AI
        usage_info = []
        for tag in sorted(all_tags):
            usage_count = tag_usage.get(tag, 0)
            usage_info.append(f"{tag} ({usage_count} files)")

        prompt = f"""
You are an AI assistant for analyzing tag quality in an Obsidian vault. Your goal is to identify tags that should be deleted because they are redundant, too generic, or low-value.

Here is the list of all tags with their usage counts:
{', '.join(usage_info)}

Instructions:
1. Identify tags that are too generic or meaningless (e.g., 'stuff', 'things', 'misc', 'test', 'temp').
2. Identify redundant tags that don't add value (e.g., 'note', 'file', 'document').
3. Identify tags used in very few files (1-2 files) that might be typos or one-off experiments.
4. Do NOT suggest deleting tags that are specific and meaningful, even if used infrequently.
5. Return a JSON array of tag names that should be deleted.
6. Be conservative - only suggest deletion for tags that are clearly problematic.
7. Format your response as a valid JSON array only, with no additional text.

Example response format:
["stuff", "things", "misc", "test", "note"]
"""

        try:
            response = self.ai_integration.gemini_model.generate_content(prompt)
            response_text = response.text.strip()

            # Debug: Log the raw response
            print(f"DEBUG: AI response length: {len(response_text)}")
            if len(response_text) < 200:
                print(f"DEBUG: AI response content: '{response_text}'")
            else:
                print(f"DEBUG: AI response preview: '{response_text[:200]}...'")

            # Clean markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

            # Try to parse the response as JSON
            try:
                suggested_deletions = json.loads(response_text)
                # Validate that the response is a list
                if not isinstance(suggested_deletions, list):
                    return {
                        'success': False,
                        'message': 'AI response is not a valid array.',
                        'suggested_deletions': []
                    }

                # Clean and validate the suggested deletions
                cleaned_deletions = []
                for tag in suggested_deletions:
                    cleaned_tag = self.tag_processor._clean_tag_format(tag)
                    if cleaned_tag in all_tags:
                        cleaned_deletions.append(cleaned_tag)

                return {
                    'success': True,
                    'message': f"AI suggested deleting {len(cleaned_deletions)} tags.",
                    'suggested_deletions': cleaned_deletions
                }

            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'message': f'Failed to parse AI response as JSON: {e}',
                    'suggested_deletions': []
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting AI suggested deletions: {e}',
                'suggested_deletions': []
            }

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

            # Debug: Log the raw response
            print(f"DEBUG: AI response length: {len(response_text)}")
            if len(response_text) < 200:
                print(f"DEBUG: AI response content: '{response_text}'")
            else:
                print(f"DEBUG: AI response preview: '{response_text[:200]}...'")

            # Clean markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            response_text = response_text.strip()

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

    def get_vault_stats(self, include_trends=False):
        """
        Returns statistics about the vault with caching to improve performance.
        
        Args:
            include_trends (bool): Whether to include trend calculations
        
        Returns:
            dict: Vault statistics with optional trends.
        """
        import time
        
        # Check if we have cached data that's still valid
        current_time = time.time()
        if (self._vault_stats_cache and 
            (current_time - self._vault_stats_cache_timestamp) < self._cache_ttl):
            result = {
                'success': True,
                'message': 'Vault statistics retrieved (cached)',
                'stats': self._vault_stats_cache
            }
            
            if include_trends:
                # Calculate trends even for cached stats
                historical_stats = self._load_historical_stats()
                trends = self._calculate_trends(self._vault_stats_cache, historical_stats)
                result['trends'] = trends
                # Save current stats as historical for next time
                self._save_historical_stats(self._vault_stats_cache)
            
            return result
        
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
        
        # Cache the results
        self._vault_stats_cache = stats
        self._vault_stats_cache_timestamp = current_time
        
        result = {
            'success': True,
            'message': 'Vault statistics retrieved',
            'stats': stats
        }
        
        if include_trends:
            # Calculate trends
            historical_stats = self._load_historical_stats()
            trends = self._calculate_trends(stats, historical_stats)
            result['trends'] = trends
            # Save current stats as historical for next time
            self._save_historical_stats(stats)
        
        return result

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

        for excluded_path_str in self.excluded_paths:
            # Normalize the excluded path to be relative to vault root
            if excluded_path_str.startswith(str(self.vault_path)):
                # Convert absolute path to relative
                excluded_relative = str(Path(excluded_path_str).relative_to(self.vault_path)).replace('\\', '/')
            else:
                # Already relative, use as-is
                excluded_relative = excluded_path_str.replace('\\', '/')

            # Check if the file path starts with the excluded path
            if relative_file_path.startswith(excluded_relative):
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
    
    def _get_historical_stats_path(self):
        """
        Get the path to the historical statistics file.
        
        Returns:
            Path: Path to the historical stats JSON file
        """
        return self.vault_path / '.obsidian' / 'automator_stats.json'
    
    def _load_historical_stats(self):
        """
        Load historical statistics from storage.
        
        Returns:
            dict: Historical statistics or empty dict if not found
        """
        stats_path = self._get_historical_stats_path()
        if stats_path.exists():
            try:
                with open(stats_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('stats', {})
            except (json.JSONDecodeError, IOError, KeyError):
                return {}
        return {}
    
    def _save_historical_stats(self, current_stats):
        """
        Save current statistics as historical data.
        
        Args:
            current_stats (dict): Current vault statistics to save
        """
        stats_path = self._get_historical_stats_path()
        stats_path.parent.mkdir(exist_ok=True)
        
        historical_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': current_stats
        }
        
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(historical_data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save historical stats: {e}")
    
    def _calculate_trends(self, current_stats, historical_stats):
        """
        Calculate trends by comparing current stats with historical stats.
        
        Args:
            current_stats (dict): Current vault statistics
            historical_stats (dict): Historical vault statistics
        
        Returns:
            dict: Trend calculations for each metric
        """
        trends = {}
        
        # Calculate percentage change for each metric
        for metric in ['total_files', 'tagged_files', 'total_tags', 'ai_processed_files']:
            current_value = current_stats.get(metric, 0)
            historical_value = historical_stats.get(metric, 0)
            
            if historical_value > 0:
                percentage_change = ((current_value - historical_value) / historical_value) * 100
                trends[metric] = {
                    'value': round(percentage_change, 1),
                    'direction': 'up' if percentage_change > 0 else 'down' if percentage_change < 0 else 'same',
                    'previous_value': historical_value,
                    'current_value': current_value
                }
            else:
                # No historical data or zero historical value
                trends[metric] = {
                    'value': 0,
                    'direction': 'same',
                    'previous_value': 0,
                    'current_value': current_value
                }
        
        return trends
