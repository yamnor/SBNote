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
          Paste Text
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
        <form @submit.prevent="createPasteNote">
          <!-- Text Input -->
          <div class="mb-4">
            <label for="text" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Text Content *
            </label>
            <textarea
              id="text"
              ref="textArea"
              v-model="text"
              rows="10"
              placeholder="Enter your text content here..."
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white resize-none"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': textError }"
              @input="validateText"
              @blur="validateText"
            ></textarea>
            <p v-if="textError" class="mt-1 text-sm text-red-600 dark:text-red-400">
              {{ textError }}
            </p>
          </div>
          
          <!-- Extension Input -->
          <div class="mb-4">
            <label for="extension" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              File Extension *
            </label>
            <input
              id="extension"
              v-model="extension"
              type="text"
              placeholder="txt"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              :class="{ 'border-red-500 focus:ring-red-500 focus:border-red-500': extensionError }"
              @input="validateExtension"
              @blur="validateExtension"
            />
            <p v-if="extensionError" class="mt-1 text-sm text-red-600 dark:text-red-400">
              {{ extensionError }}
            </p>
          </div>
          
          <!-- Category Selection -->
          <div class="mb-4">
            <label for="category" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Category *
            </label>
            <select
              id="category"
              v-model="category"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="plaintext">Plaintext</option>
              <option value="coordinate">Coordinate</option>
            </select>
          </div>
          
          <!-- Tags Input -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tags
            </label>
            <TagInput 
              v-model="tags"
              :readonly="false"
            />
          </div>
          
          <!-- Error Message -->
          <div v-if="error" class="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
          </div>
          
          <!-- Loading State -->
          <div v-if="isLoading" class="mb-4 flex items-center justify-center">
            <Loader2 class="w-5 h-5 animate-spin text-blue-500 mr-2" />
            <span class="text-sm text-gray-600 dark:text-gray-400">Creating note...</span>
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
              :disabled="isLoading || !isValidForm"
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
import { ref, computed, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { X, Loader2 } from 'lucide-vue-next';
import { importPaste } from '../api.js';
import TagInput from './TagInput.vue';

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  selectedTag: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['close']);

const router = useRouter();

// State
const textArea = ref();
const text = ref('');
const extension = ref('');
const category = ref('plaintext');
const tags = ref([]);
const textError = ref('');
const extensionError = ref('');
const error = ref('');
const isLoading = ref(false);

// Computed
const isValidForm = computed(() => {
  return text.value.trim() !== '' && 
         extension.value.trim() !== '' && 
         !textError.value && 
         !extensionError.value;
});

// Methods
function validateText() {
  const trimmedText = text.value.trim();
  
  if (!trimmedText) {
    textError.value = 'Text content is required';
    return false;
  }
  
  textError.value = '';
  return true;
}

function validateExtension() {
  const trimmedExtension = extension.value.trim();
  
  if (!trimmedExtension) {
    extensionError.value = 'File extension is required';
    return false;
  }
  
  // Basic validation for extension
  if (!/^[a-zA-Z0-9]+$/.test(trimmedExtension)) {
    extensionError.value = 'Extension can only contain letters and numbers';
    return false;
  }
  
  if (trimmedExtension.length > 10) {
    extensionError.value = 'Extension is too long (max 10 characters)';
    return false;
  }
  
  extensionError.value = '';
  return true;
}

function createTextFile() {
  const textContent = text.value;
  const extensionValue = extension.value.trim();
  
  // Generate random filename (8 characters, alphanumeric)
  const generateRandomFilename = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };
  
  const randomName = generateRandomFilename();
  const filename = `${randomName}.${extensionValue}`;
  
  // Create a Blob with the text content
  const blob = new Blob([textContent], { type: 'text/plain' });
  
  // Create a File object with the random filename and specified extension
  return new File([blob], filename, { type: 'text/plain' });
}

async function createPasteNote() {
  if (!validateText() || !validateExtension()) {
    return;
  }
  
  try {
    isLoading.value = true;
    error.value = '';
    
    // Create text file from input
    const textFile = createTextFile();
    
    // Create note via API with category information
    const createdNote = await importPaste(textFile, tags.value, category.value);
    
    // Close modal
    closeModal();
    
    // Navigate to the created note
    router.push({ name: 'note', params: { filename: createdNote.filename } });
    
  } catch (err) {
    console.error('Failed to create paste note:', err);
    error.value = err.message || 'Failed to create note. Please try again.';
  } finally {
    isLoading.value = false;
  }
}

function closeModal() {
  // Reset form
  text.value = '';
  extension.value = '';
  category.value = 'plaintext';
  tags.value = [];
  textError.value = '';
  extensionError.value = '';
  error.value = '';
  isLoading.value = false;
  
  emit('close');
}

// Watch for visibility changes
watch(() => props.isVisible, (newValue) => {
  if (!newValue) {
    closeModal();
  } else {
    // Focus on textarea when modal becomes visible
    nextTick(() => {
      if (textArea.value) {
        textArea.value.focus();
      }
    });
  }
});

// Watch for selected tag prop
watch(() => props.selectedTag, (newValue) => {
  if (newValue && !tags.value.includes(newValue)) {
    tags.value = [...tags.value, newValue];
  }
}, { immediate: true });
</script> 