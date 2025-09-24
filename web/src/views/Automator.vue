<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-white mb-2">Tag Automator</h1>
      <p class="text-slate-300">Automatically process files with AI-powered tag suggestions</p>
    </div>

    <!-- Processing Progress (when active) -->
    <div v-if="filesStore.isProcessing" class="mb-6">
      <div class="glass-effect rounded-xl p-6 shadow-xl">
        <ProgressBar
          :current="filesStore.progress.current"
          :total="filesStore.progress.total"
          :message="filesStore.progress.message"
          :status="filesStore.progress.status"
          :error="filesStore.error"
          :show-controls="true"
          title="Processing Files"
          @pause="handlePause"
          @resume="handleResume"
          @stop="handleStop"
        />
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Configuration Panel -->
      <div class="lg:col-span-1">
        <div class="glass-effect rounded-xl p-6 shadow-xl sticky top-6">
          <h2 class="text-xl font-semibold text-white mb-6">Configuration</h2>

          <!-- Processing Strategy -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-slate-300 mb-3">Processing Strategy</label>
            <div class="space-y-2">
              <label class="flex items-center">
                <input
                  v-model="processingStrategy"
                  type="radio"
                  value="untagged"
                  class="text-blue-600 bg-slate-700 border-slate-600 focus:ring-blue-500 focus:ring-1"
                />
                <span class="ml-2 text-sm text-slate-300">Untagged files only</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="processingStrategy"
                  type="radio"
                  value="all"
                  class="text-blue-600 bg-slate-700 border-slate-600 focus:ring-blue-500 focus:ring-1"
                />
                <span class="ml-2 text-sm text-slate-300">All files</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="processingStrategy"
                  type="radio"
                  value="pattern"
                  class="text-blue-600 bg-slate-700 border-slate-600 focus:ring-blue-500 focus:ring-1"
                />
                <span class="ml-2 text-sm text-slate-300">Pattern match</span>
              </label>
            </div>

            <!-- Pattern input (when pattern strategy is selected) -->
            <div v-if="processingStrategy === 'pattern'" class="mt-3">
              <input
                v-model="pattern"
                type="text"
                placeholder="e.g., *.md, project-*.txt"
                class="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <!-- AI Settings -->
          <div class="mb-6">
            <label class="flex items-center mb-3">
              <input
                v-model="aiEnabled"
                type="checkbox"
                class="text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-1"
              />
              <span class="ml-2 text-sm font-medium text-slate-300">Enable AI Suggestions</span>
            </label>

            <div v-if="aiEnabled" class="ml-6">
              <label class="block text-sm text-slate-400 mb-2">AI Confidence Threshold</label>
              <select
                v-model="aiConfidence"
                class="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="0.3">Low (30%)</option>
                <option value="0.5">Medium (50%)</option>
                <option value="0.7">High (70%)</option>
                <option value="0.9">Very High (90%)</option>
              </select>
            </div>
          </div>

          <!-- Options -->
          <div class="mb-6">
            <label class="flex items-center mb-3">
              <input
                v-model="dryRun"
                type="checkbox"
                class="text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-1"
              />
              <span class="ml-2 text-sm font-medium text-slate-300">Dry run (preview only)</span>
            </label>

            <label class="flex items-center">
              <input
                v-model="autoApply"
                type="checkbox"
                class="text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-1"
              />
              <span class="ml-2 text-sm font-medium text-slate-300">Auto-apply suggestions</span>
            </label>
          </div>

          <!-- Action Buttons -->
          <div class="space-y-3">
            <button
              @click="startProcessing"
              :disabled="selectedFiles.length === 0 || filesStore.isProcessing"
              class="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg v-if="filesStore.isProcessing" class="w-4 h-4 mr-2 inline animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              {{ filesStore.isProcessing ? 'Processing...' : 'Start Processing' }}
            </button>

            <button
              @click="clearSelection"
              :disabled="selectedFiles.length === 0"
              class="w-full px-4 py-2 bg-slate-700 text-white rounded-lg font-medium hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Clear Selection
            </button>
          </div>
        </div>
      </div>

      <!-- File Browser -->
      <div class="lg:col-span-2">
        <div class="glass-effect rounded-xl p-6 shadow-xl">
          <FileBrowser
            :selected-files="selectedFiles"
            @selection-changed="handleSelectionChange"
          />
        </div>

        <!-- Processing Summary -->
        <div v-if="selectedFiles.length > 0" class="mt-6 glass-effect rounded-xl p-6 shadow-xl">
          <h3 class="text-lg font-semibold text-white mb-4">Processing Summary</h3>

          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-400">{{ selectedFiles.length }}</div>
              <div class="text-sm text-slate-400">Selected Files</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-green-400">{{ selectedTaggedCount }}</div>
              <div class="text-sm text-slate-400">Already Tagged</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-yellow-400">{{ selectedUntaggedCount }}</div>
              <div class="text-sm text-slate-400">Untagged</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-purple-400">{{ estimatedTime }}</div>
              <div class="text-sm text-slate-400">Est. Time (min)</div>
            </div>
          </div>

          <div v-if="processingStrategy === 'untagged' && selectedTaggedCount > 0" class="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3">
            <div class="flex items-center space-x-2">
              <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
              <span class="text-sm text-yellow-300">
                {{ selectedTaggedCount }} tagged file{{ selectedTaggedCount !== 1 ? 's' : '' }} will be skipped with "Untagged only" strategy.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useFilesStore } from '../stores/files'
import FileBrowser from '../components/FileBrowser.vue'
import ProgressBar from '../components/ProgressBar.vue'

const filesStore = useFilesStore()

// Reactive state
const processingStrategy = ref('untagged')
const pattern = ref('')
const aiEnabled = ref(true)
const aiConfidence = ref('0.5')
const dryRun = ref(false)
const autoApply = ref(true)

// Computed properties
const selectedFiles = computed(() => filesStore.selectedFiles)

const selectedTaggedCount = computed(() =>
  selectedFiles.value.filter(f => f.tags && f.tags.length > 0).length
)

const selectedUntaggedCount = computed(() =>
  selectedFiles.value.filter(f => !f.tags || f.tags.length === 0).length
)

const estimatedTime = computed(() => {
  const baseTimePerFile = aiEnabled.value ? 2 : 0.5 // seconds per file
  const filesToProcess = processingStrategy.value === 'untagged'
    ? selectedUntaggedCount.value
    : selectedFiles.value.length

  return Math.ceil((filesToProcess * baseTimePerFile) / 60) // minutes
})

// Methods
const handleSelectionChange = ({ file, selected }) => {
  filesStore.selectFiles(file, selected)
}

const clearSelection = () => {
  filesStore.clearSelection()
}

const startProcessing = async () => {
  if (selectedFiles.value.length === 0) return

  try {
    await filesStore.processFiles({
      strategy: processingStrategy.value,
      pattern: pattern.value,
      ai_enabled: aiEnabled.value,
      ai_confidence: parseFloat(aiConfidence.value),
      dry_run: dryRun.value,
      auto_apply: autoApply.value
    })
  } catch (err) {
    console.error('Processing failed:', err)
  }
}

const handlePause = async () => {
  try {
    await filesStore.pauseProcessing()
  } catch (err) {
    console.error('Failed to pause:', err)
  }
}

const handleResume = async () => {
  try {
    await filesStore.resumeProcessing()
  } catch (err) {
    console.error('Failed to resume:', err)
  }
}

const handleStop = async () => {
  try {
    await filesStore.stopProcessing()
  } catch (err) {
    console.error('Failed to stop:', err)
  }
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
</script>
