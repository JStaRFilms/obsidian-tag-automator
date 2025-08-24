import os
import json
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import threading
import time
from datetime import datetime

from core.automator_core import ObsidianTagAutomatorCore

class ObsidianTagAutomatorWeb:
    """
    Web interface for the Obsidian Tag Automator.
    Provides REST API endpoints and serves the web frontend.
    """
    
    def __init__(self, vault_path=None, gemini_api_key=None):
        """
        Initialize the web interface.
        
        Args:
            vault_path (str or Path, optional): Path to the Obsidian vault.
            gemini_api_key (str, optional): Gemini API key for AI suggestions.
        """
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='../web/templates',
                        static_folder='../web/static')
        CORS(self.app)
        
        # Configure Flask
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # Initialize the core automator
        if vault_path is None:
            vault_path = self._detect_vault_path()
        
        self.automator = ObsidianTagAutomatorCore(vault_path, gemini_api_key)
        
        # Background task tracking
        self.background_tasks = {}
        
        # Register routes
        self._register_routes()
        
        # Start background task cleaner
        self._start_task_cleaner()
    
    def _detect_vault_path(self):
        """Detect the Obsidian vault path."""
        # Try to get from environment variable
        env_path = os.getenv('OBSIDIAN_VAULT_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Try to detect from current directory
        cwd = Path.cwd()
        while cwd != cwd.parent:
            if (cwd / ".obsidian").exists():
                return cwd
            cwd = cwd.parent
        
        # Default to current directory
        return Path.cwd()
    
    def _register_routes(self):
        """Register all Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard."""
            return render_template('index.html')
        
        @self.app.route('/api/status/quick')
        def get_quick_status():
            """Get basic system status quickly without heavy operations."""
            try:
                vault_path = self.automator.vault_path
                
                response = {
                    'success': True,
                    'vault_path': str(vault_path),
                    'vault_exists': vault_path.exists(),
                    'is_obsidian_vault': (vault_path / '.obsidian').exists() if vault_path.exists() else False,
                    'ai_status': bool(self.automator.ai_integration.gemini_model),
                    'timestamp': datetime.now().isoformat()
                }
                return jsonify(response)
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'error': str(e),
                    'vault_path': str(self.automator.vault_path) if hasattr(self.automator, 'vault_path') else 'Unknown'
                }), 500
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status and vault information."""
            try:
                # Get vault stats (may be cached)
                stats_result = self.automator.get_vault_stats()
                config = self.automator.get_config()
                vault_path = self.automator.vault_path
                
                # Check vault accessibility and validity
                vault_exists = vault_path.exists()
                is_obsidian_vault = (vault_path / '.obsidian').exists() if vault_exists else False
                vault_readable = False
                vault_stats = None
                
                if vault_exists:
                    try:
                        # Test if we can read the vault directory
                        list(vault_path.iterdir())
                        vault_readable = True
                        vault_stats = {
                            'vault_size_bytes': sum(f.stat().st_size for f in vault_path.rglob('*') if f.is_file()),
                            'total_items': len(list(vault_path.rglob('*')))
                        }
                    except (PermissionError, OSError):
                        vault_readable = False
                
                response = {
                    'success': True,
                    'vault_path': str(vault_path),
                    'vault_info': {
                        'exists': vault_exists,
                        'readable': vault_readable,
                        'is_obsidian_vault': is_obsidian_vault,
                        'absolute_path': str(vault_path.absolute()),
                        'stats': vault_stats
                    },
                    'ai_status': bool(self.automator.ai_integration.gemini_model),
                    'stats': stats_result['stats'] if stats_result['success'] else {},
                    'config': {
                        'excluded_tags_count': len(config.get('excluded_tags', [])),
                        'excluded_paths_count': len(config.get('excluded_paths', [])),
                        'ai_prompt_configured': bool(config.get('ai_prompt'))
                    },
                    'system_info': {
                        'current_working_directory': str(Path.cwd()),
                        'python_executable': os.sys.executable if hasattr(os, 'sys') else 'Unknown'
                    }
                }
                return jsonify(response)
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'error': str(e),
                    'vault_path': str(self.automator.vault_path) if hasattr(self.automator, 'vault_path') else 'Unknown',
                    'debug_info': {
                        'current_working_directory': str(Path.cwd()),
                        'exception_type': type(e).__name__
                    }
                }), 500
        
        @self.app.route('/api/files/recent')
        def get_recent_files():
            """Get recent files with pagination for progressive loading."""
            try:
                limit = int(request.args.get('limit', 20))
                offset = int(request.args.get('offset', 0))
                sort_by = request.args.get('sort', 'modified')  # 'modified', 'name', 'size'
                
                vault_path = self.automator.vault_path
                
                if not vault_path.exists():
                    return jsonify({
                        'success': False,
                        'error': f'Vault path does not exist: {vault_path}'
                    }), 404
                
                files = []
                for root, dirs, file_names in os.walk(vault_path):
                    # Skip .obsidian and other hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for file_name in file_names:
                        if file_name.endswith('.md'):
                            file_path = Path(root) / file_name
                            relative_path = file_path.relative_to(vault_path)
                            
                            try:
                                stat = file_path.stat()
                                files.append({
                                    'name': file_name,
                                    'path': str(relative_path),
                                    'full_path': str(file_path),
                                    'size': stat.st_size,
                                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                                })
                            except (OSError, IOError):
                                continue
                
                # Sort files
                if sort_by == 'modified':
                    files.sort(key=lambda x: x['modified'], reverse=True)
                elif sort_by == 'name':
                    files.sort(key=lambda x: x['name'].lower())
                elif sort_by == 'size':
                    files.sort(key=lambda x: x['size'], reverse=True)
                
                # Apply pagination
                total_files = len(files)
                paginated_files = files[offset:offset + limit]
                
                return jsonify({
                    'success': True,
                    'files': paginated_files,
                    'pagination': {
                        'total': total_files,
                        'limit': limit,
                        'offset': offset,
                        'has_more': offset + limit < total_files
                    },
                    'vault_info': {
                        'path': str(vault_path),
                        'is_obsidian_vault': (vault_path / '.obsidian').exists()
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/files')
        def get_files():
            """Get list of markdown files in the vault."""
            try:
                files = []
                vault_path = self.automator.vault_path
                
                # Validate vault path exists and is accessible
                if not vault_path.exists():
                    return jsonify({
                        'success': False, 
                        'error': f'Vault path does not exist: {vault_path}',
                        'vault_path': str(vault_path)
                    }), 404
                
                # Check if it's actually an Obsidian vault
                obsidian_folder = vault_path / '.obsidian'
                is_obsidian_vault = obsidian_folder.exists()
                
                file_count = 0
                scanned_directories = []
                
                for root, dirs, file_names in os.walk(vault_path):
                    root_path = Path(root)
                    relative_root = root_path.relative_to(vault_path)
                    scanned_directories.append(str(relative_root))
                    
                    # Skip .obsidian and other hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') or d == '.obsidian']
                    
                    for file_name in file_names:
                        if file_name.endswith('.md') and '.obsidian' not in root:
                            file_count += 1
                            file_path = root_path / file_name
                            relative_path = file_path.relative_to(vault_path)
                            
                            try:
                                stat = file_path.stat()
                                files.append({
                                    'name': file_name,
                                    'path': str(relative_path),
                                    'full_path': str(file_path),
                                    'size': stat.st_size,
                                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                                })
                            except (OSError, IOError) as e:
                                # Skip files that can't be accessed
                                print(f"Warning: Could not access file {file_path}: {e}")
                                continue
                
                return jsonify({
                    'success': True, 
                    'files': files,
                    'vault_path': str(vault_path),
                    'is_obsidian_vault': is_obsidian_vault,
                    'total_files': file_count,
                    'scanned_directories': scanned_directories[:10],  # Limit to first 10 for debugging
                    'scan_summary': {
                        'total_directories': len(scanned_directories),
                        'total_md_files': file_count,
                        'vault_root': str(vault_path)
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'error': str(e),
                    'vault_path': str(self.automator.vault_path) if hasattr(self.automator, 'vault_path') else 'Unknown'
                }), 500
        
        @self.app.route('/api/tags')
        def get_tags():
            """Get all tags from the vault."""
            try:
                tags = self.automator.get_all_tags()
                return jsonify({'success': True, 'tags': tags})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/process-file', methods=['POST'])
        def process_file():
            """Process a single file."""
            try:
                data = request.get_json()
                file_path = data.get('file_path')
                options = data.get('options', {})
                
                if not file_path:
                    return jsonify({'success': False, 'error': 'File path is required'}), 400
                
                result = self.automator.process_file(file_path, options)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/process-multiple-files', methods=['POST'])
        def process_multiple_files():
            """Process multiple files as a background task."""
            try:
                data = request.get_json()
                file_paths = data.get('file_paths', [])
                options = data.get('options', {})
                
                if not file_paths:
                    return jsonify({'success': False, 'error': 'File paths are required'}), 400
                
                # Create background task
                task_id = str(uuid.uuid4())
                self.background_tasks[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'total': len(file_paths),
                    'result': None,
                    'start_time': datetime.now().isoformat()
                }
                
                # Start background thread
                thread = threading.Thread(
                    target=self._process_files_background,
                    args=(task_id, file_paths, options)
                )
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'File processing started'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/task-status/<task_id>')
        def get_task_status(task_id):
            """Get status of a background task."""
            try:
                if task_id not in self.background_tasks:
                    return jsonify({'success': False, 'error': 'Task not found'}), 404
                
                task = self.background_tasks[task_id]
                return jsonify({
                    'success': True,
                    'task': task
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/rename-tag', methods=['POST'])
        def rename_tag():
            """Rename a tag across all files."""
            try:
                data = request.get_json()
                old_tag = data.get('old_tag')
                new_tag = data.get('new_tag')
                
                if not old_tag or not new_tag:
                    return jsonify({'success': False, 'error': 'Both old_tag and new_tag are required'}), 400
                
                result = self.automator.rename_tag(old_tag, new_tag)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/merge-tags', methods=['POST'])
        def merge_tags():
            """Merge multiple tags into one."""
            try:
                data = request.get_json()
                tags_to_merge = data.get('tags_to_merge', [])
                new_tag_name = data.get('new_tag_name')
                
                if not tags_to_merge or not new_tag_name:
                    return jsonify({'success': False, 'error': 'tags_to_merge and new_tag_name are required'}), 400
                
                result = self.automator.merge_tags(tags_to_merge, new_tag_name)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/delete-tags', methods=['POST'])
        def delete_tags():
            """Delete specified tags from all files."""
            try:
                data = request.get_json()
                tags_to_delete = data.get('tags_to_delete', [])
                
                if not tags_to_delete:
                    return jsonify({'success': False, 'error': 'tags_to_delete is required'}), 400
                
                result = self.automator.delete_tags(tags_to_delete)
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/generate-aliases', methods=['POST'])
        def generate_aliases():
            """Generate tag aliases."""
            try:
                data = request.get_json()
                method = data.get('method', 'heuristic')  # 'heuristic' or 'ai'
                
                if method == 'ai':
                    result = self.automator.generate_ai_suggested_aliases()
                else:
                    result = self.automator.generate_suggested_aliases()
                
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/save-aliases', methods=['POST'])
        def save_aliases():
            """Save tag aliases."""
            try:
                data = request.get_json()
                aliases = data.get('aliases', {})
                
                self.automator.set_tag_aliases(aliases)
                return jsonify({'success': True, 'message': 'Aliases saved successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/get-aliases')
        def get_aliases():
            """Get current tag aliases."""
            try:
                aliases = self.automator.get_tag_aliases()
                return jsonify({'success': True, 'aliases': aliases})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/validate-tags')
        def validate_tags():
            """Validate all tags in the vault."""
            try:
                result = self.automator.validate_tags()
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/vault-stats')
        def vault_stats():
            """Get vault statistics."""
            try:
                result = self.automator.get_vault_stats()
                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update-tag-database', methods=['POST'])
        def update_tag_database():
            """Update the tag database."""
            try:
                # Create background task
                task_id = str(uuid.uuid4())
                self.background_tasks[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'total': 100,  # Arbitrary total for progress
                    'result': None,
                    'start_time': datetime.now().isoformat()
                }
                
                # Start background thread
                thread = threading.Thread(
                    target=self._update_database_background,
                    args=(task_id,)
                )
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Tag database update started'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/config')
        def get_config():
            """Get current configuration."""
            try:
                config = self.automator.get_config()
                return jsonify({'success': True, 'config': config})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update-config', methods=['POST'])
        def update_config():
            """Update configuration."""
            try:
                data = request.get_json()
                new_config = data.get('config', {})
                
                self.automator.update_config(new_config)
                return jsonify({'success': True, 'message': 'Configuration updated successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/ai-prompt')
        def get_ai_prompt():
            """Get current AI prompt."""
            try:
                prompt = self.automator.get_ai_prompt()
                return jsonify({'success': True, 'prompt': prompt})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/update-ai-prompt', methods=['POST'])
        def update_ai_prompt():
            """Update AI prompt."""
            try:
                data = request.get_json()
                new_prompt = data.get('prompt')
                
                if not new_prompt:
                    return jsonify({'success': False, 'error': 'Prompt is required'}), 400
                
                self.automator.set_ai_prompt(new_prompt)
                return jsonify({'success': True, 'message': 'AI prompt updated successfully'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/file-content/<path:file_path>')
        def get_file_content(file_path):
            """Get content of a specific file."""
            try:
                # Security: Ensure file path is within vault
                full_path = self.automator.vault_path / file_path
                if not full_path.exists() or not str(full_path).startswith(str(self.automator.vault_path)):
                    return jsonify({'success': False, 'error': 'File not found or access denied'}), 404
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return jsonify({'success': True, 'content': content})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
    
    def _process_files_background(self, task_id, file_paths, options):
        """Process files in the background."""
        try:
            total_files = len(file_paths)
            processed_files = 0
            
            # Process files in batches to show progress
            batch_size = 5
            results = []
            
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i:i + batch_size]
                batch_result = self.automator.process_multiple_files(batch, options)
                results.extend(batch_result['file_results'])
                processed_files += len(batch)
                
                # Update progress
                self.background_tasks[task_id]['progress'] = (processed_files / total_files) * 100
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.1)
            
            # Task completed
            self.background_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'result': {
                    'total_files': total_files,
                    'processed_files': processed_files,
                    'results': results
                },
                'end_time': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.background_tasks[task_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
    
    def _update_database_background(self, task_id):
        """Update tag database in the background."""
        try:
            # Simulate progress
            for progress in range(0, 101, 10):
                self.background_tasks[task_id]['progress'] = progress
                time.sleep(0.2)
            
            # Actual update
            self.automator.update_tag_database()
            
            # Task completed
            self.background_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'result': {'message': 'Tag database updated successfully'},
                'end_time': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.background_tasks[task_id].update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
    
    def _start_task_cleaner(self):
        """Start background thread to clean up old tasks."""
        def cleaner():
            while True:
                time.sleep(300)  # Clean every 5 minutes
                current_time = datetime.now()
                
                # Remove tasks older than 1 hour
                tasks_to_remove = []
                for task_id, task in self.background_tasks.items():
                    task_time = datetime.fromisoformat(task['start_time'])
                    if (current_time - task_time).total_seconds() > 3600:
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.background_tasks[task_id]
        
        thread = threading.Thread(target=cleaner)
        thread.daemon = True
        thread.start()
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the Flask application."""
        print(f"Starting Obsidian Tag Automator Web Interface...")
        print(f"Vault path: {self.automator.vault_path}")
        print(f"Access at: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

def create_web_app(vault_path=None, gemini_api_key=None):
    """Factory function to create the web app."""
    web_interface = ObsidianTagAutomatorWeb(vault_path, gemini_api_key)
    return web_interface.app

if __name__ == '__main__':
    # Command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Obsidian Tag Automator Web Interface")
    parser.add_argument("-v", "--vault-path", help="Path to the Obsidian vault")
    parser.add_argument("-k", "--gemini-api-key", help="Gemini API key for AI tag suggestions")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create and run the web app
    web_app = ObsidianTagAutomatorWeb(args.vault_path, args.gemini_api_key)
    web_app.run(host=args.host, port=args.port, debug=args.debug)