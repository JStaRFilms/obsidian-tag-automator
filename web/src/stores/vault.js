import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useVaultStore = defineStore('vault', () => {
  // State
  const vaultInfo = ref({
    path: '',
    aiStatus: false,
    connected: false
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
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isConnected = computed(() => vaultInfo.value.connected)
  const hasError = computed(() => !!error.value)
  const isLoading = computed(() => loading.value)

  // Actions
  const loadVaultStatus = async () => {
    try {
      const response = await axios.get('/api/status')
      vaultInfo.value = {
        path: response.data.vault_path || '',
        aiStatus: response.data.ai_status || false,
        connected: response.data.connected || false
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load vault status'
      vaultInfo.value.connected = false
      throw err
    }
  }

  const loadStats = async (includeTrends = true) => {
    try {
      const response = await axios.get(`/api/stats?include_trends=${includeTrends}`)
      if (response.data.success) {
        stats.value = {
          totalFiles: response.data.stats.total_files || 0,
          taggedFiles: response.data.stats.tagged_files || 0,
          uniqueTags: response.data.stats.total_tags || 0,
          fileTrend: response.data.trends?.total_files?.value || 0,
          taggedTrend: response.data.trends?.tagged_files?.value || 0,
          tagTrend: response.data.trends?.total_tags?.value || 0
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load statistics'
      throw err
    }
  }

  const loadRecentActivity = async (limit = 10) => {
    try {
      const response = await axios.get(`/api/files/recent?limit=${limit}&sort=modified`)
      if (response.data.success && response.data.files) {
        recentActivity.value = response.data.files.map((file, index) => ({
          id: index,
          title: file.name,
          description: `Modified ${formatTimeAgo(file.modified)}`,
          time: formatTimeAgo(file.modified),
          type: 'modified',
          file: file
        }))
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load recent activity'
      throw err
    }
  }

  const loadAllData = async () => {
    loading.value = true
    error.value = null

    try {
      await Promise.all([
        loadVaultStatus(),
        loadStats(),
        loadRecentActivity()
      ])
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      loading.value = false
    }
  }

  // Helper function
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

  return {
    // State
    vaultInfo,
    stats,
    recentActivity,
    loading,
    error,

    // Getters
    isConnected,
    hasError,
    isLoading,

    // Actions
    loadVaultStatus,
    loadStats,
    loadRecentActivity,
    loadAllData
  }
})
