<template>
  <div class="file-tree-node">
    <div
      class="flex items-center py-1 px-2 hover:bg-slate-800 rounded cursor-pointer group"
      :class="{
        'bg-slate-800': isSelected,
        'bg-blue-900/30': isSelected
      }"
      @click="handleClick"
    >
      <!-- Expand/collapse icon for directories -->
      <div v-if="item.type === 'directory'" class="w-4 h-4 mr-2 flex items-center justify-center">
        <svg
          class="w-3 h-3 text-slate-400 transition-transform"
          :class="{ 'rotate-90': isExpanded }"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </div>

      <!-- File/directory icon -->
      <div class="w-4 h-4 mr-2 flex items-center justify-center">
        <svg v-if="item.type === 'directory'" class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
        </svg>
        <svg v-else class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
      </div>

      <!-- Checkbox for selection -->
      <input
        type="checkbox"
        :checked="isSelected"
        @change.stop="handleSelect"
        class="mr-2 w-3 h-3 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-1"
      />

      <!-- File/directory name -->
      <span
        class="flex-1 text-sm truncate"
        :class="{
          'text-white': isSelected,
          'text-slate-300': !isSelected,
          'font-medium': item.type === 'directory'
        }"
      >
        {{ item.name }}
      </span>

      <!-- Tag indicators -->
      <div v-if="item.tags && item.tags.length > 0" class="flex items-center space-x-1 ml-2">
        <div class="flex items-center space-x-1">
          <svg class="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
          </svg>
          <span class="text-xs text-slate-400">{{ item.tags.length }}</span>
        </div>
      </div>

      <!-- File size -->
      <span v-if="item.type === 'file' && item.size" class="text-xs text-slate-500 ml-2">
        {{ formatFileSize(item.size) }}
      </span>
    </div>

    <!-- Children (for directories) -->
    <div v-if="item.type === 'directory' && isExpanded && item.children" class="ml-6">
      <FileTreeNode
        v-for="child in item.children"
        :key="child.path"
        :item="child"
        :selected-files="selectedFiles"
        :search-query="searchQuery"
        @select="$emit('select', $event.file, $event.selected)"
        @expand="$emit('expand', $event.path, $event.expanded)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  selectedFiles: {
    type: Array,
    default: () => []
  },
  searchQuery: {
    type: String,
    default: ''
  },
  level: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['select', 'expand'])

// Computed properties
const isSelected = computed(() =>
  props.selectedFiles.some(f => f.path === props.item.path)
)

const isExpanded = computed(() => {
  // For now, just expand directories that contain search results
  if (props.searchQuery && props.item.type === 'directory') {
    return hasMatchingChildren(props.item, props.searchQuery)
  }
  return false // Default collapsed
})

// Methods
const handleClick = () => {
  if (props.item.type === 'directory') {
    // Toggle expansion
    emit('expand', props.item.path, !isExpanded.value)
  }
}

const handleSelect = (event) => {
  emit('select', props.item, event.target.checked)
}

const hasMatchingChildren = (item, query) => {
  if (!item.children) return false

  return item.children.some(child => {
    if (child.name.toLowerCase().includes(query.toLowerCase())) {
      return true
    }
    if (child.type === 'directory') {
      return hasMatchingChildren(child, query)
    }
    return false
  })
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>

<style scoped>
.file-tree-node {
  position: relative;
}

.rotate-90 {
  transform: rotate(90deg);
}
</style>
