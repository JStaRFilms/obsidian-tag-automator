<template>
  <div id="app" class="min-h-screen bg-gradient-to-br from-secondary-900 via-secondary-800 to-primary-900">
    <!-- Header -->
    <header class="bg-glass-400 backdrop-blur-sm border-b border-glass-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- Logo -->
          <div class="flex items-center space-x-4">
            <div class="w-10 h-10 rounded-xl bg-primary-500 flex items-center justify-center shadow-glow">
              <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
              </svg>
            </div>
            <div>
              <h1 class="text-xl font-bold text-white">Obsidian Tag Automator</h1>
              <p class="text-xs text-secondary-300">AI-Powered Knowledge Management</p>
            </div>
          </div>

          <!-- Mobile menu button -->
          <button
            @click="toggleMobileMenu"
            class="md:hidden p-2 rounded-lg bg-glass-300 text-secondary-200 hover:text-white transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!isMobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>

          <!-- Desktop navigation -->
          <nav class="hidden md:flex space-x-1">
            <router-link
              v-for="route in navigation"
              :key="route.name"
              :to="route.path"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2"
              :class="[
                $route.name === route.name
                  ? 'bg-primary-500 text-white shadow-glow'
                  : 'text-secondary-300 hover:text-white hover:bg-glass-300'
              ]"
            >
              <span class="text-lg">{{ route.icon }}</span>
              <span>{{ route.label }}</span>
            </router-link>
          </nav>
        </div>
      </div>

      <!-- Mobile menu -->
      <div
        v-show="isMobileMenuOpen"
        class="md:hidden border-t border-glass-200 bg-glass-500 backdrop-blur-sm"
      >
        <nav class="px-4 py-3 space-y-1">
          <router-link
            v-for="route in navigation"
            :key="route.name"
            :to="route.path"
            @click="closeMobileMenu"
            class="block px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-3"
            :class="[
              $route.name === route.name
                ? 'bg-primary-500 text-white shadow-glow'
                : 'text-secondary-300 hover:text-white hover:bg-glass-300'
            ]"
            >
            <span class="text-lg">{{ route.icon }}</span>
            <span>{{ route.label }}</span>
          </router-link>
        </nav>
      </div>
    </header>

    <!-- Main content -->
    <main class="flex-1">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="bg-glass-400 backdrop-blur-sm border-t border-glass-200 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="text-center text-secondary-400 text-sm">
          <p>&copy; 2025 Obsidian Tag Automator. Built with Vue.js & AI.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

// Mobile menu state
const isMobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

// Navigation configuration with simple text icons (temporary fix)
const navigation = [
  {
    name: 'dashboard',
    path: '/',
    label: 'Dashboard',
    icon: '🏠'
  },
  {
    name: 'automator',
    path: '/automator',
    label: 'Tag Automator',
    icon: '🤖'
  },
  {
    name: 'aliases',
    path: '/aliases',
    label: 'Tag Aliases',
    icon: '🔗'
  },
  {
    name: 'manage',
    path: '/manage',
    label: 'Tag Management',
    icon: '⚙️'
  },
  {
    name: 'validate',
    path: '/validate',
    label: 'Validate Tags',
    icon: '✅'
  },
  {
    name: 'settings',
    path: '/settings',
    label: 'Settings',
    icon: '🔧'
  }
]
</script>

<style scoped>
/* Additional component-specific styles */
</style>
