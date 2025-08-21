# Obsidian Tag Automator

A powerful tool for managing and automating tags in your Obsidian vault.

## Features

- AI-powered tag suggestions
- Batch tag processing
- Tag renaming and merging
- Tag validation and cleanup
- Interactive tag review
- Support for tag aliases
- Configurable exclusions

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

Run the main script:
```bash
python -m tag_automator
```

## Project Structure

- `tag_automator.py` - Main script for tag automation
- `tag_extractor.py` - Core functionality for tag extraction and processing
- `tests/` - Test files and demo scripts
- `requirements.txt` - Project dependencies
- `.gitignore` - Git ignore file

## License

MIT
