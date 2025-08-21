import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env in the project root
load_dotenv(Path(__file__).parent / '.env')

class ObsidianTagExtractor:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.tags = set()
        # self.tag_pattern = re.compile(r'#([\w-]+)') # No longer needed if tags are only in front matter
        self.front_matter_pattern = re.compile(r'---\s*\n(.*?)\n---\s*\n(.*)', re.DOTALL)
        
    def should_process_file(self, file_path):
        """Check if the file should be processed."""
        # Only process markdown files
        if not file_path.suffix.lower() == '.md':
            return False
            
        # Skip files in .obsidian directory
        if '.obsidian' in file_path.parts:
            return False
            
        return True

    def _extract_front_matter_and_content(self, file_path):
        """Extracts YAML front matter and content from a markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        front_matter_match = self.front_matter_pattern.match(content)
        if front_matter_match:
            front_matter_raw = front_matter_match.group(1)
            main_content = front_matter_match.group(2)
            return front_matter_raw, main_content
        return None, content # No front matter found

    def _parse_front_matter_tags(self, front_matter_raw):
        """Parses raw YAML front matter to extract tags."""
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
                    current_tags = [t.strip() for t in value[1:-1].split(',') if t.strip()]
                    parsed_tags.extend(current_tags)
                elif value: # Handle single tag: tags: tag1
                    parsed_tags.append(value)
                else: # Handle multi-line list: tags:\n  - tag1\n  - tag2
                    j = i + 1
                    while j < len(lines):
                        sub_line = lines[j].strip()
                        if sub_line.startswith('- '):
                            tag = sub_line[1:].strip()
                            if tag:
                                parsed_tags.append(tag)
                        elif sub_line: # Stop if it's not a tag line and not empty
                            break
                        j += 1
                    i = j - 1 # Adjust index to skip processed tag lines
            i += 1
        return parsed_tags
        
    def extract_tags_from_file(self, file_path):
        """Extract tags from a single file, prioritizing front matter."""
        try:
            front_matter_raw, _ = self._extract_front_matter_and_content(file_path)
            found_tags = self._parse_front_matter_tags(front_matter_raw)
            
            # Add to the set of all tags
            self.tags.update(found_tags)
            
            return found_tags
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []
    
    def scan_vault(self):
        """Scan the entire vault for tags."""
        print(f"Starting vault scan from: {self.vault_path}")
        initial_tag_count = len(self.tags)
        processed_files_count = 0
        
        for root, dirs, files in os.walk(self.vault_path):
            # Skip .obsidian directory
            if '.obsidian' in Path(root).parts:
                # print(f"Skipping .obsidian directory: {root}") # Optional: for very detailed debugging
                continue
            
            # print(f"Scanning directory: {root}") # Optional: for very detailed debugging
            
            for file in files:
                file_path = Path(root) / file
                if self.should_process_file(file_path):
                    processed_files_count += 1
                    found_tags_in_file = self.extract_tags_from_file(file_path)
                    # print(f"  Processed file: {file_path.name}, Found tags: {found_tags_in_file}") # Optional: for very detailed debugging
        
        print(f"Finished vault scan. Processed {processed_files_count} markdown files.")
        print(f"Total unique tags found: {len(self.tags)} (Added {len(self.tags) - initial_tag_count} new tags during this scan).")
        return sorted(list(self.tags))
    
    def save_tags_to_json(self, output_path):
        """Save the extracted tags to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"tags": sorted(list(self.tags))}, f, indent=2)
            
    def get_tags_for_ai(self):
        """Return tags in a format suitable for AI processing."""
        return {"tags": sorted(list(self.tags))}

    def suggest_tags_for_content(self, content, existing_tags=None):
        """Suggest relevant tags for new content based on existing tags."""
        if existing_tags is None:
            existing_tags = []
            
        # This is a simple implementation that could be enhanced with AI
        # For now, just check if any existing tags appear in the content
        suggested_tags = []
        
        for tag in self.tags:
            # Skip tags that are already assigned
            if tag in existing_tags:
                continue
                
            # Simple check if the tag word appears in the content
            if tag.lower() in content.lower():
                suggested_tags.append(tag)
                
        return suggested_tags

# Example usage
def main():
    vault_path = r"e:\Creator_Command_Hub_Obsidian"
    output_path = os.path.join(vault_path, "tags_database.json")
    
    extractor = ObsidianTagExtractor(vault_path)
    print(f"Scanning vault at {vault_path}...")
    
    tags = extractor.scan_vault()
    print(f"Found {len(tags)} unique tags")
    
    extractor.save_tags_to_json(output_path)
    print(f"Tags saved to {output_path}")
    
    # Example of how to use with an AI agent
    # This would be integrated with your AI agent code
    sample_content = "This is a note about YouTube video production and thumbnail design."
    suggested_tags = extractor.suggest_tags_for_content(sample_content)
    print(f"Suggested tags for sample content: {suggested_tags}")

if __name__ == "__main__":
    main()
