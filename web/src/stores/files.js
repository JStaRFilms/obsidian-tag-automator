import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useFilesStore = defineStore('files', () => {
  // State
  const files = ref([])
  const selectedFiles = ref([])
  const fileTree = ref([])
  const loading = ref(false)
  const error = ref(null)
  const operationInProgress = ref(false)
  const progress = ref({
    current: 0,
    total: 0,
    message: '',
    status: 'idle' // idle, processing, paused, completed, error
  })

  // Getters
  const totalFiles = computed(() => files.value.length)
  const taggedFiles = computed(() => files.value.filter(file => file.tags && file.tags.length > 0))
  const untaggedFiles = computed(() => files.value.filter(file => !file.tags || file.tags.length === 0))
  const selectedFileCount = computed(() => selectedFiles.value.length)
  const isProcessing = computed(() => operationInProgress.value)
  const progressPercentage = computed(() =>
    progress.value.total > 0 ? Math.round((progress.value.current / progress.value.total) * 100) : 0
  )

  // Actions
  const loadFiles = async (options = {}) => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (options.filter) params.append('filter', options.filter)
      if (options.sort) params.append('sort', options.sort)
      if (options.limit) params.append('limit', options.limit)

      const response = await axios.get(`/api/files?${params}`)
      if (response.data.success) {
        files.value = response.data.files || []
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load files'
      throw err
    } finally {
      loading.value = false
    }
  }

  const loadFileTree = async (path = '') => {
    try {
      const response = await axios.get(`/api/files/tree?path=${encodeURIComponent(path)}`)
      if (response.data.success) {
        fileTree.value = response.data.tree || []
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to load file tree'
      throw err
    }
  }

  const selectFiles = (fileSelection) => {
    if (Array.isArray(fileSelection)) {
      selectedFiles.value = fileSelection
    } else {
      const index = selectedFiles.value.findIndex(f => f.path === fileSelection.path)
      if (index > -1) {
        selectedFiles.value.splice(index, 1)
      } else {
        selectedFiles.value.push(fileSelection)
      }
    }
  }

  const clearSelection = () => {
    selectedFiles.value = []
  }

  const selectAll = (files) => {
    selectedFiles.value = [...files]
  }

  const selectFiltered = (filterFn) => {
    selectedFiles.value = files.value.filter(filterFn)
  }

  const processFiles = async (options = {}) => {
    if (selectedFiles.value.length === 0) {
      throw new Error('No files selected for processing')
    }

    operationInProgress.value = true
    progress.value = {
      current: 0,
      total: selectedFiles.value.length,
      message: 'Initializing...',
      status: 'processing'
    }

    try {
      const payload = {
        files: selectedFiles.value.map(f => f.path),
        strategy: options.strategy || 'untagged', // untagged, all, pattern
        pattern: options.pattern || '',
        ai_enabled: options.ai_enabled !== false,
        dry_run: options.dry_run || false
      }

      const response = await axios.post('/api/files/process', payload)

      if (response.data.success) {
        progress.value.status = 'completed'
        progress.value.message = 'Processing completed successfully'

        // Refresh files list
        await loadFiles()

        return response.data
      } else {
        throw new Error(response.data.error || 'Processing failed')
      }
    } catch (err) {
      progress.value.status = 'error'
      progress.value.message = err.response?.data?.error || err.message || 'Processing failed'
      error.value = progress.value.message
      throw err
    } finally {
      operationInProgress.value = false
    }
  }

  const pauseProcessing = async () => {
    try {
      const response = await axios.post('/api/files/process/pause')
      if (response.data.success) {
        progress.value.status = 'paused'
        progress.value.message = 'Processing paused'
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to pause processing'
      throw err
    }
  }

  const resumeProcessing = async () => {
    try {
      const response = await axios.post('/api/files/process/resume')
      if (response.data.success) {
        progress.value.status = 'processing'
        progress.value.message = 'Processing resumed'
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to resume processing'
      throw err
    }
  }

  const stopProcessing = async () => {
    try {
      const response = await axios.post('/api/files/process/stop')
      if (response.data.success) {
        progress.value.status = 'idle'
        progress.value.message = 'Processing stopped'
        operationInProgress.value = false
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to stop processing'
      throw err
    }
  }

  const getFileTags = async (filePath) => {
    try {
      const response = await axios.get(`/api/files/${encodeURIComponent(filePath)}/tags`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to get file tags'
      throw err
    }
  }

  const updateFileTags = async (filePath, tags) => {
    try {
      const response = await axios.put(`/api/files/${encodeURIComponent(filePath)}/tags`, { tags })
      if (response.data.success) {
        // Update local file data
        const fileIndex = files.value.findIndex(f => f.path === filePath)
        if (fileIndex > -1) {
          files.value[fileIndex].tags = tags
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update file tags'
      throw err
    }
  }

  const addTagsToFiles = async (filePaths, tags) => {
    try {
      const response = await axios.post('/api/files/bulk-add-tags', {
        files: filePaths,
        tags: tags
      })
      if (response.data.success) {
        await loadFiles() // Refresh the list
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to add tags to files'
      throw err
    }
  }

  const removeTagsFromFiles = async (filePaths, tags) => {
    try {
      const response = await axios.post('/api/files/bulk-remove-tags', {
        files: filePaths,
        tags: tags
      })
      if (response.data.success) {
        await loadFiles() // Refresh the list
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to remove tags from files'
      throw err
    }
  }

  const getProcessingStatus = async () => {
    try {
      const response = await axios.get('/api/files/process/status')
      if (response.data.success) {
        progress.value = {
          current: response.data.current || 0,
          total: response.data.total || 0,
          message: response.data.message || '',
          status: response.data.status || 'idle'
        }
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to get processing status'
      throw err
    }
  }

  const resetProgress = () => {
    progress.value = {
      current: 0,
      total: 0,
      message: '',
      status: 'idle'
    }
  }

  return {
    // State
    files,
    selectedFiles,
    fileTree,
    loading,
    error,
    operationInProgress,
    progress,

    // Getters
    totalFiles,
    taggedFiles,
    untaggedFiles,
    selectedFileCount,
    isProcessing,
    progressPercentage,

    // Actions
    loadFiles,
    loadFileTree,
    selectFiles,
    clearSelection,
    selectAll,
    selectFiltered,
    processFiles,
    pauseProcessing,
    resumeProcessing,
    stopProcessing,
    getFileTags,
    updateFileTags,
    addTagsToFiles,
    removeTagsFromFiles,
    getProcessingStatus,
    resetProgress
  }
})
