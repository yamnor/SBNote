<template>
  <TransitionRoot appear :show="isVisible" as="template">
    <Dialog as="div" @close="closeModal" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-lg bg-color-bg-neutral border border-color-border-primary p-6 text-left align-middle shadow-2xl transition-all">
              <DialogTitle
                as="h3"
                class="text-lg font-medium leading-6 text-color-text-primary mb-4"
              >
                Import File
              </DialogTitle>
              
              <div class="mt-2">
                
                <!-- File Type Selection -->
                <div class="mt-4">
                  <label class="block text-sm font-medium text-color-text-primary mb-2">
                    File Type
                  </label>
                  <select 
                    v-model="selectedFileType"
                    class="w-full px-3 py-2 border border-color-border-primary rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-color-primary focus:border-color-primary bg-color-bg-base text-color-text-primary"
                  >
                    <option value="markdown">Markdown</option>
                    <option value="image">Image (JPEG/PNG)</option>
                    <option value="coordinate">Coordinate File</option>
                    <option value="output">Output</option>
                  </select>
                </div>
                
                <!-- File Input -->
                <div class="mt-4">
                  <label class="block text-sm font-medium text-color-text-primary mb-2">
                    Select File
                  </label>
                  <input
                    ref="fileInput"
                    type="file"
                    :accept="fileTypeAccept"
                    @change="onFileSelected"
                    class="block w-full text-sm text-color-text-primary border border-color-border-primary rounded-lg cursor-pointer bg-color-bg-base focus:outline-none file:border-0 file:bg-transparent file:text-sm file:font-medium file:bg-color-button-primary-bg file:text-color-button-primary-fg hover:file:bg-color-button-primary-hover-bg file:cursor-pointer cursor-pointer"
                  />
                </div>
                
                <!-- File Info -->
                <div v-if="selectedFile" class="mt-4 p-3 bg-color-bg-subtle rounded-md">
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <p class="text-sm font-medium text-color-text-primary">{{ selectedFile.name }}</p>
                      <p class="text-xs text-color-text-secondary">{{ formatFileSize(selectedFile.size) }}</p>
                    </div>
                    <button
                      @click="clearFile"
                      class="ml-2 p-1 text-color-text-secondary hover:text-color-text-primary"
                      title="Remove file"
                    >
                      <X class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <!-- Error Message -->
                <div v-if="errorMessage" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p class="text-sm text-red-600">{{ errorMessage }}</p>
                </div>
              </div>

              <div class="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  class="inline-flex justify-center rounded-md border border-transparent bg-color-button-secondary-grayed-bg px-4 py-2 text-sm font-medium text-color-button-secondary-grayed-fg hover:bg-color-button-secondary-grayed-hover-bg focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-color-primary"
                  @click="closeModal"
                >
                  Cancel
                </button>
                
                <button
                  type="button"
                  :disabled="!selectedFile || isImporting"
                  class="inline-flex justify-center rounded-md border border-transparent bg-color-button-primary-bg px-4 py-2 text-sm font-medium text-color-button-primary-fg hover:bg-color-button-primary-hover-bg focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-color-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  @click="importFile"
                >
                  <Loader2 v-if="isImporting" class="w-4 h-4 mr-2 animate-spin" />
                  {{ isImporting ? 'Importing...' : 'Import' }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue'
import { ref, computed } from 'vue'
import { X, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  selectedTag: {
    type: String,
    default: null
  }
});

const emit = defineEmits(["close", "imported"]);
const isVisible = defineModel({ type: Boolean });

const fileInput = ref();
const selectedFile = ref(null);
const selectedFileType = ref('markdown');
const errorMessage = ref('');
const isImporting = ref(false);

// Computed property for file input accept attribute
const fileTypeAccept = computed(() => {
  if (selectedFileType.value === 'markdown') {
    return '.md,.markdown';
  } else if (selectedFileType.value === 'image') {
    return '.jpg,.jpeg,.png';
  } else if (selectedFileType.value === 'coordinate') {
    return '.xyz';
  } else if (selectedFileType.value === 'output') {
    return ''; // Accept any file type for output
  }
  return '';
});

function closeModal() {
  isVisible.value = false;
  clearFile();
  emit("close");
}

function onFileSelected(event) {
  const file = event.target.files[0];
  if (!file) {
    clearFile();
    return;
  }
  
  // Validate file type based on selected file type
  if (selectedFileType.value === 'markdown') {
    if (!file.name.toLowerCase().endsWith('.md') && !file.name.toLowerCase().endsWith('.markdown')) {
      errorMessage.value = 'Please select a markdown file (.md or .markdown)';
      clearFile();
      return;
    }
  } else if (selectedFileType.value === 'image') {
    const validImageExtensions = ['.jpg', '.jpeg', '.png'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    if (!validImageExtensions.includes(fileExtension)) {
      errorMessage.value = 'Please select an image file (.jpg, .jpeg, or .png)';
      clearFile();
      return;
    }
  } else if (selectedFileType.value === 'coordinate') {
    if (!file.name.toLowerCase().endsWith('.xyz')) {
      errorMessage.value = 'Please select a coordinate file (.xyz)';
      clearFile();
      return;
    }
  } else if (selectedFileType.value === 'output') {
    // No file extension validation for output - accept any file
  }
  
  // Validate file size (10MB limit)
  if (file.size > 10 * 1024 * 1024) {
    errorMessage.value = 'File size must be less than 10MB';
    clearFile();
    return;
  }
  
  selectedFile.value = file;
  errorMessage.value = '';
}

function clearFile() {
  selectedFile.value = null;
  errorMessage.value = '';
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function importFile() {
  if (!selectedFile.value) return;
  
  isImporting.value = true;
  errorMessage.value = '';
  
  try {
    if (selectedFileType.value === 'markdown') {
      const content = await readFileContent(selectedFile.value);
      emit("imported", { type: 'markdown', content });
    } else if (selectedFileType.value === 'image') {
      emit("imported", { type: 'image', file: selectedFile.value });
    } else if (selectedFileType.value === 'coordinate') {
      emit("imported", { type: 'coordinate', file: selectedFile.value });
    } else if (selectedFileType.value === 'output') {
      emit("imported", { type: 'output', file: selectedFile.value });
    }
    closeModal();
  } catch (error) {
    console.error('Import failed:', error);
    errorMessage.value = 'Failed to read file. Please try again.';
  } finally {
    isImporting.value = false;
  }
}

function readFileContent(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        resolve(content);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}
</script> 