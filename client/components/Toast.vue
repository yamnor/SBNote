<template>
  <TransitionGroup
    tag="div"
    enter-active-class="transition ease-out duration-300"
    enter-from-class="transform translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
    enter-to-class="transform translate-y-0 opacity-100 sm:translate-x-0"
    leave-active-class="transition ease-in duration-100"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
    class="fixed top-4 right-4 z-toast space-y-2"
    style="z-index: 55;"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="w-96 bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden"
    >
      <div class="p-4">
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <CheckCircle
              v-if="toast.severity === 'success'"
              class="h-6 w-6 text-green-400"
            />
            <AlertTriangle
              v-else-if="toast.severity === 'error'"
              class="h-6 w-6 text-red-400"
            />
            <Info
              v-else
              class="h-6 w-6 text-blue-400"
            />
          </div>
          <div class="ml-3 w-0 flex-1 pt-0.5">
            <p class="text-sm font-medium text-gray-900">
              {{ toast.title }}
            </p>
            <p class="mt-1 text-sm text-gray-500">
              {{ toast.description }}
            </p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button
              @click="removeToast(toast.id)"
              class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <span class="sr-only">Close</span>
              <X class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </TransitionGroup>
</template>

<script setup>
import { ref } from 'vue'
import { CheckCircle, AlertTriangle, Info, X } from 'lucide-vue-next'

const toasts = ref([])
let nextId = 1

const addToast = (description, title = '', severity = 'info') => {
  const id = nextId++
  const toast = {
    id,
    description,
    title,
    severity
  }
  toasts.value.push(toast)
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    removeToast(id)
  }, 5000)
}

const removeToast = (id) => {
  const index = toasts.value.findIndex(toast => toast.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

// Expose methods
defineExpose({
  addToast
})
</script> 