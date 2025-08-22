Perfect! Now let's create the web frontend. We'll start with the main HTML template and then add the CSS and JavaScript files.

## Step 4: Web Frontend

### File: `web/templates/index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Obsidian Tag Automator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
        }
        
        .gradient-bg {
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        }
        
        .glass-effect {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .neon-glow {
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.5), 0 0 20px rgba(56, 189, 248, 0.3);
        }
        
        .terminal-font {
            font-family: 'Courier New', monospace;
        }
        
        .hover-lift {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .hover-lift:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        
        .pulse-animation {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .slide-in {
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .progress-bar {
            transition: width 0.3s ease;
        }

        .loading-spinner {
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 3px solid white;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
        }

        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .tag-chip {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            margin: 0.25rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .tag-chip:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body class="gradient-bg min-h-screen text-gray-100">
    <!-- Main Container -->
    <div id="app" class="container mx-auto px-4 py-8">
        <!-- Header -->
        <header class="mb-10 text-center">
            <div class="inline-flex items-center justify-center mb-4">
                <div class="w-16 h-16 rounded-full bg-blue-500 flex items-center justify-center neon-glow">
                    <i class="fas fa-tags text-2xl text-white"></i>
                </div>
            </div>
            <h1 class="text-4xl font-bold mb-2 text-blue-300">Obsidian Tag Automator</h1>
            <p class="text-gray-300 max-w-2xl mx-auto">
                AI-powered tag management system for your Obsidian vault. Automate tagging, suggest aliases, and maintain consistency across your knowledge base.
            </p>
        </header>

        <!-- Main Dashboard -->
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Sidebar Navigation -->
            <div class="lg:col-span-1">
                <div class="glass-effect rounded-xl p-6 mb-6">
                    <h2 class="text-xl font-semibold mb-4 text-blue-300 flex items-center">
                        <i class="fas fa-cogs mr-2"></i> Control Panel
                    </h2>
                    <nav class="space-y-2" id="navigation">
                        <a href="#" data-view="dashboard" class="nav-link block py-3 px-4 rounded-lg bg-blue-900/30 hover:bg-blue-800/50 transition-all duration-300 border-l-4 border-blue-500">
                            <i class="fas fa-home mr-3 text-blue-400"></i> Dashboard
                        </a>
                        <a href="#" data-view="automator" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-robot mr-3 text-green-400"></i> Tag Automator
                        </a>
                        <a href="#" data-view="aliases" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-code-branch mr-3 text-purple-400"></i> Tag Aliases
                        </a>
                        <a href="#" data-view="rename" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-edit mr-3 text-yellow-400"></i> Rename Tags
                        </a>
                        <a href="#" data-view="merge" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-object-group mr-3 text-pink-400"></i> Merge Tags
                        </a>
                        <a href="#" data-view="delete" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-trash mr-3 text-red-400"></i> Delete Tags
                        </a>
                        <a href="#" data-view="validate" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-shield-alt mr-3 text-orange-400"></i> Validate Tags
                        </a>
                        <a href="#" data-view="settings" class="nav-link block py-3 px-4 rounded-lg hover:bg-slate-700/50 transition-all duration-300">
                            <i class="fas fa-sliders-h mr-3 text-cyan-400"></i> Settings
                        </a>
                    </nav>
                </div>
                
                <!-- Status Panel -->
                <div class="glass-effect rounded-xl p-6">
                    <h3 class="text-lg font-semibold mb-4 text-blue-300 flex items-center">
                        <i class="fas fa-info-circle mr-2"></i> System Status
                    </h3>
                    <div class="space-y-3" id="status-panel">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Vault Path:</span>
                            <span class="text-sm terminal-font text-green-400" id="vault-path">Loading...</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">AI Status:</span>
                            <span class="flex items-center" id="ai-status">
                                <div class="loading-spinner mr-2"></div>
                                <span class="text-yellow-400">Checking...</span>
                            </span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Total Files:</span>
                            <span class="text-blue-400" id="total-files">-</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Tagged Files:</span>
                            <span class="text-blue-400" id="tagged-files">-</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">Unique Tags:</span>
                            <span class="text-blue-400" id="unique-tags">-</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main Content Area -->
            <div class="lg:col-span-3">
                <!-- Dashboard View -->
                <div id="dashboard-view" class="view-content">
                    <div class="glass-effect rounded-xl p-6 mb-6 slide-in">
                        <div class="flex justify-between items-center mb-6">
                            <h2 class="text-2xl font-bold text-blue-300">Dashboard Overview</h2>
                            <button onclick="refreshDashboard()" class="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors duration-300 flex items-center">
                                <i class="fas fa-sync-alt mr-2"></i> Refresh Data
                            </button>
                        </div>
                        
                        <!-- Stats Cards -->
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                            <div class="bg-gradient-to-br from-blue-900/50 to-blue-800/30 rounded-xl p-5 border border-blue-700/30 hover-lift">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <p class="text-gray-400 text-sm">Total Files</p>
                                        <p class="text-3xl font-bold mt-1" id="dashboard-total-files">-</p>
                                    </div>
                                    <div class="bg-blue-500/20 p-3 rounded-lg">
                                        <i class="fas fa-file-alt text-blue-400 text-xl"></i>
                                    </div>
                                </div>
                                <div class="mt-4 text-sm text-green-400 flex items-center" id="total-files-trend">
                                    <i class="fas fa-minus mr-1"></i> No data
                                </div>
                            </div>
                            
                            <div class="bg-gradient-to-br from-green-900/50 to-green-800/30 rounded-xl p-5 border border-green-700/30 hover-lift">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <p class="text-gray-400 text-sm">Tagged Files</p>
                                        <p class="text-3xl font-bold mt-1" id="dashboard-tagged-files">-</p>
                                    </div>
                                    <div class="bg-green-500/20 p-3 rounded-lg">
                                        <i class="fas fa-tags text-green-400 text-xl"></i>
                                    </div>
                                </div>
                                <div class="mt-4 text-sm text-green-400 flex items-center" id="tagged-files-trend">
                                    <i class="fas fa-minus mr-1"></i> No data
                                </div>
                            </div>
                            
                            <div class="bg-gradient-to-br from-purple-900/50 to-purple-800/30 rounded-xl p-5 border border-purple-700/30 hover-lift">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <p class="text-gray-400 text-sm">Unique Tags</p>
                                        <p class="text-3xl font-bold mt-1" id="dashboard-unique-tags">-</p>
                                    </div>
                                    <div class="bg-purple-500/20 p-3 rounded-lg">
                                        <i class="fas fa-hashtag text-purple-400 text-xl"></i>
                                    </div>
                                </div>
                                <div class="mt-4 text-sm text-yellow-400 flex items-center" id="unique-tags-trend">
                                    <i class="fas fa-minus mr-1"></i> No data
                                </div>
                            </div>
                        </div>
                        
                        <!-- Recent Activity -->
                        <div>
                            <h3 class="text-lg font-semibold mb-4 text-blue-300">Recent Activity</h3>
                            <div class="bg-slate-800/30 rounded-lg overflow-hidden">
                                <div class="overflow-x-auto">
                                    <table class="w-full">
                                        <thead class="bg-slate-700/50">
                                            <tr>
                                                <th class="py-3 px-4 text-left text-sm font-medium text-gray-300">File</th>
                                                <th class="py-3 px-4 text-left text-sm font-medium text-gray-300">Action</th>
                                                <th class="py-3 px-4 text-left text-sm font-medium text-gray-300">Tags</th>
                                                <th class="py-3 px-4 text-left text-sm font-medium text-gray-300">Time</th>
                                            </tr>
                                        </thead>
                                        <tbody id="recent-activity">
                                            <tr>
                                                <td colspan="4" class="py-8 text-center text-gray-400">
                                                    <i class="fas fa-spinner fa-spin mr-2"></i> Loading recent activity...
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div class="glass-effect rounded-xl p-6">
                        <h3 class="text-xl font-semibold mb-4 text-blue-300">Quick Actions</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <button onclick="showView('automator')" class="bg-gradient-to-r from-blue-600 to-blue-800 hover:from-blue-700 hover:to-blue-900 text-white py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-between group hover-lift">
                                <div class="flex items-center">
                                    <div class="bg-blue-500/30 p-3 rounded-lg mr-4 group-hover:bg-blue-500/50 transition-colors">
                                        <i class="fas fa-robot text-blue-300 text-xl"></i>
                                    </div>
                                    <div class="text-left">
                                        <p class="font-medium">Run Tag Automator</p>
                                        <p class="text-sm text-blue-200">Process files with AI suggestions</p>
                                    </div>
                                </div>
                                <i class="fas fa-arrow-right text-blue-300 group-hover:translate-x-1 transition-transform"></i>
                            </button>
                            
                            <button onclick="showView('aliases')" class="bg-gradient-to-r from-green-600 to-green-800 hover:from-green-700 hover:to-green-900 text-white py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-between group hover-lift">
                                <div class="flex items-center">
                                    <div class="bg-green-500/30 p-3 rounded-lg mr-4 group-hover:bg-green-500/50 transition-colors">
                                        <i class="fas fa-code-branch text-green-300 text-xl"></i>
                                    </div>
                                    <div class="text-left">
                                        <p class="font-medium">Generate Aliases</p>
                                        <p class="text-sm text-green-200">Suggest tag aliases automatically</p>
                                    </div>
                                </div>
                                <i class="fas fa-arrow-right text-green-300 group-hover:translate-x-1 transition-transform"></i>
                            </button>
                            
                            <button onclick="showView('validate')" class="bg-gradient-to-r from-purple-600 to-purple-800 hover:from-purple-700 hover:to-purple-900 text-white py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-between group hover-lift">
                                <div class="flex items-center">
                                    <div class="bg-purple-500/30 p-3 rounded-lg mr-4 group-hover:bg-purple-500/50 transition-colors">
                                        <i class="fas fa-shield-alt text-purple-300 text-xl"></i>
                                    </div>
                                    <div class="text-left">
                                        <p class="font-medium">Validate Tags</p>
                                        <p class="text-sm text-purple-200">Check for orphans and malformed tags</p>
                                    </div>
                                </div>
                                <i class="fas fa-arrow-right text-purple-300 group-hover:translate-x-1 transition-transform"></i>
                            </button>
                            
                            <button onclick="showView('settings')" class="bg-gradient-to-r from-cyan-600 to-cyan-800 hover:from-cyan-700 hover:to-cyan-900 text-white py-4 px-6 rounded-xl transition-all duration-300 flex items-center justify-between group hover-lift">
                                <div class="flex items-center">
                                    <div class="bg-cyan-500/30 p-3 rounded-lg mr-4 group-hover:bg-cyan-500/50 transition-colors">
                                        <i class="fas fa-sliders-h text-cyan-300 text-xl"></i>
                                    </div>
                                    <div class="text-left">
                                        <p class="font-medium">Configure AI</p>
                                        <p class="text-sm text-cyan-200">Adjust AI prompts and settings</p>
                                    </div>
                                </div>
                                <i class="fas fa-arrow-right text-cyan-300 group-hover:translate-x-1 transition-transform"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Other views will be dynamically loaded here -->
                <div id="other-views"></div>
            </div>
        </div>
        
        <!-- Footer -->
        <footer class="mt-12 text-center text-gray-500 text-sm">
            <p>Obsidian Tag Automator v1.0 • AI-powered knowledge management</p>
        </footer>
    </div>

    <!-- Progress Modal -->
    <div id="progress-modal" class="modal">
        <div class="glass-effect rounded-xl p-8 max-w-md w-full mx-4">
            <h3 class="text-xl font-semibold mb-4 text-blue-300">Processing...</h3>
            <div class="mb-4">
                <div class="bg-slate-700 rounded-full h-2 mb-2">
                    <div id="progress-bar" class="progress-bar bg-blue-500 h-2 rounded-full" style="width: 0%"></div>
                </div>
                <p class="text-sm text-gray-400 text-center">
                    <span id="progress-text">0%</span> - <span id="progress-status">Initializing...</span>
                </p>
            </div>
            <div id="progress-details" class="text-sm text-gray-300 mb-4 max-h-32 overflow-y-auto"></div>
            <button onclick="closeProgressModal()" class="w-full bg-slate-600 hover:bg-slate-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                Close
            </button>
        </div>
    </div>

    <!-- Notification Toast -->
    <div id="notification" class="fixed top-4 right-4 z-50 hidden">
        <div class="glass-effect rounded-lg p-4 max-w-sm">
            <div class="flex items-center">
                <div id="notification-icon" class="mr-3"></div>
                <div>
                    <p id="notification-title" class="font-semibold"></p>
                    <p id="notification-message" class="text-sm text-gray-300"></p>
                </div>
            </div>
        </div>
    </div>

    <!-- Include JavaScript -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

### File: `web/static/js/app.js`
```javascript
// Obsidian Tag Automator - Frontend JavaScript
class ObsidianTagAutomatorApp {
    constructor() {
        this.currentView = 'dashboard';
        this.currentTask = null;
        this.pollingInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboard();
        this.startStatusPolling();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const view = e.currentTarget.dataset.view;
                this.showView(view);
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshDashboard();
                        break;
                    case '1':
                        e.preventDefault();
                        this.showView('automator');
                        break;
                    case '2':
                        e.preventDefault();
                        this.showView('aliases');
                        break;
                    case '3':
                        e.preventDefault();
                        this.showView('validate');
                        break;
                }
            }
        });
    }

    // API Helper Methods
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(`/api${endpoint}`, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('error', 'API Error', error.message);
            throw error;
        }
    }

    async apiGet(endpoint) {
        return this.apiCall(endpoint, { method: 'GET' });
    }

    async apiPost(endpoint, data) {
        return this.apiCall(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // View Management
    showView(viewName) {
        this.currentView = viewName;
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.dataset.view === viewName) {
                link.classList.add('bg-blue-900/30', 'border-l-4', 'border-blue-500');
                link.classList.remove('hover:bg-slate-700/50');
            } else {
                link.classList.remove('bg-blue-900/30', 'border-l-4', 'border-blue-500');
                link.classList.add('hover:bg-slate-700/50');
            }
        });

        // Hide dashboard view
        document.getElementById('dashboard-view').style.display = 'none';

        // Load specific view
        const otherViewsContainer = document.getElementById('other-views');
        
        switch(viewName) {
            case 'dashboard':
                document.getElementById('dashboard-view').style.display = 'block';
                otherViewsContainer.innerHTML = '';
                this.loadDashboard();
                break;
            case 'automator':
                this.loadAutomatorView(otherViewsContainer);
                break;
            case 'aliases':
                this.loadAliasesView(otherViewsContainer);
                break;
            case 'rename':
                this.loadRenameView(otherViewsContainer);
                break;
            case 'merge':
                this.loadMergeView(otherViewsContainer);
                break;
            case 'delete':
                this.loadDeleteView(otherViewsContainer);
                break;
            case 'validate':
                this.loadValidateView(otherViewsContainer);
                break;
            case 'settings':
                this.loadSettingsView(otherViewsContainer);
                break;
        }
    }

    // Dashboard View
    async loadDashboard() {
        try {
            const [status, files, tags] = await Promise.all([
                this.apiGet('/status'),
                this.apiGet('/files'),
                this.apiGet('/tags')
            ]);

            this.updateStatusPanel(status);
            this.updateDashboardStats(status.stats);
            this.updateRecentActivity(files);
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    updateStatusPanel(status) {
        document.getElementById('vault-path').textContent = status.vault_path;
        
        const aiStatus = document.getElementById('ai-status');
        if (status.ai_status) {
            aiStatus.innerHTML = `
                <span class="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-animation"></span>
                <span class="text-green-400">Online</span>
            `;
        } else {
            aiStatus.innerHTML = `
                <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                <span class="text-red-400">Offline</span>
            `;
        }

        if (status.stats) {
            document.getElementById('total-files').textContent = status.stats.total_files || '-';
            document.getElementById('tagged-files').textContent = status.stats.tagged_files || '-';
            document.getElementById('unique-tags').textContent = status.stats.total_tags || '-';
        }
    }

    updateDashboardStats(stats) {
        if (!stats) return;

        document.getElementById('dashboard-total-files').textContent = stats.total_files || '-';
        document.getElementById('dashboard-tagged-files').textContent = stats.tagged_files || '-';
        document.getElementById('dashboard-unique-tags').textContent = stats.total_tags || '-';

        // Update trends (placeholder logic)
        const totalTrend = document.getElementById('total-files-trend');
        const taggedTrend = document.getElementById('tagged-files-trend');
        const uniqueTrend = document.getElementById('unique-tags-trend');

        totalTrend.innerHTML = '<i class="fas fa-minus mr-1"></i> No data';
        taggedTrend.innerHTML = '<i class="fas fa-minus mr-1"></i> No data';
        uniqueTrend.innerHTML = '<i class="fas fa-minus mr-1"></i> No data';
    }

    updateRecentActivity(files) {
        const tbody = document.getElementById('recent-activity');
        
        if (!files || !files.files || files.files.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="py-8 text-center text-gray-400">
                        No files found in vault
                    </td>
                </tr>
            `;
            return;
        }

        // Show recent files (last 10 modified)
        const recentFiles = files.files
            .sort((a, b) => new Date(b.modified) - new Date(a.modified))
            .slice(0, 10);

        tbody.innerHTML = recentFiles.map(file => `
            <tr class="border-b border-slate-700/30 hover:bg-slate-700/20">
                <td class="py-3 px-4 text-sm terminal-font text-blue-300">${file.name}</td>
                <td class="py-3 px-4 text-sm">
                    <span class="bg-blue-900/50 text-blue-400 py-1 px-2 rounded-full text-xs">Indexed</span>
                </td>
                <td class="py-3 px-4 text-sm">
                    <span class="text-gray-400">Not processed</span>
                </td>
                <td class="py-3 px-4 text-sm text-gray-400">${this.formatDate(file.modified)}</td>
            </tr>
        `).join('');
    }

    // Automator View
    loadAutomatorView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 mb-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Tag Automator</h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-green-400">Processing Options</h3>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">Re-tagging Strategy</label>
                                <select id="retag-option" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white">
                                    <option value="1">Only process files that have NOT been AI-tagged before</option>
                                    <option value="2">Process all files</option>
                                    <option value="3">Only re-tag files that have existing tags but are NOT AI-tagged</option>
                                    <option value="4">Do NOT re-tag any files that already have tags</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">File Selection</label>
                                <div class="space-y-2">
                                    <label class="flex items-center">
                                        <input type="radio" name="file-selection" value="all" checked class="mr-2">
                                        <span>Process all files in vault</span>
                                    </label>
                                    <label class="flex items-center">
                                        <input type="radio" name="file-selection" value="pattern" class="mr-2">
                                        <span>Process files matching pattern</span>
                                    </label>
                                    <label class="flex items-center">
                                        <input type="radio" name="file-selection" value="selected" class="mr-2">
                                        <span>Process selected files</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div id="pattern-input" class="hidden">
                                <label class="block text-sm font-medium text-gray-300 mb-2">File Pattern</label>
                                <input type="text" id="file-pattern" placeholder="*.md, notes/*.md" 
                                       class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white">
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-blue-400">File Selection</h3>
                        <div id="file-list-container" class="h-64 overflow-y-auto bg-slate-900/50 rounded-lg p-4">
                            <div class="text-center text-gray-400 py-8">
                                <i class="fas fa-spinner fa-spin mr-2"></i> Loading files...
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="flex justify-between items-center">
                    <div class="text-sm text-gray-400">
                        <span id="selected-count">0</span> files selected
                    </div>
                    <button onclick="app.startTagProcessing()" 
                            class="bg-gradient-to-r from-green-600 to-green-800 hover:from-green-700 hover:to-green-900 text-white py-3 px-6 rounded-lg transition-all duration-300 flex items-center">
                        <i class="fas fa-play mr-2"></i> Start Processing
                    </button>
                </div>
            </div>
        `;
        
        this.setupAutomatorEventListeners();
        this.loadFileList();
    }

    setupAutomatorEventListeners() {
        // File selection radio buttons
        document.querySelectorAll('input[name="file-selection"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const patternInput = document.getElementById('pattern-input');
                const fileListContainer = document.getElementById('file-list-container');
                
                if (e.target.value === 'pattern') {
                    patternInput.classList.remove('hidden');
                    fileListContainer.classList.add('hidden');
                } else if (e.target.value === 'selected') {
                    patternInput.classList.add('hidden');
                    fileListContainer.classList.remove('hidden');
                } else {
                    patternInput.classList.add('hidden');
                    fileListContainer.classList.add('hidden');
                }
            });
        });
    }

    async loadFileList() {
        try {
            const response = await this.apiGet('/files');
            const container = document.getElementById('file-list-container');
            
            if (!response.files || response.files.length === 0) {
                container.innerHTML = `
                    <div class="text-center text-gray-400 py-8">
                        No files found in vault
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="space-y-2">
                    ${response.files.map(file => `
                        <label class="flex items-center p-2 hover:bg-slate-700/50 rounded cursor-pointer">
                            <input type="checkbox" value="${file.full_path}" class="file-checkbox mr-3">
                            <div class="flex-1">
                                <div class="text-sm font-medium">${file.name}</div>
                                <div class="text-xs text-gray-400">${file.path}</div>
                            </div>
                            <div class="text-xs text-gray-400">
                                ${this.formatFileSize(file.size)}
                            </div>
                        </label>
                    `).join('')}
                </div>
            `;

            // Setup checkbox listeners
            document.querySelectorAll('.file-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', () => this.updateSelectedCount());
            });
        } catch (error) {
            console.error('Failed to load file list:', error);
        }
    }

    updateSelectedCount() {
        const checkboxes = document.querySelectorAll('.file-checkbox:checked');
        document.getElementById('selected-count').textContent = checkboxes.length;
    }

    async startTagProcessing() {
        const fileSelection = document.querySelector('input[name="file-selection"]:checked').value;
        let filePaths = [];

        if (fileSelection === 'all') {
            // Get all files
            const response = await this.apiGet('/files');
            filePaths = response.files.map(f => f.full_path);
        } else if (fileSelection === 'pattern') {
            // For now, we'll get all files and filter client-side
            // In a real implementation, this should be done server-side
            const response = await this.apiGet('/files');
            const pattern = document.getElementById('file-pattern').value;
            const regex = new RegExp(pattern.replace(/\*/g, '.*'));
            filePaths = response.files.filter(f => regex.test(f.path)).map(f => f.full_path);
        } else if (fileSelection === 'selected') {
            // Get selected files
            const checkboxes = document.querySelectorAll('.file-checkbox:checked');
            filePaths = Array.from(checkboxes).map(cb => cb.value);
        }

        if (filePaths.length === 0) {
            this.showNotification('warning', 'No Files Selected', 'Please select files to process.');
            return;
        }

        const options = {
            re_tag_option: document.getElementById('retag-option').value
        };

        try {
            const response = await this.apiPost('/process-multiple-files', {
                file_paths: filePaths,
                options: options
            });

            this.showProgressModal(response.task_id);
            this.startTaskPolling(response.task_id);
        } catch (error) {
            console.error('Failed to start processing:', error);
        }
    }

    // Progress Modal Management
    showProgressModal(taskId) {
        this.currentTask = taskId;
        const modal = document.getElementById('progress-modal');
        modal.classList.add('show');
        
        // Reset progress
        document.getElementById('progress-bar').style.width = '0%';
        document.getElementById('progress-text').textContent = '0%';
        document.getElementById('progress-status').textContent = 'Initializing...';
        document.getElementById('progress-details').innerHTML = '';
    }

    closeProgressModal() {
        const modal = document.getElementById('progress-modal');
        modal.classList.remove('show');
        this.currentTask = null;
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    startTaskPolling(taskId) {
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await this.apiGet(`/task-status/${taskId}`);
                this.updateProgressModal(response.task);
                
                if (response.task.status === 'completed' || response.task.status === 'failed') {
                    clearInterval(this.pollingInterval);
                    this.pollingInterval = null;
                    
                    if (response.task.status === 'completed') {
                        this.showNotification('success', 'Processing Complete', 'Files have been processed successfully.');
                        this.loadDashboard(); // Refresh dashboard
                    } else {
                        this.showNotification('error', 'Processing Failed', response.task.error || 'Unknown error occurred.');
                    }
                }
            } catch (error) {
                console.error('Failed to poll task status:', error);
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
        }, 1000);
    }

    updateProgressModal(task) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const progressStatus = document.getElementById('progress-status');
        const progressDetails = document.getElementById('progress-details');

        progressBar.style.width = `${task.progress}%`;
        progressText.textContent = `${Math.round(task.progress)}%`;
        progressStatus.textContent = task.status.charAt(0).toUpperCase() + task.status.slice(1);

        if (task.result && task.result.results) {
            const results = task.result.results;
            let detailsHtml = '<div class="space-y-1">';
            
            results.forEach(result => {
                const statusIcon = result.success ? '✓' : '✗';
                const statusColor = result.success ? 'text-green-400' : 'text-red-400';
                detailsHtml += `
                    <div class="text-sm">
                        <span class="${statusColor}">${statusIcon}</span>
                        <span class="ml-2">${result.file_path}</span>
                    </div>
                `;
            });
            
            detailsHtml += '</div>';
            progressDetails.innerHTML = detailsHtml;
        }
    }

    // Other Views (simplified implementations)
    loadAliasesView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Tag Aliases</h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-purple-400">Generate Aliases</h3>
                        <p class="text-gray-300 mb-4">Automatically suggest tag aliases based on similar names.</p>
                        
                        <div class="space-y-3">
                            <button onclick="app.generateAliases('heuristic')" 
                                    class="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                                <i class="fas fa-magic mr-2"></i> Heuristic Detection
                            </button>
                            <button onclick="app.generateAliases('ai')" 
                                    class="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                                <i class="fas fa-brain mr-2"></i> AI-Powered Detection
                            </button>
                        </div>
                    </div>
                    
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-green-400">Current Aliases</h3>
                        <div id="current-aliases" class="space-y-2 max-h-48 overflow-y-auto">
                            <div class="text-center text-gray-400 py-4">
                                <i class="fas fa-spinner fa-spin mr-2"></i> Loading aliases...
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="suggested-aliases-container" class="hidden">
                    <h3 class="text-lg font-semibold mb-4 text-yellow-400">Suggested Aliases</h3>
                    <div id="suggested-aliases" class="bg-slate-800/30 rounded-lg p-4 mb-4"></div>
                    <div class="flex justify-end space-x-3">
                        <button onclick="app.clearSuggestedAliases()" 
                                class="bg-slate-600 hover:bg-slate-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                            Clear
                        </button>
                        <button onclick="app.saveAliases()" 
                                class="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                            Save Aliases
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.loadCurrentAliases();
    }

    async loadCurrentAliases() {
        try {
            const response = await this.apiGet('/get-aliases');
            const container = document.getElementById('current-aliases');
            
            if (Object.keys(response.aliases).length === 0) {
                container.innerHTML = '<div class="text-center text-gray-400 py-4">No aliases configured</div>';
                return;
            }

            container.innerHTML = Object.entries(response.aliases).map(([alias, canonical]) => `
                <div class="flex justify-between items-center p-2 bg-slate-700/30 rounded">
                    <div>
                        <span class="text-yellow-400">${alias}</span>
                        <i class="fas fa-arrow-right mx-2 text-gray-400"></i>
                        <span class="text-green-400">${canonical}</span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load aliases:', error);
        }
    }

    async generateAliases(method) {
        try {
            const response = await this.apiPost('/generate-aliases', { method });
            
            if (response.success && Object.keys(response.suggested_aliases).length > 0) {
                this.displaySuggestedAliases(response.suggested_aliases);
                this.showNotification('success', 'Aliases Generated', `Found ${Object.keys(response.suggested_aliases).length} suggested aliases.`);
            } else {
                this.showNotification('info', 'No Aliases', 'No aliases were suggested.');
            }
        } catch (error) {
            console.error('Failed to generate aliases:', error);
        }
    }

    displaySuggestedAliases(aliases) {
        const container = document.getElementById('suggested-aliases');
        const wrapper = document.getElementById('suggested-aliases-container');
        
        container.innerHTML = Object.entries(aliases).map(([alias, canonical]) => `
            <div class="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg mb-2">
                <div class="flex items-center space-x-3">
                    <input type="checkbox" checked class="alias-checkbox" data-alias="${alias}" data-canonical="${canonical}">
                    <div>
                        <span class="text-yellow-400 font-mono">${alias}</span>
                        <i class="fas fa-arrow-right mx-2 text-gray-400"></i>
                        <span class="text-green-400 font-mono">${canonical}</span>
                    </div>
                </div>
            </div>
        `).join('');
        
        wrapper.classList.remove('hidden');
    }

    clearSuggestedAliases() {
        document.getElementById('suggested-aliases-container').classList.add('hidden');
        document.getElementById('suggested-aliases').innerHTML = '';
    }

    async saveAliases() {
        const checkboxes = document.querySelectorAll('.alias-checkbox:checked');
        const aliases = {};
        
        checkboxes.forEach(checkbox => {
            aliases[checkbox.dataset.alias] = checkbox.dataset.canonical;
        });

        try {
            const response = await this.apiPost('/save-aliases', { aliases });
            this.showNotification('success', 'Aliases Saved', 'Tag aliases have been saved successfully.');
            this.clearSuggestedAliases();
            this.loadCurrentAliases();
        } catch (error) {
            console.error('Failed to save aliases:', error);
        }
    }

    // Placeholder methods for other views
    loadRenameView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Rename Tags</h2>
                <div class="text-center text-gray-400 py-8">
                    <i class="fas fa-tools text-4xl mb-4"></i>
                    <p>Tag renaming functionality coming soon...</p>
                </div>
            </div>
        `;
    }

    loadMergeView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Merge Tags</h2>
                <div class="text-center text-gray-400 py-8">
                    <i class="fas fa-object-group text-4xl mb-4"></i>
                    <p>Tag merging functionality coming soon...</p>
                </div>
            </div>
        `;
    }

    loadDeleteView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Delete Tags</h2>
                <div class="text-center text-gray-400 py-8">
                    <i class="fas fa-trash text-4xl mb-4"></i>
                    <p>Tag deletion functionality coming soon...</p>
                </div>
            </div>
        `;
    }

    async loadValidateView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Validate Tags</h2>
                
                <div class="mb-6">
                    <button onclick="app.validateTags()" 
                            class="bg-orange-600 hover:bg-orange-700 text-white py-3 px-6 rounded-lg transition-colors duration-300">
                        <i class="fas fa-shield-alt mr-2"></i> Validate All Tags
                    </button>
                </div>
                
                <div id="validation-results" class="hidden">
                    <!-- Results will be loaded here -->
                </div>
            </div>
        `;
    }

    async validateTags() {
        try {
            const response = await this.apiGet('/validate-tags');
            this.displayValidationResults(response.validation_report);
        } catch (error) {
            console.error('Failed to validate tags:', error);
        }
    }

    displayValidationResults(report) {
        const container = document.getElementById('validation-results');
        container.classList.remove('hidden');
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div class="bg-slate-800/30 rounded-lg p-4">
                    <div class="text-2xl font-bold text-blue-400">${report.total_tags}</div>
                    <div class="text-sm text-gray-400">Total Tags</div>
                </div>
                <div class="bg-slate-800/30 rounded-lg p-4">
                    <div class="text-2xl font-bold text-red-400">${report.malformed_tags.length}</div>
                    <div class="text-sm text-gray-400">Malformed Tags</div>
                </div>
                <div class="bg-slate-800/30 rounded-lg p-4">
                    <div class="text-2xl font-bold text-yellow-400">${report.duplicate_tags.length}</div>
                    <div class="text-sm text-gray-400">Duplicate Groups</div>
                </div>
                <div class="bg-slate-800/30 rounded-lg p-4">
                    <div class="text-2xl font-bold text-purple-400">${report.orphaned_tags.length}</div>
                    <div class="text-sm text-gray-400">Orphaned Tags</div>
                </div>
            </div>
            
            ${report.malformed_tags.length > 0 ? `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3 text-red-400">Malformed Tags</h3>
                    <div class="bg-slate-800/30 rounded-lg p-4">
                        ${report.malformed_tags.map(tag => `<span class="tag-chip bg-red-900/50 text-red-300">${tag}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${report.duplicate_tags.length > 0 ? `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3 text-yellow-400">Duplicate Tag Groups</h3>
                    <div class="space-y-2">
                        ${report.duplicate_tags.map(group => `
                            <div class="bg-slate-800/30 rounded-lg p-3">
                                ${group.map(tag => `<span class="tag-chip bg-yellow-900/50 text-yellow-300">${tag}</span>`).join('')}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${report.orphaned_tags.length > 0 ? `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-3 text-purple-400">Orphaned Tags (used in only 1 file)</h3>
                    <div class="bg-slate-800/30 rounded-lg p-4 max-h-48 overflow-y-auto">
                        ${report.orphaned_tags.slice(0, 20).map(tag => `<span class="tag-chip bg-purple-900/50 text-purple-300">${tag}</span>`).join('')}
                        ${report.orphaned_tags.length > 20 ? `<div class="text-sm text-gray-400 mt-2">... and ${report.orphaned_tags.length - 20} more</div>` : ''}
                    </div>
                </div>
            ` : ''}
        `;
    }

    loadSettingsView(container) {
        container.innerHTML = `
            <div class="glass-effect rounded-xl p-6 fade-in">
                <h2 class="text-2xl font-bold mb-6 text-blue-300">Settings</h2>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-cyan-400">AI Configuration</h3>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">AI Prompt</label>
                                <textarea id="ai-prompt" rows="8" 
                                          class="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white font-mono text-sm"
                                          placeholder="Enter AI prompt..."></textarea>
                            </div>
                            
                            <button onclick="app.updateAIPrompt()" 
                                    class="w-full bg-cyan-600 hover:bg-cyan-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                                <i class="fas fa-save mr-2"></i> Update AI Prompt
                            </button>
                        </div>
                    </div>
                    
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-orange-400">Exclusions</h3>
                        
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">Excluded Tags</label>
                                <div id="excluded-tags" class="bg-slate-700 rounded-lg p-3 min-h-[100px] max-h-32 overflow-y-auto">
                                    <!-- Tags will be loaded here -->
                                </div>
                                <div class="flex mt-2 space-x-2">
                                    <input type="text" id="new-excluded-tag" placeholder="Add tag to exclude" 
                                           class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm">
                                    <button onclick="app.addExcludedTag()" 
                                            class="bg-orange-600 hover:bg-orange-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                                        Add
                                    </button>
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">Excluded Paths</label>
                                <div id="excluded-paths" class="bg-slate-700 rounded-lg p-3 min-h-[100px] max-h-32 overflow-y-auto">
                                    <!-- Paths will be loaded here -->
                                </div>
                                <div class="flex mt-2 space-x-2">
                                    <input type="text" id="new-excluded-path" placeholder="Add path to exclude" 
                                           class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm">
                                    <button onclick="app.addExcludedPath()" 
                                            class="bg-orange-600 hover:bg-orange-700 text-white py-2 px-4 rounded-lg transition-colors duration-300">
                                        Add
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-6">
                    <button onclick="app.updateTagDatabase()" 
                            class="bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-lg transition-colors duration-300">
                        <i class="fas fa-database mr-2"></i> Update Tag Database
                    </button>
                </div>
            </div>
        `;
        
        this.loadSettings();
    }

    async loadSettings() {
        try {
            const [config, prompt] = await Promise.all([
                this.apiGet('/config'),
                this.apiGet('/ai-prompt')
            ]);

            // Load AI prompt
            document.getElementById('ai-prompt').value = prompt.prompt;

            // Load excluded tags
            const excludedTagsContainer = document.getElementById('excluded-tags');
            const excludedTags = config.config.excluded_tags || [];
            if (excludedTags.length === 0) {
                excludedTagsContainer.innerHTML = '<div class="text-gray-400 text-sm">No excluded tags</div>';
            } else {
                excludedTagsContainer.innerHTML = excludedTags.map(tag => `
                    <span class="inline-flex items-center bg-orange-900/50 text-orange-300 px-2 py-1 rounded-full text-sm mr-1 mb-1">
                        ${tag}
                        <button onclick="app.removeExcludedTag('${tag}')" class="ml-1 hover:text-red-400">
                            <i class="fas fa-times"></i>
                        </button>
                    </span>
                `).join('');
            }

            // Load excluded paths
            const excludedPathsContainer = document.getElementById('excluded-paths');
            const excludedPaths = config.config.excluded_paths || [];
            if (excludedPaths.length === 0) {
                excludedPathsContainer.innerHTML = '<div class="text-gray-400 text-sm">No excluded paths</div>';
            } else {
                excludedPathsContainer.innerHTML = excludedPaths.map(path => `
                    <span class="inline-flex items-center bg-orange-900/50 text-orange-300 px-2 py-1 rounded-full text-sm mr-1 mb-1">
                        ${path}
                        <button onclick="app.removeExcludedPath('${path}')" class="ml-1 hover:text-red-400">
                            <i class="fas fa-times"></i>
                        </button>
                    </span>
                `).join('');
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    async updateAIPrompt() {
        const prompt = document.getElementById('ai-prompt').value;
        
        try {
            await this.apiPost('/update-ai-prompt', { prompt });
            this.showNotification('success', 'AI Prompt Updated', 'The AI prompt has been updated successfully.');
        } catch (error) {
            console.error('Failed to update AI prompt:', error);
        }
    }

    async addExcludedTag() {
        const input = document.getElementById('new-excluded-tag');
        const tag = input.value.trim();
        
        if (!tag) return;
        
        try {
            const configResponse = await this.apiGet('/config');
            const config = configResponse.config;
            const excludedTags = config.excluded_tags || [];
            
            if (!excludedTags.includes(tag)) {
                excludedTags.push(tag);
                await this.apiPost('/update-config', { config: { ...config, excluded_tags } });
                input.value = '';
                this.loadSettings(); // Reload settings
                this.showNotification('success', 'Tag Added', `"${tag}" has been added to excluded tags.`);
            }
        } catch (error) {
            console.error('Failed to add excluded tag:', error);
        }
    }

    async removeExcludedTag(tag) {
        try {
            const configResponse = await this.apiGet('/config');
            const config = configResponse.config;
            const excludedTags = config.excluded_tags || [];
            
            const updatedTags = excludedTags.filter(t => t !== tag);
            await this.apiPost('/update-config', { config: { ...config, excluded_tags: updatedTags } });
            this.loadSettings(); // Reload settings
            this.showNotification('success', 'Tag Removed', `"${tag}" has been removed from excluded tags.`);
        } catch (error) {
            console.error('Failed to remove excluded tag:', error);
        }
    }

    async addExcludedPath() {
        const input = document.getElementById('new-excluded-path');
        const path = input.value.trim();
        
        if (!path) return;
        
        try {
            const configResponse = await this.apiGet('/config');
            const config = configResponse.config;
            const excludedPaths = config.excluded_paths || [];
            
            if (!excludedPaths.includes(path)) {
                excludedPaths.push(path);
                await this.apiPost('/update-config', { config: { ...config, excluded_paths } });
                input.value = '';
                this.loadSettings(); // Reload settings
                this.showNotification('success', 'Path Added', `"${path}" has been added to excluded paths.`);
            }
        } catch (error) {
            console.error('Failed to add excluded path:', error);
        }
    }

    async removeExcludedPath(path) {
        try {
            const configResponse = await this.apiGet('/config');
            const config = configResponse.config;
            const excludedPaths = config.excluded_paths || [];
            
            const updatedPaths = excludedPaths.filter(p => p !== path);
            await this.apiPost('/update-config', { config: { ...config, excluded_paths: updatedPaths } });
            this.loadSettings(); // Reload settings
            this.showNotification('success', 'Path Removed', `"${path}" has been removed from excluded paths.`);
        } catch (error) {
            console.error('Failed to remove excluded path:', error);
        }
    }

    async updateTagDatabase() {
        try {
            const response = await this.apiPost('/update-tag-database');
            this.showProgressModal(response.task_id);
            this.startTaskPolling(response.task_id);
        } catch (error) {
            console.error('Failed to update tag database:', error);
        }
    }

    // Utility Methods
    refreshDashboard() {
        this.loadDashboard();
        this.showNotification('info', 'Refreshing', 'Dashboard data is being refreshed...');
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showNotification(type, title, message) {
        const notification = document.getElementById('notification');
        const icon = document.getElementById('notification-icon');
        const titleEl = document.getElementById('notification-title');
        const messageEl = document.getElementById('notification-message');

        // Set icon and colors based on type
        const typeConfig = {
            success: {
                icon: '<i class="fas fa-check-circle text-green-400 text-xl"></i>',
                bgColor: 'bg-green-900/50'
            },
            error: {
                icon: '<i class="fas fa-exclamation-circle text-red-400 text-xl"></i>',
                bgColor: 'bg-red-900/50'
            },
            warning: {
                icon: '<i class="fas fa-exclamation-triangle text-yellow-400 text-xl"></i>',
                bgColor: 'bg-yellow-900/50'
            },
            info: {
                icon: '<i class="fas fa-info-circle text-blue-400 text-xl"></i>',
                bgColor: 'bg-blue-900/50'
            }
        };

        const config = typeConfig[type] || typeConfig.info;
        
        icon.innerHTML = config.icon;
        titleEl.textContent = title;
        messageEl.textContent = message;
        
        // Show notification
        notification.classList.remove('hidden');
        notification.firstElementChild.className = `glass-effect rounded-lg p-4 max-w-sm ${config.bgColor}`;
        
        // Hide after 5 seconds
        setTimeout(() => {
            notification.classList.add('hidden');
        }, 5000);
    }

    startStatusPolling() {
        // Poll for status updates every 30 seconds
        setInterval(() => {
            if (this.currentView === 'dashboard') {
                this.loadDashboard();
            }
        }, 30000);
    }
}

// Global functions for HTML onclick handlers
function showView(viewName) {
    app.showView(viewName);
}

function refreshDashboard() {
    app.refreshDashboard();
}

function closeProgressModal() {
    app.closeProgressModal();
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ObsidianTagAutomatorApp();
});
```

### File: `web/static/css/style.css`
```css
/* Obsidian Tag Automator - Custom Styles */

/* Base Styles */
:root {
    --primary-color: #3b82f6;
    --secondary-color: #8b5cf6;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    --dark-bg: #0f172a;
    --glass-bg: rgba(30, 41, 59, 0.7);
    --border-color: rgba(148, 163, 184, 0.1);
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
    color: #e2e8f0;
    min-height: 100vh;
}

/* Glass Effect */
.glass-effect {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
}

/* Animations */
@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.7;
    }
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
}

@keyframes glow {
    0%, 100% {
        box-shadow: 0 0 5px rgba(56, 189, 248, 0.5);
    }
    50% {
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.8), 0 0 30px rgba(56, 189, 248, 0.6);
    }
}

.slide-in {
    animation: slideIn 0.5s ease-out;
}

.fade-in {
    animation: fadeIn 0.5s ease-in;
}

.pulse-animation {
    animation: pulse 2s infinite;
}

.hover-lift {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.hover-lift:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.neon-glow {
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.5), 0 0 20px rgba(56, 189, 248, 0.3);
}

.neon-glow:hover {
    animation: glow 2s infinite;
}

/* Loading Spinner */
.loading-spinner {
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top: 3px solid white;
    width: 20px;
    height: 20px;
    animation: spin 1s linear infinite;
}

/* Progress Bar */
.progress-bar {
    transition: width 0.3s ease;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    border-radius: 9999px;
}

/* Scrollbar Styles */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(30, 41, 59, 0.3);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.8);
}

/* Typography */
.terminal-font {
    font-family: 'Courier New', monospace;
}

.text-gradient {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Buttons */
.btn-primary {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
}

.btn-primary:hover {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3);
}

.btn-secondary {
    background: rgba(148, 163, 184, 0.2);
    color: #e2e8f0;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
    border: 1px solid rgba(148, 163, 184, 0.3);
    cursor: pointer;
}

.btn-secondary:hover {
    background: rgba(148, 163, 184, 0.3);
    transform: translateY(-2px);
}

.btn-success {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
}

.btn-success:hover {
    background: linear-gradient(135deg, #059669, #047857);
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(5, 150, 105, 0.3);
}

.btn-danger {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
}

.btn-danger:hover {
    background: linear-gradient(135deg, #dc2626, #b91c1c);
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(220, 38, 38, 0.3);
}

/* Cards */
.card {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-color);
    border-radius: 0.75rem;
    padding: 1.5rem;
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0;
}

/* Forms */
.form-group {
    margin-bottom: 1rem;
}

.form-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: #cbd5e1;
    margin-bottom: 0.5rem;
}

.form-input {
    width: 100%;
    padding: 0.75rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 0.5rem;
    color: #e2e8f0;
    font-size: 0.875rem;
    transition: all 0.3s ease;
}

.form-input:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
    width: 100%;
    padding: 0.75rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 0.5rem;
    color: #e2e8f0;
    font-size: 0.875rem;
    font-family: 'Courier New', monospace;
    resize: vertical;
    transition: all 0.3s ease;
}

.form-textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-select {
    width: 100%;
    padding: 0.75rem 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 0.5rem;
    color: #e2e8f0;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.form-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-checkbox {
    width: 1rem;
    height: 1rem;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 0.25rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.form-checkbox:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}

/* Tables */
.table-container {
    background: rgba(30, 41, 59, 0.3);
    border-radius: 0.75rem;
    overflow: hidden;
}

.table {
    width: 100%;
    border-collapse: collapse;
}

.table th {
    background: rgba(30, 41, 59, 0.8);
    padding: 0.75rem 1rem;
    text-align: left;
    font-weight: 500;
    color: #cbd5e1;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.table tbody tr:hover {
    background: rgba(59, 130, 246, 0.1);
}

/* Tags */
.tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    margin: 0.25rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
    transition: all 0.2s ease;
    cursor: pointer;
}

.tag:hover {
    transform: scale(1.05);
}

.tag-primary {
    background: rgba(59, 130, 246, 0.2);
    color: #93c5fd;
}

.tag-success {
    background: rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
}

.tag-warning {
    background: rgba(245, 158, 11, 0.2);
    color: #fcd34d;
}

.tag-error {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
}

.tag-info {
    background: rgba(139, 92, 246, 0.2);
    color: #c4b5fd;
}

/* Modal */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(5px);
}

.modal.show {
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-color);
    border-radius: 1rem;
    padding: 2rem;
    max-width: 90vw;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.modal-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 0;
}

.modal-close {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.5rem;
    cursor: pointer;
    transition: color 0.3s ease;
}

.modal-close:hover {
    color: #e2e8f0;
}

/* Notifications */
.notification {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1100;
    min-width: 300px;
    max-width: 500px;
}

.notification-content {
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.notification-success {
    background: rgba(16, 185, 129, 0.2);
    border-color: rgba(16, 185, 129, 0.3);
}

.notification-error {
    background: rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.3);
}

.notification-warning {
    background: rgba(245, 158, 11, 0.2);
    border-color: rgba(245, 158, 11, 0.3);
}

.notification-info {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.3);
}

/* Navigation */
.nav-link {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-radius: 0.5rem;
    text-decoration: none;
    color: #cbd5e1;
    transition: all 0.3s ease;
}

.nav-link:hover {
    background: rgba(59, 130, 246, 0.1);
    color: #e2e8f0;
}

.nav-link.active {
    background: rgba(59, 130, 246, 0.2);
    border-left: 4px solid #3b82f6;
    color: #e2e8f0;
}

/* Status Indicators */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.status-dot {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
}

.status-online {
    background: #10b981;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

.status-offline {
    background: #ef4444;
}

.status-warning {
    background: #f59e0b;
}

/* Utility Classes */
.text-truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.text-center {
    text-align: center;
}

.text-right {
    text-align: right;
}

.text-left {
    text-align: left;
}

.d-flex {
    display: flex;
}

.align-items-center {
    align-items: center;
}

.justify-content-between {
    justify-content: space-between;
}

.justify-content-center {
    justify-content: center;
}

.w-100 {
    width: 100%;
}

.h-100 {
    height: 100%;
}

.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mt-5 { margin-top: 1.25rem; }

.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-5 { margin-bottom: 1.25rem; }

.ml-1 { margin-left: 0.25rem; }
.ml-2 { margin-left: 0.5rem; }
.ml-3 { margin-left: 0.75rem; }
.ml-4 { margin-left: 1rem; }
.ml-5 { margin-left: 1.25rem; }

.mr-1 { margin-right: 0.25rem; }
.mr-2 { margin-right: 0.5rem; }
.mr-3 { margin-right: 0.75rem; }
.mr-4 { margin-right: 1rem; }
.mr-5 { margin-right: 1.25rem; }

.p-1 { padding: 0.25rem; }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-5 { padding: 1.25rem; }

.pt-1 { padding-top: 0.25rem; }
.pt-2 { padding-top: 0.5rem; }
.pt-3 { padding-top: 0.75rem; }
.pt-4 { padding-top: 1rem; }
.pt-5 { padding-top: 1.25rem; }

.pb-1 { padding-bottom: 0.25rem; }
.pb-2 { padding-bottom: 0.5rem; }
.pb-3 { padding-bottom: 0.75rem; }
.pb-4 { padding-bottom: 1rem; }
.pb-5 { padding-bottom: 1.25rem; }

.pl-1 { padding-left: 0.25rem; }
.pl-2 { padding-left: 0.5rem; }
.pl-3 { padding-left: 0.75rem; }
.pl-4 { padding-left: 1rem; }
.pl-5 { padding-left: 1.25rem; }

.pr-1 { padding-right: 0.25rem; }
.pr-2 { padding-right: 0.5rem; }
.pr-3 { padding-right: 0.75rem; }
.pr-4 { padding-right: 1rem; }
.pr-5 { padding-right: 1.25rem; }

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }
    
    .grid {
        grid-template-columns: 1fr;
    }
    
    .modal-content {
        margin: 1rem;
        padding: 1.5rem;
    }
    
    .notification {
        left: 1rem;
        right: 1rem;
        min-width: auto;
    }
    
    .table-container {
        overflow-x: auto;
    }
    
    .table {
        min-width: 600px;
    }
}

@media (max-width: 480px) {
    .card {
        padding: 1rem;
    }
    
    .btn-primary,
    .btn-secondary,
    .btn-success,
    .btn-danger {
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
    }
    
    .form-input,
    .form-textarea,
    .form-select {
        padding: 0.5rem 0.75rem;
        font-size: 0.875rem;
    }
}

/* Print Styles */
@media print {
    body {
        background: white;
        color: black;
    }
    
    .glass-effect {
        background: white;
        border: 1px solid #e5e7eb;
    }
    
    .btn-primary,
    .btn-secondary,
    .btn-success,
    .btn-danger {
        display: none;
    }
    
    .modal {
        display: none;
    }
    
    .notification {
        display: none;
    }
}
```

### File: `tag_automator_cli.py` (Main Entry Point)
```python
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
```

### File: `requirements.txt`
```txt
# Core dependencies
Flask==2.3.3
Flask-CORS==4.0.0
Werkzeug==2.3.7
click==8.1.7
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3

# AI Integration
google-generativeai==0.8.5
google-api-core==2.25.1
google-api-python-client==2.179.0
google-auth==2.40.3
google-auth-httplib2==0.2.0
googleapis-common-protos==1.70.0
grpcio==1.74.0
grpcio-status==1.71.2
proto-plus==1.26.1
protobuf==5.29.5
pyasn1==0.6.1
pyasn1_modules==0.4.2

# YAML Processing
PyYAML==6.0.2

# Environment and Configuration
python-dotenv==1.1.1

# CLI Interface
rich==14.1.0

# HTTP Requests
requests==2.32.5
urllib3==2.5.0
certifi==2025.8.3

# Data Validation
pydantic==2.11.7
pydantic_core==2.33.2
annotated-types==0.7.0
typing-extensions==4.14.1

# Async Support (for future enhancements)
anyio==3.7.1
sniffio==1.3.0

# Development and Testing
pytest==7.4.3
pytest-cov==4.1.0
black==23.9.1
flake8==6.1.0
mypy==1.6.1
```

### File: `README.md`
```markdown
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

Your Obsidian Tag Automator is now ready to use! The web interface provides a beautiful, modern way to manage your tags, while the CLI interface offers powerful command-line functionality. Both interfaces use the same core logic, ensuring consistency across all usage scenarios.