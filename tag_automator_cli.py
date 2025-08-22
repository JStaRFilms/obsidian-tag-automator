#!/usr/bin/env python3
"""
Obsidian Tag Automator - Main Entry Point
This script provides both CLI and Web interfaces for the tag automator.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the Obsidian Tag Automator."""
    parser = argparse.ArgumentParser(
        description="Obsidian Tag Automator - AI-powered tag management for your knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CLI Interface
  python tag_automator_cli.py
  
  # CLI with custom vault path
  python tag_automator_cli.py --vault-path /path/to/vault
  
  # CLI with Gemini API key
  python tag_automator_cli.py --gemini-api-key your-api-key
  
  # Web Interface
  python tag_automator_cli.py --web
  
  # Web Interface on custom port
  python tag_automator_cli.py --web --port 8080
  
  # Web Interface with custom host
  python tag_automator_cli.py --web --host 0.0.0.0 --port 8080
        """
    )
    
    # General arguments
    parser.add_argument("-v", "--vault-path", help="Path to the Obsidian vault")
    parser.add_argument("-k", "--gemini-api-key", help="Gemini API key for AI tag suggestions")
    
    # Interface selection
    interface_group = parser.add_mutually_exclusive_group()
    interface_group.add_argument("--cli", action="store_true", help="Use CLI interface (default)")
    interface_group.add_argument("--web", action="store_true", help="Use web interface")
    
    # Web interface specific arguments
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind web server to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind web server to (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for web interface")
    
    # Utility arguments
    parser.add_argument("--version", action="version", version="Obsidian Tag Automator v1.0")
    parser.add_argument("--setup", action="store_true", help="Run initial setup wizard")
    
    args = parser.parse_args()
    
    # Determine which interface to use
    use_web = args.web or (not args.cli and os.getenv('OBSIDIAN_AUTOMATOR_WEB', '').lower() == 'true')
    
    try:
        if use_web:
            # Import and run web interface
            from interfaces.web_interface import ObsidianTagAutomatorWeb
            
            print("🚀 Starting Obsidian Tag Automator Web Interface...")
            print(f"📁 Vault Path: {args.vault_path or 'Auto-detecting...'}")
            print(f"🌐 Access URL: http://{args.host}:{args.port}")
            print("💡 Press Ctrl+C to stop the server")
            print()
            
            web_app = ObsidianTagAutomatorWeb(args.vault_path, args.gemini_api_key)
            web_app.run(host=args.host, port=args.port, debug=args.debug)
            
        else:
            # Import and run CLI interface
            from interfaces.cli_interface import ObsidianTagAutomatorCLI
            
            print("🤖 Starting Obsidian Tag Automator CLI...")
            print(f"📁 Vault Path: {args.vault_path or 'Auto-detecting...'}")
            print()
            
            cli = ObsidianTagAutomatorCLI(args.vault_path, args.gemini_api_key)
            cli.display_main_menu()
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()