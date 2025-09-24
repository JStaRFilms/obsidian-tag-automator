<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">Tag Manager</h1>
      <p class="text-slate-300">Create, edit, merge, and manage your tags</p>
    </div>

    <!-- Loading State -->
    <div v-if="tagsStore.loading" class="flex items-center justify-center min-h-96">
      <div class="text-center">
        <div class="loading-spinner mb-4"></div>
        <p class="text-slate-300">Loading tags...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="tagsStore.error" class="bg-red-900/20 border border-red-700 rounded-xl p-6">
      <div class="flex items-center space-x-3">
        <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
        <div>
          <h3 class="text-red-400 font-semibold">Error Loading Tags</h3>
          <p class="text-slate-300 text-sm">{{ tagsStore.error }}</p>
        </div>
      </div>
      <button @click="loadTags" class="mt-4 px-4 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors">
        Try Again
      </button>
    </div>

    <!-- Main Content -->
    <div v-else class="space-y-6">
      <!-- Quick Actions & Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Total Tags</p>
              <p class="text-3xl font-bold text-white mt-1">{{ tagsStore.totalTags }}</p>
            </div>
            <div class="bg-blue-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Orphaned Tags</p>
              <p class="text-3xl font-bold text-yellow-400 mt-1">{{ tagsStore.orphanedTags.length }}</p>
            </div>
            <div class="bg-yellow-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Duplicate Tags</p>
              <p class="text-3xl font-bold text-red-400 mt-1">{{ tagsStore.duplicateTags.length }}</p>
            </div>
            <div class="bg-red-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-slate-400 text-sm font-medium">Malformed Tags</p>
              <p class="text-3xl font-bold text-orange-400 mt-1">{{ tagsStore.malformedTags.length }}</p>
            </div>
            <div class="bg-orange-500/20 p-3 rounded-lg">
              <svg class="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="glass-effect rounded-xl p-6 shadow-xl">
        <h2 class="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            @click="showCreateModal = true"
            class="flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
            </svg>
            Create Tag
          </button>

          <button
            @click="showBulkRenameModal = true"
            class="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
            Bulk Rename
          </button>

          <button
            @click="showMergeModal = true"
            class="flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors"
          >
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
            </svg>
            Merge Tags
          </button>
        </div>
      </div>

      <!-- Tags List -->
      <div class="glass-effect rounded-xl shadow-xl overflow-hidden">
        <div class="p-6 border-b border-slate-700">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-white">All Tags</h2>
            <div class="flex items-center space-x-2">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search tags..."
                class="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                v-model="sortBy"
                class="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="name">Name</option>
                <option value="count">File Count</option>
                <option value="recent">Recently Used</option>
              </select>
            </div>
          </div>
        </div>

        <div class="max-h-96 overflow-y-auto">
          <div v-if="filteredTags.length === 0" class="p-8 text-center text-slate-400">
            No tags found matching your criteria.
          </div>

          <div v-else class="divide-y divide-slate-700">
            <div
              v-for="tag in filteredTags"
              :key="tag.name"
              class="p-4 hover:bg-slate-800/50 transition-colors group"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="flex items-center space-x-2">
                    <span class="px-2 py-1 bg-slate-700 text-slate-300 rounded text-sm font-medium">
                      {{ tag.name }}
                    </span>
                    <span class="text-xs text-slate-500">
                      {{ tagStats[tag.name]?.file_count || 0 }} files
                    </span>
                  </div>

                  <!-- Tag issues -->
                  <div class="flex items-center space-x-1">
                    <span
                      v-if="tag.name.includes(' ') || tag.name.includes('#')"
                      class="px-2 py-1 bg-orange-900/20 text-orange-400 rounded text-xs"
                    >
                      Malformed
                    </span>
                    <span
                      v-if="(tagStats[tag.name]?.file_count || 0) === 0"
                      class="px-2 py-1 bg-yellow-900/20 text-yellow-400 rounded text-xs"
                    >
                      Orphaned
                    </span>
                  </div>
                </div>

                <div class="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    @click="editTag(tag)"
                    class="p-1 text-slate-400 hover:text-blue-400 transition-colors"
                    title="Edit tag"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>

                  <button
                    @click="showTagFiles(tag)"
                    class="p-1 text-slate-400 hover:text-green-400 transition-colors"
                    title="View files with this tag"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                  </button>

                  <button
                    @click="deleteTag(tag)"
                    class="p-1 text-slate-400 hover:text-red-400 transition-colors"
                    title="Delete tag"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Operation History -->
      <div v-if="tagsStore.operationHistory.length > 0" class="glass-effect rounded-xl p-6 shadow-xl">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-white">Recent Operations</h2>
          <button
            @click="tagsStore.clearHistory"
            class="px-3 py-1 text-sm bg-slate-700 text-white rounded hover:bg-slate-600 transition-colors"
          >
            Clear History
          </button>
        </div>

        <div class="space-y-2 max-h-48 overflow-y-auto">
          <div
            v-for="(operation, index) in tagsStore.operationHistory.slice(0, 10)"
            :key="index"
            class="flex items-center justify-between py-2 px-3 bg-slate-800/30 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <div
                class="w-2 h-2 rounded-full"
                :class="{
                  'bg-green-400': operation.type === 'create',
                  'bg-blue-400': operation.type === 'update',
                  'bg-red-400': operation.type === 'delete',
                  'bg-purple-400': operation.type === 'merge',
                  'bg-yellow-400': operation.type === 'bulk-rename'
                }"
              ></div>
              <span class="text-sm text-white capitalize">{{ operation.type }}</span>
              <span class="text-sm text-slate-400">
                {{ getOperationDescription(operation) }}
              </span>
            </div>
            <span class="text-xs text-slate-500">
              {{ formatTimeAgo(operation.timestamp) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Tag Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-slate-800 rounded-xl p-6 w-full max-w-md mx-4">
        <h3 class="text-lg font-semibold text-white mb-4">Create New Tag</h3>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">Tag Name</label>
            <input
              v-model="newTagName"
              type="text"
              placeholder="Enter tag name..."
              class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              @keyup.enter="createTag"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">Description (optional)</label>
            <textarea
              v-model="newTagDescription"
              rows="3"
              placeholder="Enter tag description..."
              class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>
        </div>

        <div class="flex items-center justify-end space-x-3 mt-6">
          <button
            @click="showCreateModal = false"
            class="px-4 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="createTag"
            :disabled="!newTagName.trim()"
            class="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Create Tag
          </button>
        </div>
      </div>
    </div>

    <!-- Bulk Rename Modal -->
    <div v-if="showBulkRenameModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-slate-800 rounded-xl p-6 w-full max-w-lg mx-4">
        <h3 class="text-lg font-semibold text-white mb-4">Bulk Rename Tags</h3>

        <div class="space-y-4">
          <div class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3">
            <p class="text-sm text-yellow-300">
              This will rename all occurrences of the old tag to the new tag across all files.
            </p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">Old Tag</label>
              <input
                v-model="bulkRenameOld"
                type="text"
                placeholder="e.g., old-name"
                class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">New Tag</label>
              <input
                v-model="bulkRenameNew"
                type="text"
                placeholder="e.g., new-name"
                class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end space-x-3 mt-6">
          <button
            @click="showBulkRenameModal = false"
            class="px-4 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="bulkRename"
            :disabled="!bulkRenameOld.trim() || !bulkRenameNew.trim()"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Rename All
          </button>
        </div>
      </div>
    </div>

    <!-- Merge Tags Modal -->
    <div v-if="showMergeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-slate-800 rounded-xl p-6 w-full max-w-lg mx-4">
        <h3 class="text-lg font-semibold text-white mb-4">Merge Tags</h3>

        <div class="space-y-4">
          <div class="bg-purple-900/20 border border-purple-700 rounded-lg p-3">
            <p class="text-sm text-purple-300">
              This will merge the source tag into the target tag and remove the source tag.
            </p>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">Source Tag (will be removed)</label>
              <select
                v-model="mergeSource"
                class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select source tag...</option>
                <option v-for="tag in tagsStore.tags" :key="tag.name" :value="tag.name">
                  {{ tag.name }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">Target Tag (will remain)</label>
              <select
                v-model="mergeTarget"
                class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select target tag...</option>
                <option v-for="tag in tagsStore.tags" :key="tag.name" :value="tag.name">
                  {{ tag.name }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end space-x-3 mt-6">
          <button
            @click="showMergeModal = false"
            class="px-4 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="mergeTags"
            :disabled="!mergeSource || !mergeTarget || mergeSource === mergeTarget"
            class="px-4 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Merge Tags
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useTagsStore } from '../stores/tags'

// Store
const tagsStore = useTagsStore()

// Reactive state
const searchQuery = ref('')
const sortBy = ref('name')
const showCreateModal = ref(false)
const showBulkRenameModal = ref(false)
const showMergeModal = ref(false)

// Form data
const newTagName = ref('')
const newTagDescription = ref('')
const bulkRenameOld = ref('')
const bulkRenameNew = ref('')
const mergeSource = ref('')
const mergeTarget = ref('')

// Computed properties
const filteredTags = computed(() => {
  let tags = [...tagsStore.tags]

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    tags = tags.filter(tag => tag.name.toLowerCase().includes(query))
  }

  // Apply sorting
  tags.sort((a, b) => {
    switch (sortBy.value) {
      case 'count':
        return (tagsStore.tagStats[b.name]?.file_count || 0) - (tagsStore.tagStats[a.name]?.file_count || 0)
      case 'recent':
        // For now, sort by name as recent data isn't available
        return a.name.localeCompare(b.name)
      default:
        return a.name.localeCompare(b.name)
    }
  })

  return tags
})

const tagStats = computed(() => tagsStore.tagStats)

// Methods
const loadTags = async () => {
  try {
    await tagsStore.loadTags()
  } catch (err) {
    console.error('Failed to load tags:', err)
  }
}

const createTag = async () => {
  if (!newTagName.value.trim()) return

  try {
    await tagsStore.createTag({
      name: newTagName.value.trim(),
      description: newTagDescription.value.trim()
    })

    // Reset form
    newTagName.value = ''
    newTagDescription.value = ''
    showCreateModal.value = false
  } catch (err) {
    console.error('Failed to create tag:', err)
  }
}

const editTag = (tag) => {
  // For now, just show an alert. In a real app, this would open an edit modal
  alert(`Edit functionality for "${tag.name}" would be implemented here`)
}

const showTagFiles = async (tag) => {
  try {
    const result = await tagsStore.getTagFiles(tag.name)
    if (result.success && result.files) {
      alert(`Tag "${tag.name}" is used in ${result.files.length} files:\n${result.files.slice(0, 5).map(f => `- ${f}`).join('\n')}${result.files.length > 5 ? '\n...' : ''}`)
    }
  } catch (err) {
    console.error('Failed to get tag files:', err)
  }
}

const deleteTag = async (tag) => {
  if (!confirm(`Are you sure you want to delete the tag "${tag.name}"? This will remove it from all files.`)) {
    return
  }

  try {
    await tagsStore.deleteTag(tag.name, { confirm: true })
  } catch (err) {
    console.error('Failed to delete tag:', err)
  }
}

const bulkRename = async () => {
  if (!bulkRenameOld.value.trim() || !bulkRenameNew.value.trim()) return

  if (!confirm(`Are you sure you want to rename all occurrences of "${bulkRenameOld.value}" to "${bulkRenameNew.value}"?`)) {
    return
  }

  try {
    await tagsStore.bulkRenameTags([{
      old_name: bulkRenameOld.value.trim(),
      new_name: bulkRenameNew.value.trim()
    }])

    // Reset form
    bulkRenameOld.value = ''
    bulkRenameNew.value = ''
    showBulkRenameModal.value = false
  } catch (err) {
    console.error('Failed to rename tags:', err)
  }
}

const mergeTags = async () => {
  if (!mergeSource.value || !mergeTarget.value || mergeSource.value === mergeTarget.value) return

  if (!confirm(`Are you sure you want to merge "${mergeSource.value}" into "${mergeTarget.value}"? The source tag will be deleted.`)) {
    return
  }

  try {
    await tagsStore.mergeTags(mergeSource.value, mergeTarget.value)

    // Reset form
    mergeSource.value = ''
    mergeTarget.value = ''
    showMergeModal.value = false
  } catch (err) {
    console.error('Failed to merge tags:', err)
  }
}

const getOperationDescription = (operation) => {
  switch (operation.type) {
    case 'create':
      return `Created "${operation.tag?.name || 'tag'}"`
    case 'update':
      return `"${operation.oldTag}" → "${operation.newTag}"`
    case 'delete':
      return `Deleted "${operation.tag}" (${operation.affectedFiles || 0} files)`
    case 'merge':
      return `Merged "${operation.sourceTag}" into "${operation.targetTag}"`
    case 'bulk-rename':
      return `Renamed ${operation.count} tags (${operation.affectedFiles || 0} files)`
    default:
      return operation.type
  }
}

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

// Load tags on mount
onMounted(() => {
  loadTags()
})

// Watch for sort changes to refresh if needed
watch(sortBy, () => {
  // Could implement more sophisticated sorting here
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
