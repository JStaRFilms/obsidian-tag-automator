import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'

// Create a simple component for placeholder pages
const PlaceholderPage = {
  template: `
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">{{ title }}</h1>
        <p class="text-secondary-300">{{ description }}</p>
      </div>
      <div class="glass-card">
        <div class="text-center py-12">
          <div class="text-6xl mb-4">{{ icon }}</div>
          <h2 class="text-xl font-semibold text-white mb-2">Coming Soon</h2>
          <p class="text-secondary-300">{{ message }}</p>
        </div>
      </div>
    </div>
  `,
  props: ['title', 'description', 'icon', 'message']
}

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard,
    meta: { title: 'Dashboard' }
  },
  {
    path: '/automator',
    name: 'automator',
    component: PlaceholderPage,
    props: {
      title: 'Tag Automator',
      description: 'Automatically process files with AI-powered tag suggestions',
      icon: '🤖',
      message: 'The new Tag Automator interface is under development.'
    },
    meta: { title: 'Tag Automator' }
  },
  {
    path: '/aliases',
    name: 'aliases',
    component: PlaceholderPage,
    props: {
      title: 'Tag Aliases',
      description: 'Create and manage smart tag aliases',
      icon: '🔗',
      message: 'Tag alias management coming soon.'
    },
    meta: { title: 'Tag Aliases' }
  },
  {
    path: '/manage',
    name: 'manage',
    component: PlaceholderPage,
    props: {
      title: 'Tag Management',
      description: 'Rename, merge, and delete tags across your vault',
      icon: '⚙️',
      message: 'Advanced tag management tools under development.'
    },
    meta: { title: 'Tag Management' }
  },
  {
    path: '/validate',
    name: 'validate',
    component: PlaceholderPage,
    props: {
      title: 'Validate Tags',
      description: 'Check for orphaned, duplicate, and malformed tags',
      icon: '✅',
      message: 'Tag validation system coming soon.'
    },
    meta: { title: 'Validate Tags' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: PlaceholderPage,
    props: {
      title: 'Settings',
      description: 'Configure AI prompts, exclusions, and preferences',
      icon: '🔧',
      message: 'Settings panel under development.'
    },
    meta: { title: 'Settings' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Update page title
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - Obsidian Tag Automator`
  next()
})

export default router
