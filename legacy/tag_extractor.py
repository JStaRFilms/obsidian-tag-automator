import os
import re
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

class ObsidianTagExtractor:
    """
    Extracts and manages tags from an Obsidian vault by scanning Markdown files
    and parsing their YAML front matter.
    """
    
    def __init__(self, vault_path=None, config=None):
        """
        Initialize the tag extractor with a vault path and optional configuration.
        
        Args:
            vault_path (str or Path, optional): Path to the Obsidian vault. 
                If not provided, will try to detect it or use environment variable.
            config (dict, optional): Configuration options for the extractor.
        """
        # Load environment variables
        load_dotenv(Path(__file__).parent / '.env')
        
        # Set vault path with fallbacks
        if vault_path is None:
            vault_path = os.getenv('OBSIDIAN_VAULT_PATH')
        
        if vault_path is None:
            vault_path = self._detect_vault_path()
        
        self.vault_path = Path(vault_path)
        self.tags = set()
        
        # Default configuration
        default_config = {
            'output_file': 'tags_database.json',
            'scan_hidden_files': False,
            'skip_directories': ['.obsidian', '.git', '.idea'],
            'file_extensions': ['.md', '.markdown'],
            'tag_min_length': 1,
            'tag_max_length': 50,
            'case_sensitive': False,
            'include_hashtag_tags': True,
            'strict_yaml_parsing': False,
            'allow_special_chars': False,  # More restrictive to avoid false positives
            'normalize_tags': True,
            'min_word_length': 3,  # Minimum word length for content matching
            'exclude_common_words': True  # Exclude common words like "the", "and", etc.
        }
        
        # Apply user configuration
        self.config = {**default_config, **(config or {})}
        
        # Compile regex patterns
        self.front_matter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n(.*)', re.DOTALL)
        if self.config['include_hashtag_tags']:
            # Standard regex for hashtag tags
            self.tag_pattern = re.compile(r'#([a-zA-Z0-9_-]+)')
        
        # Common words to exclude from content matching
        self.common_words = {
            'the', 'and', 'or', 'but', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
    
    def _detect_vault_path(self):
        """
        Attempts to detect the Obsidian vault path based on the current working directory.
        
        Returns:
            Path: The detected Obsidian vault path.
        """
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / ".obsidian").exists():
                return cwd
            cwd = cwd.parent
        
        # If not found, prompt the user
        print("Obsidian vault path not detected. Please enter the path manually:")
        vault_path = input("> ")
        return Path(vault_path)
    
    def should_process_file(self, file_path):
        """
        Check if the file should be processed based on configuration.
        
        Args:
            file_path (Path): Path to the file to check.
            
        Returns:
            bool: True if the file should be processed, False otherwise.
        """
        # Check file extension
        if file_path.suffix.lower() not in self.config['file_extensions']:
            return False
            
        # Skip hidden files if configured
        if not self.config['scan_hidden_files'] and file_path.name.startswith('.'):
            return False
            
        # Skip files in excluded directories
        for dir_name in self.config['skip_directories']:
            if dir_name in file_path.parts:
                return False
                
        return True
    
    def _extract_front_matter_and_content(self, file_path):
        """
        Extracts YAML front matter and content from a markdown file.
        
        Args:
            file_path (Path): Path to the markdown file.
            
        Returns:
            tuple: (front_matter_raw, main_content) or (None, full_content) if no front matter.
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
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
                
            return front_matter_raw, main_content
            
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None, ""
    
    def _parse_front_matter_tags(self, front_matter_raw):
        """
        Parses raw YAML front matter to extract tags.
        More permissive parsing to match old behavior.
        
        Args:
            front_matter_raw (str): Raw YAML front matter content.
            
        Returns:
            list: List of tags found in the front matter.
        """
        parsed_tags = []
        if not front_matter_raw:
            return parsed_tags
            
        lines = front_matter_raw.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('tags:'):
                value = line.split(':', 1)[1].strip()
                
                # Handle inline list: tags: [tag1, tag2]
                if value.startswith('[') and value.endswith(']'):
                    current_tags = [t.strip().strip('"\'') for t in value[1:-1].split(',') if t.strip()]
                    parsed_tags.extend(current_tags)
                elif value: # Handle single tag: tags: tag1
                    parsed_tags.append(value.strip('"\''))
                else: # Handle multi-line list: tags:\n  - tag1\n  - tag2
                    j = i + 1
                    while j < len(lines):
                        sub_line = lines[j].strip()
                        if sub_line.startswith('- '):
                            tag = sub_line[1:].strip().strip('"\'')
                            if tag:
                                parsed_tags.append(tag)
                        elif sub_line: # Stop if it's not a tag line and not empty
                            break
                        j += 1
                    i = j - 1 # Adjust index to skip processed tag lines
            i += 1
            
        return parsed_tags
    
    def _extract_hashtag_tags(self, content):
        """
        Extracts hashtag-style tags from content if configured.
        
        Args:
            content (str): Content to search for tags.
            
        Returns:
            list: List of hashtag tags found in the content.
        """
        if not self.config['include_hashtag_tags'] or not self.tag_pattern:
            return []
            
        return self.tag_pattern.findall(content)
    
    def _normalize_tag(self, tag):
        """
        Normalize a tag according to configuration.
        
        Args:
            tag (str): The tag to normalize.
            
        Returns:
            str: The normalized tag.
        """
        if not tag:
            return tag
            
        # Apply case sensitivity
        if not self.config['case_sensitive']:
            tag = tag.lower()
            
        # Normalize tag format if enabled
        if self.config['normalize_tags']:
            # Replace spaces with hyphens
            tag = re.sub(r'\s+', '-', tag)
            # Remove special characters except hyphens and underscores (if not allowed)
            if not self.config['allow_special_chars']:
                tag = re.sub(r'[^a-zA-Z0-9_-]', '', tag)
            
        return tag
    
    def extract_tags_from_file(self, file_path):
        """
        Extract tags from a single file, prioritizing front matter.
        
        Args:
            file_path (Path): Path to the file to extract tags from.
            
        Returns:
            list: List of tags found in the file.
        """
        try:
            front_matter_raw, main_content = self._extract_front_matter_and_content(file_path)
            found_tags = self._parse_front_matter_tags(front_matter_raw)
            
            # Also extract hashtag tags if configured
            if self.config['include_hashtag_tags']:
                hashtag_tags = self._extract_hashtag_tags(main_content)
                found_tags.extend(hashtag_tags)
            
            # Clean and filter tags
            cleaned_tags = []
            for tag in found_tags:
                # Skip empty tags
                if not tag:
                    continue
                    
                # Normalize tag
                tag = self._normalize_tag(tag)
                
                # Check length constraints
                if (len(tag) >= self.config['tag_min_length'] and 
                    len(tag) <= self.config['tag_max_length']):
                    cleaned_tags.append(tag)
            
            # Add to the set of all tags
            self.tags.update(cleaned_tags)
            
            return cleaned_tags
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []
    
    def scan_vault(self, progress_callback=None):
        """
        Scan the entire vault for tags.
        
        Args:
            progress_callback (callable, optional): Function to call with progress updates.
                
        Returns:
            list: Sorted list of all unique tags found in the vault.
        """
        print(f"Starting vault scan from: {self.vault_path}")
        initial_tag_count = len(self.tags)
        processed_files_count = 0
        total_files = 0
        
        # Count total files for progress reporting
        if progress_callback:
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    file_path = Path(root) / file
                    if self.should_process_file(file_path):
                        total_files += 1
        
        for root, dirs, files in os.walk(self.vault_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.config['skip_directories']]
            
            for file in files:
                file_path = Path(root) / file
                if self.should_process_file(file_path):
                    processed_files_count += 1
                    found_tags_in_file = self.extract_tags_from_file(file_path)
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress = {
                            'current': processed_files_count,
                            'total': total_files,
                            'current_file': str(file_path),
                            'tags_found': found_tags_in_file,
                            'total_tags': len(self.tags)
                        }
                        progress_callback(progress)
        
        print(f"Finished vault scan. Processed {processed_files_count} files.")
        print(f"Total unique tags found: {len(self.tags)} (Added {len(self.tags) - initial_tag_count} new tags during this scan).")
        return sorted(list(self.tags))
    
    def save_tags_to_json(self, output_path=None):
        """
        Save the extracted tags to a JSON file.
        
        Args:
            output_path (str or Path, optional): Path to save the tags JSON file.
                If not provided, uses the configured output file.
        """
        if output_path is None:
            output_path = self.vault_path / self.config['output_file']
        else:
            output_path = Path(output_path)
            
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"tags": sorted(list(self.tags))}, f, indent=2)
            
        print(f"Tags saved to {output_path}")
    
    def get_tags_for_ai(self):
        """
        Return tags in a format suitable for AI processing.
        
        Returns:
            dict: Dictionary containing sorted list of tags.
        """
        return {"tags": sorted(list(self.tags))}
    
    def suggest_tags_for_content(self, content, existing_tags=None, max_suggestions=10):
        """
        Suggest relevant tags for new content based on existing tags.
        
        Args:
            content (str): Content to suggest tags for.
            existing_tags (list, optional): List of tags already assigned to the content.
            max_suggestions (int, optional): Maximum number of suggestions to return.
                
        Returns:
            list: List of suggested tags.
        """
        if existing_tags is None:
            existing_tags = []
            
        # This is a simple implementation that could be enhanced with AI
        suggested_tags = []
        content_lower = content.lower()
        
        # Create a frequency map of words in content
        word_freq = {}
        for word in re.findall(r'\b\w+\b', content_lower):
            if len(word) >= self.config['min_word_length']:
                if not self.config['exclude_common_words'] or word not in self.common_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
        # Score tags based on presence in content
        tag_scores = {}
        for tag in self.tags:
            # Skip tags that are already assigned
            if tag in existing_tags:
                continue
                
            # Check if tag appears as a whole word in content
            if tag.lower() in content_lower:
                # Higher score for exact matches
                tag_scores[tag] = 10
                
            # Check if parts of the tag appear in content
            tag_parts = tag.split('-')
            for part in tag_parts:
                if len(part) >= self.config['min_word_length'] and part in word_freq:
                    # Score based on word frequency
                    tag_scores[tag] = tag_scores.get(tag, 0) + word_freq[part]
        
        # Sort by score and return top suggestions
        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
        return [tag for tag, score in sorted_tags[:max_suggestions]]
    
    def load_tags_from_json(self, input_path=None):
        """
        Load tags from a JSON file instead of scanning the vault.
        
        Args:
            input_path (str or Path, optional): Path to the tags JSON file.
                If not provided, uses the configured output file.
        """
        if input_path is None:
            input_path = self.vault_path / self.config['output_file']
        else:
            input_path = Path(input_path)
            
        if not input_path.exists():
            print(f"Tags file not found: {input_path}")
            return False
            
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tags = set(data.get('tags', []))
            print(f"Loaded {len(self.tags)} tags from {input_path}")
            return True
        except Exception as e:
            print(f"Error loading tags from {input_path}: {e}")
            return False


def main():
    """
    Main function for command-line usage of the tag extractor.
    """
    parser = argparse.ArgumentParser(description="Extract tags from an Obsidian vault.")
    parser.add_argument("-v", "--vault-path", help="Path to the Obsidian vault")
    parser.add_argument("-o", "--output", help="Output file path for tags database")
    parser.add_argument("--include-hashtags", action="store_true", default=True,
                        help="Include hashtag-style tags from content (default: True)")
    parser.add_argument("--exclude-hashtags", action="store_true",
                        help="Exclude hashtag-style tags from content")
    parser.add_argument("--strict-yaml", action="store_true",
                        help="Use strict YAML parsing for front matter")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="Treat tags as case-sensitive")
    parser.add_argument("--min-tag-length", type=int, default=1,
                        help="Minimum tag length")
    parser.add_argument("--max-tag-length", type=int, default=50,
                        help="Maximum tag length")
    parser.add_argument("--load", action="store_true",
                        help="Load tags from existing JSON file instead of scanning")
    
    args = parser.parse_args()
    
    # Create configuration from command line arguments
    config = {
        'include_hashtag_tags': not args.exclude_hashtags,
        'strict_yaml_parsing': args.strict_yaml,
        'case_sensitive': args.case_sensitive,
        'tag_min_length': args.min_tag_length,
        'tag_max_length': args.max_tag_length
    }
    
    if args.output:
        config['output_file'] = args.output
    
    # Initialize extractor
    extractor = ObsidianTagExtractor(vault_path=args.vault_path, config=config)
    
    if args.load:
        # Load existing tags
        success = extractor.load_tags_from_json()
        if not success:
            print("Failed to load tags. Exiting.")
            return
    else:
        # Scan vault for tags
        def progress_callback(progress):
            print(f"Progress: {progress['current']}/{progress['total']} files processed, "
                  f"{progress['total_tags']} tags found so far")
        
        tags = extractor.scan_vault(progress_callback=progress_callback)
        print(f"Found {len(tags)} unique tags")
    
    # Save tags to JSON
    extractor.save_tags_to_json()
    
    # Example of tag suggestion
    sample_content = "This is a note about YouTube video production and thumbnail design."
    suggested_tags = extractor.suggest_tags_for_content(sample_content)
    print(f"Suggested tags for sample content: {suggested_tags}")


if __name__ == "__main__":
    main()