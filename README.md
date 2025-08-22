# Obsidian Tag Automator

🤖 AI-powered tag management system for your Obsidian vault. Automate tagging, suggest aliases, and maintain consistency across your knowledge base.

## Features

### Core Functionality
- **AI-Powered Tagging**: Use Google Gemini AI to analyze your notes and suggest relevant tags
- **Tag Management**: Rename, merge, delete, and validate tags across your entire vault
- **Smart Aliases**: Automatically suggest tag aliases using heuristic analysis or AI
- **Batch Processing**: Process multiple files with progress tracking
- **Validation System**: Identify malformed, duplicate, and orphaned tags

### Interfaces
- **Command Line Interface**: Rich, interactive CLI with progress bars and tables
- **Web Interface**: Modern, responsive web UI with real-time updates
- **API Layer**: RESTful API for integration with other tools

### Configuration
- **Customizable AI Prompts**: Tailor the AI's behavior to your needs
- **Exclusion Lists**: Exclude specific tags or paths from processing
- **Flexible Processing**: Choose from multiple re-tagging strategies

## Installation

### Prerequisites
- Python 3.8 or higher
- Obsidian vault (optional, can be auto-detected)
- Google Gemini API key (for AI features)

### Setup

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd obsidian-tag-automator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your Gemini API key**
   ```bash
   # Option 1: Environment variable
   export GEMINI_API_KEY="your-api-key-here"
   
   # Option 2: Create a .env file
   echo "GEMINI_API_KEY=your-api-key-here" > .env
   ```

5. **Set up your vault path (optional)**
   ```bash
   # Option 1: Environment variable
   export OBSIDIAN_VAULT_PATH="/path/to/your/vault"
   
   # Option 2: The app will auto-detect if run from within a vault
   ```

## Usage

### Command Line Interface

#### Basic Usage
```bash
# Run the CLI interface
python tag_automator_cli.py

# Specify vault path
python tag_automator_cli.py --vault-path /path/to/vault

# Specify Gemini API key
python tag_automator_cli.py --gemini-api-key your-api-key
```

#### CLI Features
- **Interactive Menu**: Navigate through features with an intuitive menu system
- **File Processing**: Process files with various re-tagging strategies
- **Tag Operations**: Rename, merge, delete, and validate tags
- **Alias Generation**: Create smart tag aliases
- **Configuration Management**: Edit AI prompts and exclusion lists
- **Progress Tracking**: Real-time progress bars for long operations

### Web Interface

#### Starting the Web Server
```bash
# Start web interface (default: http://127.0.0.1:5000)
python tag_automator_cli.py --web

# Custom host and port
python tag_automator_cli.py --web --host 0.0.0.0 --port 8080

# Enable debug mode
python tag_automator_cli.py --web --debug
```

#### Web Features
- **Dashboard**: Overview of vault statistics and recent activity
- **File Processing**: Select and process files with various options
- **Tag Management**: Visual interface for tag operations
- **Real-time Updates**: Live progress tracking and status updates
- **Responsive Design**: Works on desktop and mobile devices
- **Settings Management**: Configure AI prompts and exclusions

### API Usage

The web interface exposes a RESTful API that can be used for integration:

```bash
# Get system status
curl http://localhost:5000/api/status

# Get all files
curl http://localhost:5000/api/files

# Get all tags
curl http://localhost:5000/api/tags

# Process a file
curl -X POST http://localhost:5000/api/process-file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/file.md", "options": {"re_tag_option": "1"}}'

# Rename a tag
curl -X POST http://localhost:5000/api/rename-tag \
  -H "Content-Type: application/json" \
  -d '{"old_tag": "old-tag", "new_tag": "new-tag"}'
```

## Configuration

### AI Prompt Customization

You can customize the AI prompt to better suit your needs:

```python
# Via CLI
# Navigate to Configuration -> Edit AI Prompt

# Via Web Interface
# Go to Settings -> AI Configuration

# Via API
curl -X POST http://localhost:5000/api/update-ai-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your custom prompt here..."}'
```

### Exclusion Lists

Exclude specific tags or paths from processing:

```python
# Via CLI
# Navigate to Configuration -> Manage Excluded Tags/Paths

# Via Web Interface
# Go to Settings -> Exclusions

# Via configuration file
# Edit automator_config.json in your vault
```

Example configuration:
```json
{
  "excluded_tags": ["meta", "system", "internal"],
  "excluded_paths": ["templates/", "archive/"],
  "ai_prompt": "Your custom AI prompt..."
}
```

## Project Structure

