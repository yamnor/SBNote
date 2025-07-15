<template>
  <div v-if="isVisible" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div 
      class="absolute inset-0 bg-black bg-opacity-50"
      @click="closeModal"
    ></div>
    
    <!-- Modal -->
    <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Embed Page
        </h2>
        <button
          @click="closeModal"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Content -->
      <div class="p-6">
        <form @submit.prevent="createEmbedNote">
          <!-- URL Input -->
          <div class="mb-4">
            <label for="url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              URL
            </label>
            <input
              id="url"
              v-model="url"
              type="url"
                            placeholder="https://example.com"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': urlError }"
              @input="validateUrl"
              @blur="validateUrl"
                            />
              <p v-if="urlError" class="mt-1 text-sm text-red-600 dark:text-red-400">
                {{ urlError }}
              </p>
            </div>
          
          <!-- Error Message -->
          <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
          </div>
          
          <!-- Loading State -->
          <div v-if="isLoading" class="mb-4 flex items-center justify-center">
            <Loader2 class="w-5 h-5 animate-spin text-blue-500 mr-2" />
            <span class="text-sm text-gray-600 dark:text-gray-400">Getting page title and creating note...</span>
          </div>
          
          <!-- Buttons -->
          <div class="flex justify-end space-x-3">
            <button
              type="button"
              @click="closeModal"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              :disabled="isLoading"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="isLoading || !isValidUrl"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { X, Loader2 } from 'lucide-vue-next';
import { createNote } from '../../lib/api.js';

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['close']);

const router = useRouter();

// State
const url = ref('');
const urlError = ref('');
const error = ref('');
const isLoading = ref(false);

// Computed
const isValidUrl = computed(() => {
  return url.value.trim() !== '' && !urlError.value;
});

// Methods
async function getPageTitle(url) {
  try {
    const response = await fetch(url, {
      method: 'GET',
      mode: 'cors',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; SBNote/1.0)'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch page');
    }
    
    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    let title = doc.title;
    if (!title || title.trim() === '') {
      // titleタグがない場合、h1タグを試す
      const h1 = doc.querySelector('h1');
      title = h1 ? h1.textContent.trim() : 'Untitled';
    }
    
    return title || 'Untitled';
  } catch (error) {
    console.warn('Failed to get page title:', error);
    return 'Untitled';
  }
}

function validateUrl() {
  const trimmedUrl = url.value.trim();
  
  if (!trimmedUrl) {
    urlError.value = 'URL is required';
    return false;
  }
  
  try {
    const urlObj = new URL(trimmedUrl);
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      urlError.value = 'Only HTTP and HTTPS URLs are supported';
      return false;
    }
    urlError.value = '';
    return true;
  } catch (err) {
    urlError.value = 'Please enter a valid URL';
    return false;
  }
}

async function createEmbedNote() {
  if (!validateUrl()) {
    return;
  }
  
  try {
    isLoading.value = true;
    error.value = '';
    
    // Get page title from URL
    const pageTitle = await getPageTitle(url.value.trim());
    
    // Create note content
    const noteContent = `${pageTitle}

[Link](${url.value.trim()})`;
    
    // Create note via API with embed category
    const createdNote = await createNote(pageTitle, noteContent, [], 'embed', 'private');
    
    // Close modal
    closeModal();
    
    // Navigate to the created note
    router.push({ name: 'note', params: { filename: createdNote.filename } });
    
  } catch (err) {
    console.error('Failed to create embed note:', err);
    error.value = err.message || 'Failed to create note. Please try again.';
  } finally {
    isLoading.value = false;
  }
}

function closeModal() {
  // Reset form
  url.value = '';
  urlError.value = '';
  error.value = '';
  isLoading.value = false;
  
  emit('close');
}

// Watch for visibility changes
watch(() => props.isVisible, (newValue) => {
  if (!newValue) {
    closeModal();
  }
});
</script> 