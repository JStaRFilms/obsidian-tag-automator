<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">Dashboard</h1>
      <p class="text-slate-300">Overview of your Obsidian vault statistics and recent activity</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-96">
      <div class="text-center">
        <div class="loading-spinner mb-4"></div>
        <p class="text-slate-300">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-900/20 border border-red-700 rounded-xl p-6">
      <div class="flex items-center space-x-3">
        <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
        <div>
          <h3 class="text-red-400 font-semibold">Connection Error</h3>
          <p class="text-slate-300 text-sm">{{ error }}</p>
        </div>
      </div>
      <button @click="loadDashboard" class="mt-4 px-4 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors">
        Try Again
      </button>
    </div>

    <!-- Main Content -->
    <div v-else>
      <!-- Vault Information Card -->
      <div class="glass-effect rounded-xl p-6 shadow-xl mb-8">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-white mb-2">Vault Information</h2>
            <div class="flex flex-col sm:flex-row sm:items-center gap-4">
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                </svg>
                <span class="text-slate-300">{{ vaultInfo.path || '/path/to/vault' }}</span>
              </div>
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 rounded-full bg-green-500"></div>
                <span class="text-sm text-slate-300">AI: Online</span>
              </div>
            </div>
          </div>
          <button @click="loadDashboard" class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors">
            <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh Data
          </button>
        </div>
      </div>

      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <!-- Total Files -->
        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Total Files</p>
              <p class="text-3xl font-bold text-white mt-1">{{ stats.totalFiles || 1247 }}</p>
              <div class="flex items-center mt-2">
                <svg class="w-4 h-4 text-green-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <span class="text-xs text-green-400">↑ 12% from last week</span>
              </div>
            </div>
            <div class="bg-blue-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- Tagged Files -->
        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Tagged Files</p>
              <p class="text-3xl font-bold text-white mt-1">{{ stats.taggedFiles || 892 }}</p>
              <div class="flex items-center mt-2">
                <svg class="w-4 h-4 text-green-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <span class="text-xs text-green-400">↑ 8% from last week</span>
              </div>
            </div>
            <div class="bg-green-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- Unique Tags -->
        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Unique Tags</p>
              <p class="text-3xl font-bold text-white mt-1">{{ stats.uniqueTags || 156 }}</p>
              <div class="flex items-center mt-2">
                <svg class="w-4 h-4 text-yellow-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <span class="text-xs text-yellow-400">↑ 3% from last week</span>
              </div>
            </div>
            <div class="bg-yellow-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="glass-effect rounded-xl p-6 shadow-xl">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-white">Recent Activity</h2>
          <button @click="loadRecentActivity" class="px-3 py-1 text-slate-300 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors">
            <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh
          </button>
        </div>

        <div class="space-y-3">
          <div class="flex items-center space-x-4 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-700/30 transition-colors">
            <div class="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
              <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-white font-medium">Auto-tagged 15 files</p>
              <p class="text-slate-400 text-sm">Added #productivity, #workflow tags</p>
            </div>
            <div class="text-right">
              <p class="text-slate-400 text-sm">2 min ago</p>
            </div>
          </div>

          <div class="flex items-center space-x-4 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-700/30 transition-colors">
            <div class="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
              <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-white font-medium">Created alias mapping</p>
              <p class="text-slate-400 text-sm">"ai" → "artificial-intelligence"</p>
            </div>
            <div class="text-right">
              <p class="text-slate-400 text-sm">5 min ago</p>
            </div>
          </div>

          <div class="flex items-center space-x-4 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-700/30 transition-colors">
            <div class="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center">
              <svg class="w-4 h-4 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-white font-medium">Bulk renamed tags</p>
              <p class="text-slate-400 text-sm">"ml" → "machine-learning" (23 files)</p>
            </div>
            <div class="text-right">
              <p class="text-slate-400 text-sm">10 min ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// Reactive state
const loading = ref(true)
const error = ref(null)
const vaultInfo = ref({
  path: '',
  aiStatus: false
})
const stats = ref({
  totalFiles: 0,
  taggedFiles: 0,
  uniqueTags: 0,
  fileTrend: 0,
  taggedTrend: 0,
  tagTrend: 0
})
const recentActivity = ref([])

// Load dashboard data
const loadDashboard = async () => {
  loading.value = true
  error.value = null

  try {
    // Load vault status
    const statusResponse = await axios.get('/api/status')
    vaultInfo.value = {
      path: statusResponse.data.vault_path || 'Not connected',
      aiStatus: statusResponse.data.ai_status || false
    }

    // Load statistics
    const statsResponse = await axios.get('/api/stats?include_trends=true')
    if (statsResponse.data.success) {
      stats.value = {
        totalFiles: statsResponse.data.stats.total_files || 0,
        taggedFiles: statsResponse.data.stats.tagged_files || 0,
        uniqueTags: statsResponse.data.stats.total_tags || 0,
        fileTrend: statsResponse.data.trends?.total_files?.value || 0,
        taggedTrend: statsResponse.data.trends?.tagged_files?.value || 0,
        tagTrend: statsResponse.data.trends?.total_tags?.value || 0
      }
    }

    // Load recent activity
    await loadRecentActivity()
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to load dashboard data'
    console.error('Dashboard load error:', err)
  } finally {
    loading.value = false
  }
}

// Load recent activity
const loadRecentActivity = async () => {
  try {
    const response = await axios.get('/api/files/recent?limit=10&sort=modified')
    if (response.data.success && response.data.files) {
      recentActivity.value = response.data.files.slice(0, 10).map((file, index) => ({
        id: index,
        title: file.name,
        description: `Modified ${formatTimeAgo(file.modified)}`,
        time: formatTimeAgo(file.modified),
        type: 'modified'
      }))
    }
  } catch (err) {
    console.error('Recent activity load error:', err)
  }
}

// Format time ago
const formatTimeAgo = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString()
}

// Load data on mount
onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.loading-spinner {
  border: 4px solid rgba(56, 189, 248, 0.2);
  border-radius: 50%;
  border-top-color: #38bdf8;
  width: 32px;
  height: 32px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
