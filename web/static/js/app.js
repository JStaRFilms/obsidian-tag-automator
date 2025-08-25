// Obsidian Tag Automator - Frontend JavaScript
class ObsidianTagAutomatorApp {
    constructor() {
        this.currentView = 'dashboard';
        this.currentTask = null;
        this.pollingInterval = null;
        this.cache = new Map();
        this.cacheTTL = 30000; // 30 seconds
        this.performanceMetrics = {
            apiCalls: [],
            loadTimes: {},
            errorCount: 0
        };
        this.init();
    }

    init() {
        const startTime = performance.now();
        this.setupEventListeners();
        this.loadDashboard();
        this.startStatusPolling();
        this.performanceMetrics.loadTimes.initialization = performance.now() - startTime;
        
        // Add performance indicator to the UI
        this.addPerformanceIndicator();
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

    // API Helper Methods with Caching
    async apiCall(endpoint, options = {}) {
        const startTime = performance.now();
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaultOptions, ...options };
        const cacheKey = `${endpoint}_${JSON.stringify(config)}`;
        
        // Check cache for GET requests
        if (!config.method || config.method === 'GET') {
            const cached = this.cache.get(cacheKey);
            if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
                // Record cache hit
                this.performanceMetrics.apiCalls.push({
                    endpoint,
                    duration: performance.now() - startTime,
                    cached: true,
                    timestamp: Date.now()
                });
                return cached.data;
            }
        }

