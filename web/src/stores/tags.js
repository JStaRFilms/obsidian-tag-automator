import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useTagsStore = defineStore('tags', () => {
  // State
  const tags = ref([])
  const tagStats = ref({})
  const loading = ref(false)
  const error = ref(null)
  const operationHistory = ref([])

  // Getters
  const totalTags = computed(() => tags.value.length)
  const orphanedTags = computed(() =>
    tags.value.filter(tag => tagStats.value[tag.name]?.file_count === 0)
  )
  const duplicateTags = computed(() => {
    const duplicates = []
    const tagMap = new Map()

    tags.value.forEach(tag => {
      const normalized = tag.name.toLowerCase()
      if (tagMap.has(normalized)) {
        duplicates.push({ original: tagMap.get(normalized), duplicate: tag })
      } else {
        tagMap.set(normalized, tag)
      }
    })

    return duplicates
  })

  const malformedTags = computed(() =>
    tags.value.filter(tag =>
      tag.name.includes(' ') ||
      tag.name.includes('#') ||
      /[^a-zA-Z0-9\-_]/.test(tag.name)
    )
  )

  // Actions
  const loadTags = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get('/api/tags')
      if (response.data.success) {
        tags.value = response.data.tags || []
        tagStats.value = response.data.stats || {}
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load tags'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createTag = async (tagData) => {
    try {
      const response = await axios.post('/api/tags', tagData)
      if (response.data.success) {
        await loadTags() // Refresh the list
        operationHistory.value.unshift({
          type: 'create',
          tag: response.data.tag,
          timestamp: new Date().toISOString()
        })
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create tag'
      throw err
    }
  }

  const updateTag = async (tagName, updates) => {
    try {
      const response = await axios.put(`/api/tags/${encodeURIComponent(tagName)}`, updates)
      if (response.data.success) {
        await loadTags() // Refresh the list
        operationHistory.value.unshift({
          type: 'update',
          oldTag: tagName,
          newTag: response.data.tag,
          timestamp: new Date().toISOString()
        })
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update tag'
      throw err
    }
  }

  const deleteTag = async (tagName, options = {}) => {
    try {
      const response = await axios.delete(`/api/tags/${encodeURIComponent(tagName)}`, {
        data: options
      })
      if (response.data.success) {
        await loadTags() // Refresh the list
        operationHistory.value.unshift({
          type: 'delete',
          tag: tagName,
          affectedFiles: response.data.affected_files || 0,
          timestamp: new Date().toISOString()
        })
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete tag'
      throw err
    }
  }

  const bulkRenameTags = async (renames) => {
    try {
      const response = await axios.post('/api/tags/bulk-rename', { renames })
      if (response.data.success) {
        await loadTags() // Refresh the list
        operationHistory.value.unshift({
          type: 'bulk-rename',
          count: renames.length,
          affectedFiles: response.data.total_affected_files || 0,
          timestamp: new Date().toISOString()
        })
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to rename tags'
      throw err
    }
  }

  const mergeTags = async (sourceTag, targetTag) => {
    try {
      const response = await axios.post('/api/tags/merge', {
        source: sourceTag,
        target: targetTag
      })
      if (response.data.success) {
        await loadTags() // Refresh the list
        operationHistory.value.unshift({
          type: 'merge',
          sourceTag,
          targetTag,
          affectedFiles: response.data.affected_files || 0,
          timestamp: new Date().toISOString()
        })
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to merge tags'
      throw err
    }
  }

  const validateTags = async () => {
    try {
      const response = await axios.get('/api/tags/validate')
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to validate tags'
      throw err
    }
  }

  const getTagFiles = async (tagName) => {
    try {
      const response = await axios.get(`/api/tags/${encodeURIComponent(tagName)}/files`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to get tag files'
      throw err
    }
  }

  const clearHistory = () => {
    operationHistory.value = []
  }

  return {
    // State
    tags,
    tagStats,
    loading,
    error,
    operationHistory,

    // Getters
    totalTags,
    orphanedTags,
    duplicateTags,
    malformedTags,

    // Actions
    loadTags,
    createTag,
    updateTag,
    deleteTag,
    bulkRenameTags,
    mergeTags,
    validateTags,
    getTagFiles,
    clearHistory
  }
})
