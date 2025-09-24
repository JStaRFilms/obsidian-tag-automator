import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAliasesStore = defineStore('aliases', () => {
  // State
  const aliases = ref([])
  const suggestedAliases = ref([])
  const loading = ref(false)
  const error = ref(null)
  const aiSuggestionsLoading = ref(false)

  // Getters
  const totalAliases = computed(() => aliases.value.length)
  const activeAliases = computed(() =>
    aliases.value.filter(alias => alias.is_active !== false)
  )
  const aliasConflicts = computed(() => {
    const conflicts = []
    const aliasMap = new Map()

    aliases.value.forEach(alias => {
      if (aliasMap.has(alias.alias)) {
        conflicts.push({
          alias: alias.alias,
          conflicting: [aliasMap.get(alias.alias), alias]
        })
      } else {
        aliasMap.set(alias.alias, alias)
      }
    })

    return conflicts
  })

  // Actions
  const loadAliases = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get('/api/aliases')
      if (response.data.success) {
        aliases.value = response.data.aliases || []
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load aliases'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createAlias = async (aliasData) => {
    try {
      const response = await axios.post('/api/aliases', aliasData)
      if (response.data.success) {
        aliases.value.push(response.data.alias)
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create alias'
      throw err
    }
  }

  const updateAlias = async (aliasId, updates) => {
    try {
      const response = await axios.put(`/api/aliases/${aliasId}`, updates)
      if (response.data.success) {
        const index = aliases.value.findIndex(a => a.id === aliasId)
        if (index > -1) {
          aliases.value[index] = { ...aliases.value[index], ...updates }
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update alias'
      throw err
    }
  }

  const deleteAlias = async (aliasId) => {
    try {
      const response = await axios.delete(`/api/aliases/${aliasId}`)
      if (response.data.success) {
        const index = aliases.value.findIndex(a => a.id === aliasId)
        if (index > -1) {
          aliases.value.splice(index, 1)
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete alias'
      throw err
    }
  }

  const bulkCreateAliases = async (aliasList) => {
    try {
      const response = await axios.post('/api/aliases/bulk', { aliases: aliasList })
      if (response.data.success) {
        await loadAliases() // Refresh the list
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create aliases'
      throw err
    }
  }

  const getAISuggestions = async (options = {}) => {
    aiSuggestionsLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (options.limit) params.append('limit', options.limit)
      if (options.min_confidence) params.append('min_confidence', options.min_confidence)

      const response = await axios.get(`/api/aliases/suggestions?${params}`)
      if (response.data.success) {
        suggestedAliases.value = response.data.suggestions || []
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to get AI suggestions'
      throw err
    } finally {
      aiSuggestionsLoading.value = false
    }
  }

  const applyAISuggestion = async (suggestion) => {
    try {
      const response = await axios.post('/api/aliases/apply-suggestion', suggestion)
      if (response.data.success) {
        // Remove from suggestions
        const index = suggestedAliases.value.findIndex(s => s.id === suggestion.id)
        if (index > -1) {
          suggestedAliases.value.splice(index, 1)
        }

        // Add to aliases if created
        if (response.data.alias) {
          aliases.value.push(response.data.alias)
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to apply AI suggestion'
      throw err
    }
  }

  const rejectAISuggestion = async (suggestionId) => {
    try {
      const response = await axios.post('/api/aliases/reject-suggestion', {
        suggestion_id: suggestionId
      })
      if (response.data.success) {
        // Remove from suggestions
        const index = suggestedAliases.value.findIndex(s => s.id === suggestionId)
        if (index > -1) {
          suggestedAliases.value.splice(index, 1)
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to reject AI suggestion'
      throw err
    }
  }

  const resolveConflict = async (alias, resolution) => {
    try {
      const response = await axios.post('/api/aliases/resolve-conflict', {
        alias: alias,
        resolution: resolution // 'keep_first', 'keep_second', 'merge', 'create_new'
      })
      if (response.data.success) {
        await loadAliases() // Refresh the list
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to resolve conflict'
      throw err
    }
  }

  const applyAliasToFiles = async (aliasId, filePaths) => {
    try {
      const response = await axios.post(`/api/aliases/${aliasId}/apply`, {
        files: filePaths
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to apply alias to files'
      throw err
    }
  }

  const getAliasUsage = async (aliasId) => {
    try {
      const response = await axios.get(`/api/aliases/${aliasId}/usage`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to get alias usage'
      throw err
    }
  }

  const validateAliases = async () => {
    try {
      const response = await axios.get('/api/aliases/validate')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to validate aliases'
      throw err
    }
  }

  const clearSuggestions = () => {
    suggestedAliases.value = []
  }

  return {
    // State
    aliases,
    suggestedAliases,
    loading,
    error,
    aiSuggestionsLoading,

    // Getters
    totalAliases,
    activeAliases,
    aliasConflicts,

    // Actions
    loadAliases,
    createAlias,
    updateAlias,
    deleteAlias,
    bulkCreateAliases,
    getAISuggestions,
    applyAISuggestion,
    rejectAISuggestion,
    resolveConflict,
    applyAliasToFiles,
    getAliasUsage,
    validateAliases,
    clearSuggestions
  }
})
