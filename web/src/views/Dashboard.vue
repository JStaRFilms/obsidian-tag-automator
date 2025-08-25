<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">Dashboard</h1>
      <p class="text-secondary-300">Overview of your Obsidian vault statistics and recent activity</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-96">
      <div class="text-center">
        <div class="loading-spinner mb-4"></div>
        <p class="text-secondary-300">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-error-900/20 border border-error-700 rounded-xl p-6">
      <div class="flex items-center space-x-3">
        <svg class="w-6 h-6 text-error-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
        <div>
          <h3 class="text-error-400 font-semibold">Connection Error</h3>
          <p class="text-secondary-300 text-sm">{{ error }}</p>
        </div>
      </div>
      <button @click="loadDashboard" class="mt-4 btn btn-secondary">
        Try Again
      </button>
    </div>

    <!-- Main Content -->
    <div v-else>
      <!-- Vault Information Card -->
      <div class="glass-card mb-8">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 class="text-xl font-semibold text-white mb-2">Vault Information</h2>
            <div class="flex flex-col sm:flex-row sm:items-center gap-4">
              <div class="flex items-center space-x-2">
                <svg class="w-4 h-4 text-secondary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                </svg>
                <span class="text-secondary-300">{{ vaultInfo.path || 'Not connected' }}</span>
              </div>
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 rounded-full" :class="vaultInfo.aiStatus ? 'bg-success-500' : 'bg-error-500'"></div>
                <span class="text-sm text-secondary-300">
                  AI: {{ vaultInfo.aiStatus ? 'Online' : 'Offline' }}
                </span>
              </div>
            </div>
          </div>
          <button @click="loadDashboard" class="btn btn-primary">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh Data
          </button>
        </div>
      </div>

      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="glass-card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-secondary-400 text-sm font-medium">Total Files</p>
              <p class="text-3xl font-bold text-white mt-1">{{ stats.totalFiles || 0 }}</p>
              <div v-if="stats.fileTrend" class="flex items-center mt-2">
                <svg v-if="stats.fileTrend > 0" class="w-4 h-4 text-success-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <svg v-else class="w-4 h-4 text-error-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path>
                </svg>
                <span class="text-xs" :class="stats.fileTrend > 0 ? 'text-success-400' : 'text-error-400'">
                  {{ Math.abs(stats.fileTrend) }}% from last scan
                </span>
              </div>
            </div>
            <div class="bg-primary-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="glass-card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-secondary-400 text-sm font-medium">Tagged Files</p>
              <p class="text-3xl font-bold text-white mt-1">{{ stats.taggedFiles || 0 }}</p>
              <div v-if="stats.taggedTrend" class="flex items-center mt-2">
                <svg v-if="stats.taggedTrend > 0" class="w-4 h-4 text-success-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <svg v-else class="w-4 h-4 text-error-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path>
                </svg>
                <span class="text-xs" :class="stats.taggedTrend > 0 ? 'text-success-400' : 'text-error-400'">
                  {{ Math.abs(stats.taggedTrend) }}% from last scan
                </span>
              </div>
            </div>
            <div class="bg-success-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="glass-card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-secondary-400 text-sm font-medium">Unique Tags</p>
              <p class="text-3xl font-bold text-white mt-1">{{ stats.uniqueTags || 0 }}</p>
              <div v-if="stats.tagTrend" class="flex items-center mt-2">
                <svg v-if="stats.tagTrend > 0" class="w-4 h-4 text-success-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
                <svg v-else class="w-4 h-4 text-error-400 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path>
                </svg>
                <span class="text-xs" :class="stats.tagTrend > 0 ? 'text-success-400' : 'text-error-400'">
                  {{ Math.abs(stats.tagTrend) }}% from last scan
                </span>
              </div>
            </div>
            <div class="bg-warning-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-warning-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="glass-card">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-semibold text-white">Recent Activity</h2>
          <button @click="loadRecentActivity" class="btn btn-ghost">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Refresh
          </button>
        </div>

        <div v-if="recentActivity.length === 0" class="text-center py-8">
          <svg class="w-12 h-12 text-secondary-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          <p class="text-secondary-400">No recent activity</p>
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="activity in recentActivity"
            :key="activity.id"
            class="flex items-center space-x-4 p-3 rounded-lg bg-secondary-800/30 hover:bg-secondary-700/30 transition-colors"
          >
            <div class="flex-shrink-0">
              <div class="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center">
                <svg v-if="activity.type === 'tagged'" class="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                </svg>
                <svg v-else-if="activity.type === 'alias'" class="w-4 h-4 text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"></path>
                </svg>
                <svg v-else class="w-4 h-4 text-warning-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-white font-medium truncate">{{ activity.title }}</p>
              <p class="text-secondary-400 text-sm">{{ activity.description }}</p>
            </div>
            <div class="text-right">
              <p class="text-secondary-400 text-sm">{{ activity.time }}</p>
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
