<template>
  <div class="progress-container">
    <!-- Progress bar -->
    <div class="mb-3">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center space-x-2">
          <div
            class="w-3 h-3 rounded-full"
            :class="statusClass"
          ></div>
          <span class="text-sm font-medium text-white">{{ title }}</span>
        </div>
        <span class="text-sm text-slate-400">{{ percentage }}%</span>
      </div>

      <div class="progress-bar-bg">
        <div
          class="progress-bar-fill transition-all duration-300 ease-out"
          :class="fillClass"
          :style="{ width: `${percentage}%` }"
        ></div>
      </div>
    </div>

    <!-- Status message -->
    <div class="flex items-center justify-between">
      <p class="text-sm text-slate-300">{{ message }}</p>
      <div class="flex items-center space-x-2">
        <span class="text-xs text-slate-400">
          {{ current }} / {{ total }}
        </span>

        <!-- Control buttons -->
        <div v-if="showControls" class="flex items-center space-x-1">
          <button
            v-if="canPause"
            @click="$emit('pause')"
            class="px-2 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
          >
            Pause
          </button>
          <button
            v-if="canResume"
            @click="$emit('resume')"
            class="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
          >
            Resume
          </button>
          <button
            v-if="canStop"
            @click="$emit('stop')"
            class="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
          >
            Stop
          </button>
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mt-2 p-2 bg-red-900/20 border border-red-700 rounded-lg">
      <p class="text-sm text-red-400">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  current: {
    type: Number,
    default: 0
  },
  total: {
    type: Number,
    default: 0
  },
  message: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: 'Progress'
  },
  status: {
    type: String,
    default: 'processing',
    validator: (value) => ['idle', 'processing', 'paused', 'completed', 'error'].includes(value)
  },
  error: {
    type: String,
    default: ''
  },
  showControls: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['pause', 'resume', 'stop'])

// Computed properties
const percentage = computed(() => {
  if (props.total === 0) return 0
  return Math.round((props.current / props.total) * 100)
})

const statusClass = computed(() => {
  switch (props.status) {
    case 'processing':
      return 'bg-blue-500 animate-pulse'
    case 'paused':
      return 'bg-yellow-500'
    case 'completed':
      return 'bg-green-500'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-slate-500'
  }
})

const fillClass = computed(() => {
  switch (props.status) {
    case 'processing':
      return 'bg-blue-500'
    case 'paused':
      return 'bg-yellow-500'
    case 'completed':
      return 'bg-green-500'
    case 'error':
      return 'bg-red-500'
    default:
      return 'bg-slate-500'
  }
})

const canPause = computed(() =>
  props.showControls && props.status === 'processing'
)

const canResume = computed(() =>
  props.showControls && props.status === 'paused'
)

const canStop = computed(() =>
  props.showControls && ['processing', 'paused'].includes(props.status)
)
</script>

<style scoped>
.progress-container {
  min-width: 300px;
}

.progress-bar-bg {
  height: 8px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease-out;
}
</style>
