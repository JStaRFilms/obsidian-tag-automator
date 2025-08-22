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