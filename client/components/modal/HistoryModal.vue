<template>
  <div v-if="isVisible" class="fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <!-- Background overlay -->
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="closeModal"></div>

      <!-- Modal panel -->
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
        <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
          <div class="sm:flex sm:items-start">
            <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                History - {{ noteTitle }}
              </h3>
              
              <!-- Loading state -->
              <div v-if="loading" class="flex justify-center items-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span class="ml-2 text-gray-600">Loading history...</span>
              </div>
              
              <!-- History list -->
              <div v-else-if="historyEntries.length > 0" class="space-y-3 max-h-96 overflow-y-auto">
                <div 
                  v-for="entry in historyEntries" 
                  :key="entry.commit_hash"
                  class="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900">{{ entry.message }}</div>
                    <div class="text-xs text-gray-500 mt-1">
                      {{ formatTime(entry.date) }} | {{ entry.commit_hash.substring(0, 8) }}
                    </div>
                  </div>
                  
                  <div class="flex space-x-2 ml-4">
                    <button 
                      @click="previewVersion(entry.commit_hash)"
                      class="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                    >
                      Preview
                    </button>
                    <button 
                      @click="restoreVersion(entry.commit_hash)"
                      class="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                    >
                      Restore
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Empty state -->
              <div v-else class="text-center py-8 text-gray-500">
                No history available
              </div>
            </div>
          </div>
        </div>
        
        <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
          <button
            type="button"
            @click="closeModal"
            class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-gray-600 text-base font-medium text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 sm:ml-3 sm:w-auto sm:text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Preview Modal -->
  <HistoryPreviewModal 
    v-model="showPreviewModal"
    :content="previewContent"
    :title="previewTitle"
    @restore="restoreFromPreview"
  />
  
  <!-- Restore Confirmation Modal -->
  <ConfirmModal
    v-model="showRestoreConfirm"
    title="Confirm Restore"
    :message="`Are you sure you want to restore this version?\nCurrent changes will be lost.`"
    confirm-button-text="Restore"
    confirm-button-style="danger"
    @confirm="confirmRestore"
  />
</template>

<script setup>
import { ref, watch } from 'vue';
import { getNoteHistory, getNoteVersion, restoreNoteVersion } from '../../lib/api.js';
import HistoryPreviewModal from './HistoryPreviewModal.vue';
import ConfirmModal from './ConfirmModal.vue';

const props = defineProps({
  modelValue: Boolean,
  filename: String,
  noteTitle: String
});

const emit = defineEmits(['update:modelValue']);

const isVisible = ref(false);
const loading = ref(false);
const historyEntries = ref([]);
const showPreviewModal = ref(false);
const showRestoreConfirm = ref(false);
const previewContent = ref('');
const previewTitle = ref('');
const pendingRestoreHash = ref('');

watch(() => props.modelValue, (newVal) => {
  isVisible.value = newVal;
  if (newVal) {
    loadHistory();
  }
});

watch(isVisible, (newVal) => {
  emit('update:modelValue', newVal);
});

async function loadHistory() {
  if (!props.filename) return;
  
  loading.value = true;
  try {
    historyEntries.value = await getNoteHistory(props.filename);
  } catch (error) {
    console.error('Failed to load history:', error);
    historyEntries.value = [];
  } finally {
    loading.value = false;
  }
}

async function previewVersion(commitHash) {
  try {
    const content = await getNoteVersion(props.filename, commitHash);
    previewContent.value = content;
    previewTitle.value = `Preview - ${props.noteTitle}`;
    pendingRestoreHash.value = commitHash;
    showPreviewModal.value = true;
  } catch (error) {
    console.error('Failed to preview version:', error);
  }
}

function restoreVersion(commitHash) {
  pendingRestoreHash.value = commitHash;
  showRestoreConfirm.value = true;
}

async function confirmRestore() {
  try {
    await restoreNoteVersion(props.filename, pendingRestoreHash.value);
    showRestoreConfirm.value = false;
    isVisible.value = false;
    // Reload the note
    window.location.reload();
  } catch (error) {
    console.error('Failed to restore version:', error);
  }
}

function restoreFromPreview() {
  restoreVersion(pendingRestoreHash.value);
}

function closeModal() {
  isVisible.value = false;
}

function formatTime(dateString) {
  return new Date(dateString).toLocaleString('en-US');
}
</script> 