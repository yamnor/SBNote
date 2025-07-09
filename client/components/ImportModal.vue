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
            <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-lg bg-theme-background border border-theme-border p-6 text-left align-middle shadow-2xl transition-all">
              <DialogTitle
                as="h3"
                class="text-lg font-medium leading-6 text-theme-text mb-4"
              >
                Import Markdown File
              </DialogTitle>
              
              <div class="mt-2">
                <p class="text-sm text-theme-text-muted mb-4">
                  Select a markdown file to import. Frontmatter will be ignored and the content will be imported as a new note.
                </p>
                
                <!-- File Input -->
                <div class="mt-4">
                  <label class="block text-sm font-medium text-theme-text mb-2">
                    Select Markdown File
                  </label>
                  <input
                    ref="fileInput"
                    type="file"
                    accept=".md,.markdown"
                    @change="onFileSelected"
                    class="block w-full text-sm text-theme-text-muted file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-theme-brand file:text-white hover:file:bg-theme-brand-dark file:cursor-pointer cursor-pointer"
                  />
                </div>
                
                <!-- File Info -->
                <div v-if="selectedFile" class="mt-4 p-3 bg-theme-background-subtle rounded-md">
                  <div class="flex items-center justify-between">
                    <div class="flex-1">
                      <p class="text-sm font-medium text-theme-text">{{ selectedFile.name }}</p>
                      <p class="text-xs text-theme-text-muted">{{ formatFileSize(selectedFile.size) }}</p>
                    </div>
                    <button
                      @click="clearFile"
                      class="ml-2 p-1 text-theme-text-muted hover:text-theme-text"
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
                  class="inline-flex justify-center rounded-md border border-transparent bg-theme-background-subtle px-4 py-2 text-sm font-medium text-theme-text hover:bg-theme-background-elevated focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-theme-brand"
                  @click="closeModal"
                >
                  Cancel
                </button>
                
                <button
                  type="button"
                  :disabled="!selectedFile || isImporting"
                  class="inline-flex justify-center rounded-md border border-transparent bg-theme-brand px-4 py-2 text-sm font-medium text-white hover:bg-theme-brand-dark focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-theme-brand disabled:opacity-50 disabled:cursor-not-allowed"
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
import { ref } from 'vue'
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
const errorMessage = ref('');
const isImporting = ref(false);

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
  
  // Validate file type
  if (!file.name.toLowerCase().endsWith('.md') && !file.name.toLowerCase().endsWith('.markdown')) {
    errorMessage.value = 'Please select a markdown file (.md or .markdown)';
    clearFile();
    return;
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
    const content = await readFileContent(selectedFile.value);
    emit("imported", content);
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