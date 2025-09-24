<template>
  <div class="file-browser">
    <!-- Header with controls -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">File Browser</h3>
      <div class="flex items-center space-x-2">
        <button
          @click="toggleSelectAll"
          class="px-3 py-1 text-sm bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
        >
          {{ allSelected ? 'Deselect All' : 'Select All' }}
        </button>
        <button
          @click="clearSelection"
          class="px-3 py-1 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Clear ({{ selectedCount }})
        </button>
      </div>
    </div>

    <!-- Search and filters -->
    <div class="mb-4 flex flex-col sm:flex-row gap-3">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search files..."
        class="flex-1 px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        v-model="filterType"
        class="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="all">All Files</option>
        <option value="untagged">Untagged Only</option>
        <option value="tagged">Tagged Only</option>
        <option value="markdown">Markdown (.md)</option>
        <option value="text">Text Files</option>
      </select>
    </div>

    <!-- File tree -->
    <div class="file-tree bg-slate-900 rounded-lg border border-slate-700 max-h-96 overflow-y-auto">
      <div v-if="loading" class="flex items-center justify-center py-8">
        <div class="loading-spinner"></div>
        <span class="ml-2 text-slate-400">Loading files...</span>
      </div>

      <div v-else-if="error" class="p-4 text-red-400">
        <div class="flex items-center space-x-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
          <span>{{ error }}</span>
        </div>
      </div>

      <div v-else>
        <!-- Root directory -->
        <div class="p-2">
          <FileTreeNode
            v-for="item in filteredItems"
            :key="item.path"
            :item="item"
            :selected-files="selectedFiles"
            :search-query="searchQuery"
            @select="handleSelect"
            @expand="handleExpand"
          />
        </div>

        <div v-if="filteredItems.length === 0" class="p-4 text-center text-slate-400">
          No files found matching your criteria.
        </div>
      </div>
    </div>

    <!-- Selection summary -->
    <div v-if="selectedCount > 0" class="mt-4 p-3 bg-blue-900/20 border border-blue-700 rounded-lg">
      <div class="flex items-center justify-between">
        <span class="text-blue-300">
          {{ selectedCount }} file{{ selectedCount !== 1 ? 's' : '' }} selected
        </span>
        <div class="flex items-center space-x-2">
          <span class="text-xs text-slate-400">
            {{ selectedTaggedCount }} tagged, {{ selectedUntaggedCount }} untagged
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useFilesStore } from '../stores/files'
import FileTreeNode from './FileTreeNode.vue'

const props = defineProps({
  selectedFiles: {
    type: Array,
    default: () => []
  },
  multiSelect: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['selection-changed'])

const filesStore = useFilesStore()

// Local state
const searchQuery = ref('')
const filterType = ref('all')
const expandedDirs = ref(new Set())

// Computed properties
const loading = computed(() => filesStore.loading)
const error = computed(() => filesStore.error)

const filteredItems = computed(() => {
  let items = filesStore.files

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    items = items.filter(item =>
      item.name.toLowerCase().includes(query) ||
      item.path.toLowerCase().includes(query)
    )
  }

  // Apply type filter
  switch (filterType.value) {
    case 'untagged':
      items = items.filter(item => !item.tags || item.tags.length === 0)
      break
    case 'tagged':
      items = items.filter(item => item.tags && item.tags.length > 0)
      break
    case 'markdown':
      items = items.filter(item => item.name.endsWith('.md'))
      break
    case 'text':
      items = items.filter(item =>
        item.name.endsWith('.txt') ||
        item.name.endsWith('.md') ||
        item.name.endsWith('.org')
      )
      break
  }

  return items
})

const selectedCount = computed(() => props.selectedFiles.length)
const allSelected = computed(() =>
  filteredItems.value.length > 0 &&
  filteredItems.value.every(item => props.selectedFiles.some(f => f.path === item.path))
)

const selectedTaggedCount = computed(() =>
  props.selectedFiles.filter(f => f.tags && f.tags.length > 0).length
)

const selectedUntaggedCount = computed(() =>
  props.selectedFiles.filter(f => !f.tags || f.tags.length === 0).length
)

// Methods
const handleSelect = (file, selected) => {
  emit('selection-changed', { file, selected })
}

const handleExpand = (path, expanded) => {
  if (expanded) {
    expandedDirs.value.add(path)
  } else {
    expandedDirs.value.delete(path)
  }
}

const toggleSelectAll = () => {
  if (allSelected.value) {
    // Deselect all
    filteredItems.value.forEach(item => {
      emit('selection-changed', { file: item, selected: false })
    })
  } else {
    // Select all
    filteredItems.value.forEach(item => {
      if (!props.selectedFiles.some(f => f.path === item.path)) {
        emit('selection-changed', { file: item, selected: true })
      }
    })
  }
}

const clearSelection = () => {
  props.selectedFiles.forEach(file => {
    emit('selection-changed', { file, selected: false })
  })
}

// Load files on mount
onMounted(async () => {
  if (filesStore.files.length === 0) {
    try {
      await filesStore.loadFiles()
    } catch (err) {
      console.error('Failed to load files:', err)
    }
  }
})

// Watch for filter changes
watch([searchQuery, filterType], () => {
  // Could implement debouncing here for search
})
</script>

<style scoped>
.loading-spinner {
  border: 3px solid rgba(56, 189, 248, 0.2);
  border-radius: 50%;
  border-top-color: #38bdf8;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.file-tree {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.3) transparent;
}

.file-tree::-webkit-scrollbar {
  width: 6px;
}

.file-tree::-webkit-scrollbar-track {
  background: transparent;
}

.file-tree::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.file-tree::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>
