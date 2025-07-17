<template>
  <div v-if="isVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Tag Configuration
        </h2>
        <button
          @click="closeModal"
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-6">
        <!-- Tag Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select Tag
          </label>
          <select
            v-model="selectedTag"
            @change="onTagChange"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-color-primary focus:border-transparent"
          >
            <option value="">Select a tag...</option>
            <option
              v-for="tag in availableTags"
              :key="tag.tag"
              :value="tag.tag"
              :disabled="tag.tag === '_untagged'"
            >
              {{ tag.tag }} ({{ tag.count }} notes)
            </option>
          </select>
        </div>

        <!-- Tag Name Edit -->
        <div v-if="selectedTag && selectedTag !== '_untagged'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Tag Name
          </label>
          <input
            v-model="newTagName"
            @input="validateTagName"
            type="text"
            class="w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-color-primary focus:border-transparent"
            :class="tagNameError ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'"
            placeholder="Enter new tag name..."
          />
          <div v-if="tagNameError" class="text-red-600 dark:text-red-400 text-sm mt-1">
            {{ tagNameError }}
          </div>
        </div>

        <!-- Priority -->
        <div v-if="selectedTag && selectedTag !== '_untagged'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Priority (1-5)
          </label>
          <div class="flex items-center space-x-2">
            <div class="flex space-x-1">
              <button
                v-for="star in 5"
                :key="star"
                @click="priority = star"
                class="text-2xl transition-colors"
                :class="star <= priority ? 'text-color-primary' : 'text-gray-300 dark:text-gray-600'"
              >
                ★
              </button>
            </div>
            <span class="text-sm text-gray-600 dark:text-gray-400 ml-2">
              {{ priority }}/5
            </span>
          </div>
        </div>

        <!-- Description -->
        <div v-if="selectedTag && selectedTag !== '_untagged'">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Description
          </label>
          <textarea
            v-model="description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-color-primary focus:border-transparent resize-none"
            placeholder="Enter tag description..."
          ></textarea>
        </div>

        <!-- Pin Toggle -->
        <div v-if="selectedTag && selectedTag !== '_untagged'">
          <label class="flex items-center space-x-2">
            <input
              v-model="isPinned"
              type="checkbox"
              class="rounded border-gray-300 dark:border-gray-600 text-color-primary focus:ring-color-primary"
            />
            <div class="flex items-center space-x-2">
              <svg class="w-4 h-4 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"/>
              </svg>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Pin this tag
              </span>
            </div>
          </label>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-6">
            Pinned tags appear at the top of the tag list
          </p>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="text-red-600 dark:text-red-400 text-sm">
          {{ errorMessage }}
        </div>

        <!-- Success Message -->
        <div v-if="successMessage" class="text-green-600 dark:text-green-400 text-sm">
          {{ successMessage }}
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-between items-center p-6 border-t border-gray-200 dark:border-gray-700">
        <!-- Left side - Delete button -->
        <button
          v-if="selectedTag && selectedTag !== '_untagged'"
          @click="handleDeleteTag"
          class="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-md hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
        >
          Delete Tag
        </button>
        
        <!-- Right side - Cancel and Save buttons -->
        <div class="flex space-x-3">
          <button
            @click="closeModal"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
          <button
            v-if="selectedTag && selectedTag !== '_untagged'"
            @click="saveConfig"
            :disabled="isSaving"
            class="px-4 py-2 text-sm font-medium text-white bg-color-primary rounded-md hover:bg-color-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {{ isSaving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <div v-if="showConfirmDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-sm w-full mx-4">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Confirm Action
          </h3>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            {{ confirmMessage }}
          </p>
          <div class="flex justify-end space-x-3">
            <button
              @click="cancelConfirm"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              @click="confirmAction"
              class="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors"
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue';
import { X } from 'lucide-vue-next';
import { getTagsWithCounts, updateTagConfig, deleteTagConfig, renameTag, deleteTag } from '../lib/api.js';
import { useGlobalStore } from '../lib/globalStore.js';