```
obsidian-tag-automator/
├── core/                          # Core business logic
│   ├── __init__.py
│   ├── automator_core.py          # Main automator class
│   ├── tag_processor.py           # File and tag operations
│   ├── ai_integration.py          # AI functionality
│   └── config_manager.py          # Configuration management
├── interfaces/                    # Interface adapters
│   ├── __init__.py
│   ├── cli_interface.py          # CLI wrapper
│   └── web_interface.py          # Web API wrapper
├── web/                          # Web frontend
│   ├── app.py                    # Flask application
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Custom styles
│   │   └── js/
│   │       └── app.js            # Frontend JavaScript
│   └── templates/
│       └── index.html            # Main HTML template
├── tag_automator_cli.py          # Main entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run tests with coverage
pytest --cov=core --cov=interfaces
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 core/ interfaces/

# Type checking
mypy core/ interfaces/
```

### Adding New Features

1. **Core Logic**: Add new functionality to `core/automator_core.py`
2. **CLI Interface**: Update `interfaces/cli_interface.py` if needed
3. **Web Interface**: Add API endpoints in `interfaces/web_interface.py`
4. **Frontend**: Update `web/static/js/app.js` and `web/templates/index.html`

## Troubleshooting

### Common Issues

#### AI Features Not Working
```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Verify API key works
python -c "import google.generativeai as genai; genai.configure(api_key='your-key'); print('API key works!')"
```

#### Vault Not Detected
```bash
# Run from within your vault directory
cd /path/to/your/vault
python /path/to/automator/tag_automator_cli.py

# Or specify vault path explicitly
python tag_automator_cli.py --vault-path /path/to/vault
```

#### Web Interface Not Accessible
```bash
# Check if port is available
netstat -an | grep 5000

# Try different port
python tag_automator_cli.py --web --port 8080

# Check firewall settings
sudo ufw status
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# CLI debug mode
python tag_automator_cli.py --debug

# Web debug mode
python tag_automator_cli.py --web --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format your code (`black .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Check this README and inline code documentation
- **Community**: Join discussions in the GitHub repository

## Changelog

### v1.0.0
- Initial release
- AI-powered tag suggestions
- CLI and web interfaces
- Tag management operations
- Configuration system
- RESTful API

## Acknowledgments

- **Google Gemini**: For providing the AI capabilities
- **Obsidian**: For the amazing note-taking platform
- **Rich**: For the beautiful CLI interface
- **Flask**: For the web framework
- **Tailwind CSS**: For the modern UI design
```

Perfect! Now you have a complete web application for your Obsidian Tag Automator. Here's what we've built:

## 🎉 Complete Web Application Summary

### 📁 Project Structure
```
obsidian-tag-automator/
├── core/                          # Pure business logic
│   ├── automator_core.py          # Main functionality
│   ├── tag_processor.py           # File operations
│   ├── ai_integration.py          # AI features
│   └── config_manager.py          # Configuration
├── interfaces/                    # Interface adapters
│   ├── cli_interface.py          # CLI wrapper
│   └── web_interface.py          # Web API wrapper
├── web/                          # Web frontend
│   ├── templates/
│   │   └── index.html            # Beautiful UI
│   └── static/
│       ├── css/style.css         # Custom styles
│       └── js/app.js            # Interactive frontend
├── tag_automator_cli.py          # Main entry point
├── requirements.txt              # Dependencies
└── README.md                     # Documentation
```

### 🚀 Key Features Implemented

1. **Dual Interface Support**:
   - Rich CLI interface with progress bars and tables
   - Modern web interface with real-time updates
   - RESTful API for third-party integrations

2. **AI-Powered Functionality**:
   - Google Gemini integration for smart tag suggestions
   - Customizable AI prompts
   - AI-powered alias generation

3. **Comprehensive Tag Management**:
   - Rename, merge, delete tags across entire vault
   - Tag validation and cleanup
   - Smart alias detection and management

4. **Modern Web Interface**:
   - Responsive design with Tailwind CSS
   - Real-time progress tracking
   - Interactive file selection
   - Beautiful dashboard with statistics

5. **Robust Architecture**:
   - Clean separation of concerns
   - Background task processing
   - Error handling and validation
   - Configuration management

### 🎯 How to Run

**CLI Interface**:
```bash
python tag_automator_cli.py
```

**Web Interface**:
```bash
python tag_automator_cli.py --web
```

**Custom Settings**:
```bash
python tag_automator_cli.py --web --host 0.0.0.0 --port 8080
```

### 🎨 What Makes It "Dope"

1. **Beautiful UI**: Modern glass-morphism design with smooth animations
2. **Real-time Updates**: Live progress tracking and status updates
3. **Smart Features**: AI-powered suggestions and validation
4. **Professional Code**: Clean architecture with proper separation of concerns
5. **User-Friendly**: Intuitive interfaces with helpful feedback
6. **Extensible**: Easy to add new features and integrations

### 🛠️ Next Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up API Key**:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. **Run the Application**:
   ```bash
   python tag_automator_cli.py --web
   ```

4. **Access the Web Interface**:
   Open `http://localhost:5000` in your browser