        try {
            const response = await fetch(`/api${endpoint}`, config);
            const data = await response.json();
            
            const duration = performance.now() - startTime;
            
            // Record API call metrics
            this.performanceMetrics.apiCalls.push({
                endpoint,
                duration,
                status: response.status,
                cached: false,
                timestamp: Date.now()
            });
            
            // Update performance indicator
            this.updatePerformanceIndicator();

            if (!response.ok) {
                this.performanceMetrics.errorCount++;
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            // Cache successful GET responses
            if (!config.method || config.method === 'GET') {
                this.cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
            }

            return data;
        } catch (error) {
            const duration = performance.now() - startTime;
            this.performanceMetrics.apiCalls.push({
                endpoint,
                duration,
                error: error.message,
                cached: false,
                timestamp: Date.now()
            });
            this.performanceMetrics.errorCount++;
            
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
            // Show skeleton loaders immediately
            this.showSkeletonLoaders();
            
            // Step 1: Load quick status first for immediate feedback
            try {
                const quickStatus = await this.apiGet('/status/quick');
                this.updateBasicStatus(quickStatus);
            } catch (error) {
                console.warn('Quick status failed, continuing with full load:', error);
            }
            
            // Step 2: Load data in parallel
            const [statusPromise, statsPromise, filesPromise] = [
                this.apiGet('/status').catch(error => ({ 
                    success: false, 
                    error: error.message,
                    fallback: true 
                })),
                this.apiGet('/stats?include_trends=true').catch(error => ({
                    success: false,
                    error: error.message,
                    stats: {},
                    trends: {},
                    fallback: true
                })),
                this.apiGet('/files/recent?limit=20&offset=0&sort=modified').catch(error => ({ 
                    success: false, 
                    error: error.message,
                    fallback: true 
                }))
            ];
            
            // Wait for all with timeout
            const timeoutPromise = new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Request timeout')), 10000)
            );
            
            const [status, stats, files] = await Promise.race([
                Promise.all([statusPromise, statsPromise, filesPromise]),
                timeoutPromise
            ]);

            // Handle status data
            if (status.success && !status.fallback) {
                this.updateStatusPanel(status);
                this.currentVaultPath = status.vault_path;
                this.aiOnline = status.ai_status;
            } else if (status.fallback) {
                console.error('Failed to load detailed status:', status.error);
                this.showLoadingError('status');
            }
            
            // Handle stats data with trends
            if (stats.success && !stats.fallback) {
                this.updateDashboardStats(stats.stats, stats.trends);
            } else if (stats.fallback) {
                console.error('Failed to load dashboard stats:', stats.error);
                this.showStatsError(stats.error);
            }

            // Handle files data - use recent files progressive loading
            if (files.success && !files.fallback) {
                this.updateRecentActivityProgressive(files);
            } else {
                // Try progressive loading as fallback
                console.warn('Using progressive loading for files');
                this.loadRecentActivityProgressive();
            }

            // Hide skeleton loaders
            this.hideSkeletonLoaders();

        } catch (error) {
            console.error('Failed to load dashboard:', error);
            this.hideSkeletonLoaders();
            this.showLoadingError('dashboard');
        }
    }
    
    updateBasicStatus(quickStatus) {
        if (!quickStatus.success) return;
        
        // Store status for later use
        this.currentVaultPath = quickStatus.vault_path;
        this.aiOnline = quickStatus.ai_status;
        
        // Update basic vault path immediately in status panel
        const vaultPathText = document.getElementById('vault-path-text') || document.getElementById('vault-path');
        if (vaultPathText) {
            vaultPathText.textContent = quickStatus.vault_path;
            // Color coding only if we have validation data
            if (quickStatus.vault_exists !== null) {
                vaultPathText.style.color = quickStatus.vault_exists ? '#10b981' : '#ef4444';
            }
        }
        
        // Update AI status immediately in status panel
        const aiStatusContent = document.getElementById('ai-status-content') || document.getElementById('ai-status');
        if (aiStatusContent) {
            if (quickStatus.ai_status) {
                aiStatusContent.innerHTML = `
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-animation"></span>
                    <span class="text-green-400">Online</span>
                `;
            } else {
                aiStatusContent.innerHTML = `
                    <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    <span class="text-red-400">Offline</span>
                `;
            }
        }
        
        // IMPORTANT: Also update dashboard vault info and AI status immediately
        const dashboardVaultPath = document.getElementById('dashboard-vault-path');
        if (dashboardVaultPath) {
            dashboardVaultPath.textContent = quickStatus.vault_path;
        }
        
        const dashboardAiStatus = document.getElementById('dashboard-ai-status');
        if (dashboardAiStatus) {
            if (quickStatus.ai_status) {
                dashboardAiStatus.innerHTML = `
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-animation"></span>
                    <span class="text-green-400">Online</span>
                `;
            } else {
                dashboardAiStatus.innerHTML = `
                    <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    <span class="text-red-400">Offline</span>
                `;
            }
        }
        
        // Show vault status warnings in Recent Activity if there are issues
        if (quickStatus.vault_exists === false) {
            const tbody = document.getElementById('recent-activity');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="py-8 text-center text-red-400">
                            <i class="fas fa-exclamation-triangle mr-2"></i> Vault path does not exist
                            <div class="text-sm mt-2 text-gray-400">Path: ${quickStatus.vault_path}</div>
                            <div class="text-sm mt-1 text-blue-400">
                                <i class="fas fa-info-circle mr-1"></i>
                                Please check the vault path in settings
                            </div>
                        </td>
                    </tr>
                `;
            }
        } else if (quickStatus.is_obsidian_vault === false) {
            const tbody = document.getElementById('recent-activity');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="py-8 text-center text-yellow-400">
                            <i class="fas fa-exclamation-triangle mr-2"></i> Not an Obsidian vault
                            <div class="text-sm mt-2 text-gray-400">Path: ${quickStatus.vault_path}</div>
                            <div class="text-sm mt-1 text-blue-400">
                                <i class="fas fa-info-circle mr-1"></i>
                                Directory exists but no .obsidian folder found
                            </div>
                        </td>
                    </tr>
                `;
            }
        }
    }
    
    updateRecentActivityProgressive(recentFiles) {
        const tbody = document.getElementById('recent-activity');
        
        if (!recentFiles || !recentFiles.files || recentFiles.files.length === 0) {
            // Show diagnostic information
            let diagnosticInfo = '';
            if (recentFiles && recentFiles.vault_info) {
                diagnosticInfo = `
                    <div class="text-sm mt-2 space-y-1">
                        <div><strong>Vault Path:</strong> ${recentFiles.vault_info.path}</div>
                        <div><strong>Is Obsidian Vault:</strong> ${recentFiles.vault_info.is_obsidian_vault ? 'Yes' : 'No'}</div>
                        <div><strong>Total Files Found:</strong> ${recentFiles.pagination ? recentFiles.pagination.total : 0}</div>
                    </div>
                `;
            }
            
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="py-8 text-center text-gray-400">
                        <i class="fas fa-folder-open mr-2"></i> No markdown files found in vault
                        ${diagnosticInfo}
                        <div class="text-sm mt-4 text-blue-400">
                            <i class="fas fa-info-circle mr-1"></i>
                            Check that the vault path points to a directory containing .md files
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        // Show recent files
        tbody.innerHTML = recentFiles.files.map(file => `
            <tr class="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                <td class="py-3 px-4 text-sm terminal-font text-blue-300" title="${file.full_path}">
                    ${file.name}
                    <div class="text-xs text-gray-500 mt-1">${file.path}</div>
                </td>
                <td class="py-3 px-4 text-sm">
                    <span class="bg-blue-900/50 text-blue-400 py-1 px-2 rounded-full text-xs">
                        <i class="fas fa-file-alt mr-1"></i>Indexed
                    </span>
                </td>
                <td class="py-3 px-4 text-sm">
                    <span class="text-gray-400">
                        <i class="fas fa-clock mr-1"></i>Not processed
                    </span>
                </td>
                <td class="py-3 px-4 text-sm text-gray-400">
                    ${this.formatDate(file.modified)}
                    <div class="text-xs text-gray-500 mt-1">${this.formatFileSize(file.size)}</div>
                </td>
            </tr>
        `).join('');

        // Add vault information footer with load more button
        if (recentFiles.files.length > 0 && recentFiles.vault_info) {
            const hasMore = recentFiles.pagination && recentFiles.pagination.has_more;
            const totalFiles = recentFiles.pagination ? recentFiles.pagination.total : recentFiles.files.length;
            
            const vaultNote = document.createElement('tr');
            vaultNote.innerHTML = `
                <td colspan="4" class="py-2 px-4 text-xs text-gray-500 border-t border-slate-700/30">
                    <div class="flex items-center justify-between">
                        <div>
                            <i class="fas fa-info-circle mr-1"></i>
                            Showing ${recentFiles.files.length} of ${totalFiles} files from vault
                        </div>
                        <div class="flex items-center space-x-4">
                            ${recentFiles.vault_info.is_obsidian_vault ? 
                                '<span class="text-green-400"><i class="fas fa-check mr-1"></i>Valid Obsidian Vault</span>' : 
                                '<span class="text-yellow-400"><i class="fas fa-exclamation-triangle mr-1"></i>Not an Obsidian Vault</span>'
                            }
                        </div>
                    </div>
                    ${hasMore ? `
                        <div class="mt-2 text-center">
                            <button onclick="app.loadMoreRecentFiles(${recentFiles.files.length})" 
                                    class="text-blue-400 hover:text-blue-300 text-sm transition-colors">
                                <i class="fas fa-chevron-down mr-2"></i>
                                Load ${Math.min(20, totalFiles - recentFiles.files.length)} more files
                            </button>
                        </div>
                    ` : ''}
                </td>
            `;
            tbody.appendChild(vaultNote);
        }
    }
    
    async loadRecentActivityProgressive() {
        try {
            const tbody = document.getElementById('recent-activity');
            
            // Show loading state
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="py-4 text-center text-gray-400">
                        <i class="fas fa-spinner fa-spin mr-2"></i> Loading files progressively...
                    </td>
                </tr>
            `;
            
            // Load first batch of recent files
            const recentFiles = await this.apiGet('/files/recent?limit=10&offset=0&sort=modified');
            
            if (recentFiles.success && recentFiles.files.length > 0) {
                this.updateRecentActivity(recentFiles);
                
                // If there are more files, show a "Load More" option
                if (recentFiles.pagination.has_more) {
                    const loadMoreRow = document.createElement('tr');
                    loadMoreRow.innerHTML = `
                        <td colspan="4" class="py-3 text-center">
                            <button onclick="app.loadMoreRecentFiles(10)" 
                                    class="text-blue-400 hover:text-blue-300 text-sm transition-colors">
                                <i class="fas fa-chevron-down mr-2"></i>
                                Load ${Math.min(10, recentFiles.pagination.total - 10)} more files
                            </button>
                        </td>
                    `;
                    tbody.appendChild(loadMoreRow);
                }
            } else {
                this.showLoadingError('files');
            }
        } catch (error) {
            console.error('Progressive loading failed:', error);
            this.showLoadingError('files');
        }
    }
    
    async loadMoreRecentFiles(offset) {
        try {
            const tbody = document.getElementById('recent-activity');
            const loadMoreRow = tbody.querySelector('tr:last-child');
            
            // Show loading in the load more button
            if (loadMoreRow) {
                loadMoreRow.innerHTML = `
                    <td colspan="4" class="py-3 text-center text-gray-400">
                        <i class="fas fa-spinner fa-spin mr-2"></i> Loading more files...
                    </td>
                `;
            }
            
            const moreFiles = await this.apiGet(`/files/recent?limit=10&offset=${offset}&sort=modified`);
            
            if (moreFiles.success && moreFiles.files.length > 0) {
                // Remove loading row
                if (loadMoreRow) {
                    loadMoreRow.remove();
                }
                
                // Add new files
                moreFiles.files.forEach(file => {
                    const row = document.createElement('tr');
                    row.className = 'border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors';
                    row.innerHTML = `
                        <td class="py-3 px-4 text-sm terminal-font text-blue-300" title="${file.full_path}">
                            ${file.name}
                            <div class="text-xs text-gray-500 mt-1">${file.path}</div>
                        </td>
                        <td class="py-3 px-4 text-sm">
                            <span class="bg-blue-900/50 text-blue-400 py-1 px-2 rounded-full text-xs">
                                <i class="fas fa-file-alt mr-1"></i>Indexed
                            </span>
                        </td>
                        <td class="py-3 px-4 text-sm">
                            <span class="text-gray-400">
                                <i class="fas fa-clock mr-1"></i>Not processed
                            </span>
                        </td>
                        <td class="py-3 px-4 text-sm text-gray-400">
                            ${this.formatDate(file.modified)}
                            <div class="text-xs text-gray-500 mt-1">${this.formatFileSize(file.size)}</div>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                
                // Add new load more button if there are more files
                if (moreFiles.pagination.has_more) {
                    const newLoadMoreRow = document.createElement('tr');
                    newLoadMoreRow.innerHTML = `
                        <td colspan="4" class="py-3 text-center">
                            <button onclick="app.loadMoreRecentFiles(${offset + 10})" 
                                    class="text-blue-400 hover:text-blue-300 text-sm transition-colors">
                                <i class="fas fa-chevron-down mr-2"></i>
                                Load ${Math.min(10, moreFiles.pagination.total - offset - 10)} more files
                            </button>
                        </td>
                    `;
                    tbody.appendChild(newLoadMoreRow);
                }
            } else {
                // No more files, remove the load more row
                if (loadMoreRow) {
                    loadMoreRow.remove();
                }
            }
        } catch (error) {
            console.error('Failed to load more files:', error);
            this.showNotification('error', 'Load Error', 'Failed to load more files');
        }
    }

    addPerformanceIndicator() {
        // Performance indicator is now part of the HTML template
        // Just ensure it's visible and initialize it
        const indicator = document.getElementById('performance-indicator');
        if (indicator) {
            indicator.innerHTML = `
                <span class="text-green-400">●</span> Initializing...
            `;
        }
    }
    
    updatePerformanceIndicator() {
        const indicator = document.getElementById('performance-indicator');
        if (!indicator) return;
        
        const recentCalls = this.performanceMetrics.apiCalls.slice(-10);
        const avgResponseTime = recentCalls.length > 0 
            ? recentCalls.reduce((sum, call) => sum + call.duration, 0) / recentCalls.length 
            : 0;
        
        const cacheHitRate = recentCalls.length > 0
            ? (recentCalls.filter(call => call.cached).length / recentCalls.length) * 100
            : 0;
        
        let status, color;
        if (avgResponseTime < 200) {
            status = 'Excellent';
            color = 'text-green-400';
        } else if (avgResponseTime < 500) {
            status = 'Good';
            color = 'text-blue-400';
        } else if (avgResponseTime < 1000) {
            status = 'Fair';
            color = 'text-yellow-400';
        } else {
            status = 'Slow';
            color = 'text-red-400';
        }
        
        indicator.innerHTML = `
            <span class="${color}">●</span> ${status}
            <span class="text-gray-500 ml-1" title="Avg: ${Math.round(avgResponseTime)}ms, Cache: ${Math.round(cacheHitRate)}%">
                ${Math.round(avgResponseTime)}ms
            </span>
        `;
    }
    
    getPerformanceReport() {
        const metrics = this.performanceMetrics;
        const recentCalls = metrics.apiCalls.slice(-50);
        
        return {
            totalApiCalls: metrics.apiCalls.length,
            averageResponseTime: recentCalls.length > 0 
                ? recentCalls.reduce((sum, call) => sum + call.duration, 0) / recentCalls.length 
                : 0,
            cacheHitRate: recentCalls.length > 0
                ? (recentCalls.filter(call => call.cached).length / recentCalls.length) * 100
                : 0,
            errorRate: metrics.errorCount / Math.max(metrics.apiCalls.length, 1) * 100,
            initializationTime: metrics.loadTimes.initialization || 0,
            slowestEndpoint: recentCalls.reduce((slowest, call) => 
                !call.cached && call.duration > (slowest?.duration || 0) ? call : slowest
            , null)
        };
    }
    
    showSkeletonLoaders() {
        // Status panel skeletons
        const statusElements = [
            'vault-path-skeleton',
            'ai-status-skeleton', 
            'total-files-skeleton',
            'tagged-files-skeleton',
            'unique-tags-skeleton'
        ];
        
        statusElements.forEach(id => {
            const skeleton = document.getElementById(id);
            const textElement = document.getElementById(id.replace('-skeleton', '-text') || id.replace('-skeleton', ''));
            if (skeleton && textElement) {
                skeleton.classList.remove('hidden');
                textElement.classList.add('hidden');
            }
        });

        // Dashboard stats skeletons
        const dashboardSkeletons = [
            'dashboard-total-files-skeleton',
            'dashboard-tagged-files-skeleton', 
            'dashboard-unique-tags-skeleton'
        ];
        
        dashboardSkeletons.forEach(id => {
            const skeleton = document.getElementById(id);
            const textElement = document.getElementById(id.replace('-skeleton', ''));
            if (skeleton && textElement) {
                skeleton.classList.remove('hidden');
                textElement.classList.add('hidden');
            }
        });

        // Recent Activity skeleton
        const loadingRow = document.getElementById('recent-activity-loading');
        const skeletonRows = document.querySelectorAll('.skeleton-row');
        if (loadingRow) loadingRow.classList.add('hidden');
        skeletonRows.forEach(row => row.classList.remove('hidden'));
    }

    hideSkeletonLoaders() {
        // Status panel skeletons
        const statusElements = [
            'vault-path-skeleton',
            'ai-status-skeleton',
            'total-files-skeleton', 
            'tagged-files-skeleton',
            'unique-tags-skeleton'
        ];
        
        statusElements.forEach(id => {
            const skeleton = document.getElementById(id);
            const textElement = document.getElementById(id.replace('-skeleton', '-text') || id.replace('-skeleton', ''));
            if (skeleton && textElement) {
                skeleton.classList.add('hidden');
                textElement.classList.remove('hidden');
            }
        });

        // Dashboard stats skeletons
        const dashboardSkeletons = [
            'dashboard-total-files-skeleton',
            'dashboard-tagged-files-skeleton',
            'dashboard-unique-tags-skeleton'
        ];
        
        dashboardSkeletons.forEach(id => {
            const skeleton = document.getElementById(id);
            const textElement = document.getElementById(id.replace('-skeleton', ''));
            if (skeleton && textElement) {
                skeleton.classList.add('hidden');
                textElement.classList.remove('hidden');
            }
        });

        // Recent Activity skeleton
        const skeletonRows = document.querySelectorAll('.skeleton-row');
        skeletonRows.forEach(row => row.classList.add('hidden'));
    }

    showLoadingError(component) {
        switch(component) {
            case 'status':
                this.showNotification('error', 'Loading Error', 'Failed to load vault status');
                break;
            case 'files':
                document.getElementById('recent-activity').innerHTML = `
                    <tr><td colspan="4" class="py-8 text-center text-red-400">
                        <i class="fas fa-exclamation-triangle mr-2"></i> Failed to load recent activity
                    </td></tr>
                `;
                break;
            case 'dashboard':
                this.showNotification('error', 'Dashboard Error', 'Failed to load dashboard data');
                break;
        }
    }

    showStatsError(error) {
        // Show error state in stats cards instead of "-"
        const statsElements = [
            'dashboard-total-files',
            'dashboard-tagged-files', 
            'dashboard-unique-tags'
        ];
        
        statsElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = `
                    <span class="text-red-400 text-sm">
                        <i class="fas fa-exclamation-triangle mr-1"></i>
                        Error
                    </span>
                `;
            }
        });
        
        // Show error notification
        this.showNotification('error', 'Stats Error', 
            'Failed to load vault statistics: ' + (error || 'Unknown error'));
    }

    updateStatusPanel(status) {
        // Update vault path
        const vaultPathText = document.getElementById('vault-path-text') || document.getElementById('vault-path');
        if (vaultPathText) {
            vaultPathText.textContent = status.vault_path;
        }
        
        // Update AI status
        const aiStatusContent = document.getElementById('ai-status-content') || document.getElementById('ai-status');
        if (aiStatusContent) {
            if (status.ai_status) {
                aiStatusContent.innerHTML = `
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-animation"></span>
                    <span class="text-green-400">Online</span>
                `;
            } else {
                aiStatusContent.innerHTML = `
                    <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    <span class="text-red-400">Offline</span>
                `;
            }
        }

        if (status.stats) {
            // Update sidebar stats
            const totalFilesText = document.getElementById('total-files-text') || document.getElementById('total-files');
            const taggedFilesText = document.getElementById('tagged-files-text') || document.getElementById('tagged-files');
            const uniqueTagsText = document.getElementById('unique-tags-text') || document.getElementById('unique-tags');
            
            if (totalFilesText) totalFilesText.textContent = status.stats.total_files || '-';
            if (taggedFilesText) taggedFilesText.textContent = status.stats.tagged_files || '-';
            if (uniqueTagsText) uniqueTagsText.textContent = status.stats.total_tags || '-';
        }
    }

    updateDashboardStats(stats, trends) {
        if (!stats) return;

        const totalFilesEl = document.getElementById('dashboard-total-files');
        const taggedFilesEl = document.getElementById('dashboard-tagged-files');
        const uniqueTagsEl = document.getElementById('dashboard-unique-tags');
        
        if (totalFilesEl) totalFilesEl.textContent = stats.total_files || '-';
        if (taggedFilesEl) taggedFilesEl.textContent = stats.tagged_files || '-';
        if (uniqueTagsEl) uniqueTagsEl.textContent = stats.total_tags || '-';

        // Update vault path and AI status in dashboard if elements exist
        const dashboardVaultPath = document.getElementById('dashboard-vault-path');
        if (dashboardVaultPath) {
            dashboardVaultPath.textContent = this.currentVaultPath || 'Unknown';
        }
        
        const dashboardAiStatus = document.getElementById('dashboard-ai-status');
        if (dashboardAiStatus) {
            if (this.aiOnline) {
                dashboardAiStatus.innerHTML = `
                    <span class="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-animation"></span>
                    <span class="text-green-400">Online</span>
                `;
            } else {
                dashboardAiStatus.innerHTML = `
                    <span class="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    <span class="text-red-400">Offline</span>
                `;
            }
        }

        // Update trends with proper indicators
        this.updateTrend('total-files-trend', trends?.total_files);
        this.updateTrend('tagged-files-trend', trends?.tagged_files);
        this.updateTrend('unique-tags-trend', trends?.total_tags);
    }
    
    updateTrend(elementId, trend) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        if (!trend || trend.direction === undefined) {
            element.innerHTML = '<i class="fas fa-minus mr-1 text-gray-400"></i> <span class="text-gray-400">No data</span>';
            return;
        }

        const { direction, value } = trend;
        let icon, color, text;
        
        if (direction === 'up') {
            icon = 'fas fa-arrow-up';
            color = 'text-green-400';
            text = `${value}% from last scan`;
        } else if (direction === 'down') {
            icon = 'fas fa-arrow-down';
            color = 'text-red-400';
            text = `${Math.abs(value)}% from last scan`;
        } else {
            icon = 'fas fa-minus';
            color = 'text-yellow-400';
            text = 'No change from last scan';
        }
        
        element.innerHTML = `<i class="${icon} mr-1 ${color}"></i> <span class="${color}">${text}</span>`;
    }

    updateRecentActivity(files) {
        const tbody = document.getElementById('recent-activity');
        
        if (!files || !files.files || files.files.length === 0) {
            // Provide detailed diagnostic information
            let diagnosticInfo = '';
            if (files && files.vault_path) {
                diagnosticInfo = `
                    <div class="text-sm mt-2 space-y-1">
                        <div><strong>Vault Path:</strong> ${files.vault_path}</div>
                        <div><strong>Is Obsidian Vault:</strong> ${files.is_obsidian_vault ? 'Yes' : 'No'}</div>
                        <div><strong>Total Files Found:</strong> ${files.total_files || 0}</div>
                        ${files.scan_summary ? `<div><strong>Directories Scanned:</strong> ${files.scan_summary.total_directories}</div>` : ''}
                    </div>
                `;
            }
            
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="py-8 text-center text-gray-400">
                        <i class="fas fa-folder-open mr-2"></i> No markdown files found in vault
                        ${diagnosticInfo}
                        <div class="text-sm mt-4 text-blue-400">
                            <i class="fas fa-info-circle mr-1"></i>
                            Check that the vault path points to a directory containing .md files
                        </div>
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
            <tr class="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                <td class="py-3 px-4 text-sm terminal-font text-blue-300" title="${file.full_path}">
                    ${file.name}
                    <div class="text-xs text-gray-500 mt-1">${file.path}</div>
                </td>
                <td class="py-3 px-4 text-sm">
                    <span class="bg-blue-900/50 text-blue-400 py-1 px-2 rounded-full text-xs">
                        <i class="fas fa-file-alt mr-1"></i>Indexed
                    </span>
                </td>
                <td class="py-3 px-4 text-sm">
                    <span class="text-gray-400">
                        <i class="fas fa-clock mr-1"></i>Not processed
                    </span>
                </td>
                <td class="py-3 px-4 text-sm text-gray-400">
                    ${this.formatDate(file.modified)}
                    <div class="text-xs text-gray-500 mt-1">${this.formatFileSize(file.size)}</div>
                </td>
            </tr>
        `).join('');

        // Add vault information footer
        if (recentFiles.length > 0 && files.vault_path) {
            const vaultNote = document.createElement('tr');
            vaultNote.innerHTML = `
                <td colspan="4" class="py-2 px-4 text-xs text-gray-500 border-t border-slate-700/30">
                    <div class="flex items-center justify-between">
                        <div>
                            <i class="fas fa-info-circle mr-1"></i>
                            Showing ${recentFiles.length} of ${files.total_files || 0} files from vault
                        </div>
                        <div class="flex items-center space-x-4">
                            ${files.is_obsidian_vault ? 
                                '<span class="text-green-400"><i class="fas fa-check mr-1"></i>Valid Obsidian Vault</span>' : 
                                '<span class="text-yellow-400"><i class="fas fa-exclamation-triangle mr-1"></i>Not an Obsidian Vault</span>'
                            }
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(vaultNote);
        }
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
                    <!-- Vault Configuration Section -->
                    <div class="bg-slate-800/30 rounded-lg p-6">
                        <h3 class="text-lg font-semibold mb-4 text-blue-400">Vault Configuration</h3>
                    
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-2">Current Vault Path</label>
                                <div class="bg-slate-700 rounded-lg p-3 mb-3 flex justify-between items-center">
                                    <span id="current-vault-path" class="text-sm font-mono text-green-400 break-all">Loading...</span>
                                    <button id="copy-vault-path" class="ml-2 text-blue-400 hover:text-blue-300" title="Copy to clipboard">
                                        <i class="far fa-copy"></i>
                                    </button>
                                </div>
                                <div class="text-xs text-gray-400 mb-3">
                                    <i class="fas fa-info-circle mr-1"></i>
                                    The vault path is where your Obsidian notes are stored.
                                    To change it, restart the application with the --vault-path argument.
                                </div>
                                <div class="bg-blue-900/20 border border-blue-700/30 rounded-lg p-3 mb-3">
                                    <div class="text-sm text-blue-300 font-medium mb-1">How to change vault path:</div>
                                    <div class="text-xs text-blue-200 font-mono">
                                        python tag_automator_cli.py --web --vault-path "/path/to/your/vault"
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                
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
            const [status, config, prompt] = await Promise.all([
                this.apiGet('/status'),
                this.apiGet('/config'),
                this.apiGet('/ai-prompt')
            ]);

            // Load vault path
            const vaultPathElement = document.getElementById('current-vault-path');
            if (vaultPathElement) {
                // Set the vault path text
                vaultPathElement.textContent = status.vault_path || 'Not set';
                
                // Set up the copy button that was already added in the HTML
                const copyButton = document.getElementById('copy-vault-path');
                if (copyButton) {
                    copyButton.onclick = () => {
                        navigator.clipboard.writeText(status.vault_path || '');
                        this.showNotification('success', 'Copied!', 'Vault path copied to clipboard');
                    };
                }
                
                // Also update the vault path in the dashboard if it exists
                const dashboardVaultPath = document.getElementById('dashboard-vault-path');
                if (dashboardVaultPath) {
                    dashboardVaultPath.textContent = status.vault_path || 'Not set';
                }
            }

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
        // Clear relevant cache entries
        const keysToDelete = [];
        for (const [key] of this.cache) {
            if (key.includes('/status') || key.includes('/stats') || key.includes('/files') || key.includes('/tags')) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => this.cache.delete(key));
        
        // Show loading state
        this.showNotification('info', 'Refreshing', 'Updating dashboard data...');
        
        // Reload dashboard
        this.loadDashboard().then(() => {
            this.showNotification('success', 'Refreshed', 'Dashboard data updated successfully');
        }).catch((error) => {
            console.error('Failed to refresh dashboard:', error);
            this.showNotification('error', 'Refresh Failed', 'Failed to update dashboard data');
        });
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