const props = defineProps({
  isVisible: {
    type: Boolean,
    default: false
  },
  selectedTagData: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

const globalStore = useGlobalStore();

// Reactive data
const selectedTag = ref('');
const newTagName = ref('');
const priority = ref(3);
const description = ref('');
const isPinned = ref(false);
const availableTags = ref([]);
const errorMessage = ref('');
const successMessage = ref('');
const isSaving = ref(false);
const showConfirmDialog = ref(false);
const confirmMessage = ref('');
const pendingAction = ref(null);
const tagNameError = ref('');

// Load available tags
async function loadTags() {
  try {
    availableTags.value = await getTagsWithCounts();
  } catch (error) {
    console.error('Failed to load tags:', error);
    errorMessage.value = 'Failed to load tags';
  }
}

// Tag change handler
function onTagChange() {
  if (selectedTag.value && selectedTag.value !== '_untagged') {
    // Load existing config for the selected tag
    loadTagConfig(selectedTag.value);
    // Set new tag name to current tag name
    newTagName.value = selectedTag.value;
  } else {
    // Reset form
    priority.value = 3;
    description.value = '';
    isPinned.value = false;
    newTagName.value = '';
  }
  errorMessage.value = '';
  successMessage.value = '';
  tagNameError.value = '';
}

// Load tag configuration
async function loadTagConfig(tagName) {
  try {
    // Find the tag data from available tags
    const tagData = availableTags.value.find(tag => tag.tag === tagName);
    if (tagData) {
      priority.value = tagData.priority || 3;
      description.value = tagData.description || '';
      isPinned.value = tagData.is_pinned || false;
    } else {
      // Use default values if tag data not found
      priority.value = 3;
      description.value = '';
      isPinned.value = false;
    }
    newTagName.value = tagName;
  } catch (error) {
    console.error('Failed to load tag config:', error);
  }
}

// Validate tag name
function validateTagName() {
  const tagName = newTagName.value.trim();
  
  // Check for empty or whitespace-only
  if (!tagName) {
    tagNameError.value = 'Tag name cannot be empty';
    return false;
  }
  
  // Check for special characters and spaces
  const invalidChars = /[^\w\-_]/;
  if (invalidChars.test(tagName)) {
    tagNameError.value = 'Tag name can only contain letters, numbers, hyphens, and underscores';
    return false;
  }
  
  // Check for duplicate tag names (excluding current tag)
  const existingTag = availableTags.value.find(tag => 
    tag.tag === tagName && tag.tag !== selectedTag.value
  );
  if (existingTag) {
    tagNameError.value = 'A tag with this name already exists';
    return false;
  }
  
  tagNameError.value = '';
  return true;
}

// Save configuration
async function saveConfig() {
  if (!selectedTag.value || selectedTag.value === '_untagged') {
    return;
  }

  // Validate priority
  if (priority.value < 1 || priority.value > 5) {
    errorMessage.value = 'Priority must be between 1 and 5';
    return;
  }

  // Validate tag name if it has changed
  const hasTagNameChanged = newTagName.value.trim() !== selectedTag.value;
  if (hasTagNameChanged && !validateTagName()) {
    return;
  }

  isSaving.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    // If tag name has changed, rename the tag first
    if (hasTagNameChanged) {
      await renameTag(selectedTag.value, newTagName.value.trim());
    }

    // Update tag configuration
    await updateTagConfig(hasTagNameChanged ? newTagName.value.trim() : selectedTag.value, {
      priority: priority.value,
      description: description.value,
      is_pinned: isPinned.value
    });

    successMessage.value = hasTagNameChanged ? 
      `Tag renamed to "${newTagName.value.trim()}" and configuration saved successfully` : 
      'Tag configuration saved successfully';
    
    emit('saved');
    
    // Close modal on success
    closeModal();
  } catch (error) {
    console.error('Failed to save tag config:', error);
    errorMessage.value = error.response?.data?.detail || 'Failed to save tag configuration';
  } finally {
    isSaving.value = false;
  }
}

// Delete tag
function handleDeleteTag() {
  if (!selectedTag.value || selectedTag.value === '_untagged') {
    return;
  }

  confirmMessage.value = `Are you sure you want to delete the tag "${selectedTag.value}"? This will remove the tag from all notes and cannot be undone.`;
  pendingAction.value = 'delete';
  showConfirmDialog.value = true;
}

// Confirm action
async function confirmAction() {
  if (pendingAction.value === 'delete') {
    try {
      await deleteTag(selectedTag.value);
      successMessage.value = 'Tag deleted successfully';
      emit('saved');
      
      // Close modal on success
      closeModal();
    } catch (error) {
      console.error('Failed to delete tag:', error);
      errorMessage.value = error.response?.data?.detail || 'Failed to delete tag';
    }
  }
  
  showConfirmDialog.value = false;
  pendingAction.value = null;
}

// Cancel confirmation
function cancelConfirm() {
  showConfirmDialog.value = false;
  pendingAction.value = null;
}

// Close modal
function closeModal() {
  emit('close');
  selectedTag.value = '';
  newTagName.value = '';
  priority.value = 3;
  description.value = '';
  isPinned.value = false;
  errorMessage.value = '';
  successMessage.value = '';
  tagNameError.value = '';
}

// Watch for visibility changes
watch(() => props.isVisible, (newValue) => {
  if (newValue) {
    loadTags();
    // If we have selected tag data, set it
    if (props.selectedTagData) {
      selectedTag.value = props.selectedTagData.tag;
      newTagName.value = props.selectedTagData.tag;
      priority.value = props.selectedTagData.priority || 3;
      description.value = props.selectedTagData.description || '';
      isPinned.value = props.selectedTagData.is_pinned || false;
    }
  }
});

// Load tags on mount
onMounted(() => {
  if (props.isVisible) {
    loadTags();
  }
});
</script> 