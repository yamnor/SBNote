<template>
  <div class="tag-input-container">
    <div class="tags-display">
      <div
        v-for="(tag, index) in tags"
        :key="index"
        class="tag-chip"
      >
        <router-link
          :to="{ name: 'tag', params: { tagName: tag } }"
          class="tag-link"
        >
          {{ tag }}
        </router-link>
        <button
          v-if="!readonly"
          @click="(event) => removeTag(index, event)"
          class="remove-tag"
          type="button"
          title="Remove tag"
        >
          ×
        </button>
      </div>
      <!-- Show message when no tags in readonly mode -->
      <div v-if="readonly && (!tags || tags.length === 0)" class="text-sm text-gray-500 italic">
        No tags
      </div>
    </div>
    <div v-if="!readonly" class="input-container">
      <input
        ref="input"
        v-model="inputValue"
        @keydown="handleKeydown"
        @compositionstart="handleCompositionStart"
        @compositionend="handleCompositionEnd"
        @blur="handleBlur"
        @input="handleInput"
        class="tag-input"
        placeholder="Enter tags..."
        type="text"
      />
      <!-- Autocomplete dropdown -->
      <div
        v-if="showSuggestions && filteredSuggestions.length > 0"
        class="suggestions-dropdown"
      >
        <div
          v-for="(suggestion, index) in filteredSuggestions"
          :key="suggestion"
          @click="selectSuggestion(suggestion)"
          @mouseenter="selectedIndex = index"
          class="suggestion-item"
          :class="{ 'selected': index === selectedIndex }"
        >
          {{ suggestion }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTags } from '../api.js'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'tagConfirmed'])

const tags = ref([...props.modelValue])
const inputValue = ref('')
const input = ref()
const router = useRouter()
const isComposing = ref(false)

// Autocomplete state
const allTags = ref([])
const showSuggestions = ref(false)
const selectedIndex = ref(-1)
const searchTimeout = ref(null)

// Watch for changes from parent component
watch(() => props.modelValue, (newValue) => {
  tags.value = [...newValue]
}, { deep: true })

// Filtered suggestions based on input
const filteredSuggestions = computed(() => {
  if (!inputValue.value || inputValue.value.length < 1) {
    return []
  }
  
  const input = inputValue.value.toLowerCase()
  const availableTags = allTags.value.filter(tag => !tags.value.includes(tag))
  
  return availableTags
    .filter(tag => tag.toLowerCase().includes(input))
    .slice(0, 10) // Limit to 10 suggestions
})

// Load all available tags
async function loadTags() {
  try {
    const tags = await getTags()
    // Filter out "_untagged" tag from suggestions since it's automatically applied
    allTags.value = tags.filter(tag => tag !== "_untagged")
  } catch (error) {
    console.error('Failed to load tags:', error)
    allTags.value = []
  }
}

// Handle input changes with debounce
function handleInput() {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
  
  searchTimeout.value = setTimeout(() => {
    if (inputValue.value && inputValue.value.length >= 1) {
      showSuggestions.value = true
      selectedIndex.value = -1
    } else {
      showSuggestions.value = false
    }
  }, 100)
}

// Select a suggestion
function selectSuggestion(suggestion) {
  inputValue.value = suggestion
  showSuggestions.value = false
  addTag()
}

// Hide suggestions
function hideSuggestions() {
  setTimeout(() => {
    showSuggestions.value = false
    selectedIndex.value = -1
  }, 150)
}

// Add tag
function addTag() {
  const tag = inputValue.value.trim()
  
  if (tag && !tags.value.includes(tag)) {
    tags.value.push(tag)
    emit('update:modelValue', [...tags.value])
    emit('tagConfirmed') // Notify that tag is confirmed
  }
  
  inputValue.value = ''
}

// Handle tag input completion (on blur)
function handleBlur() {
  if (inputValue.value.trim()) {
    addTag()
  }
  hideSuggestions()
}

// Remove tag
function removeTag(index, event) {
  event.preventDefault()
  event.stopPropagation()
  tags.value.splice(index, 1)
  emit('update:modelValue', [...tags.value])
  emit('tagConfirmed') // Notify that tag is removed
}

// Handle keyboard events
function handleKeydown(event) {
  if (event.key === 'Enter') {
    // Don't confirm tag while IME is composing
    if (isComposing.value) {
      return
    }
    event.preventDefault()
    
    // If suggestions are shown and an item is selected, select it
    if (showSuggestions.value && selectedIndex.value >= 0 && filteredSuggestions.value[selectedIndex.value]) {
      selectSuggestion(filteredSuggestions.value[selectedIndex.value])
    } else {
      addTag()
    }
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (showSuggestions.value && filteredSuggestions.value.length > 0) {
      selectedIndex.value = Math.min(selectedIndex.value + 1, filteredSuggestions.value.length - 1)
    }
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    if (showSuggestions.value && filteredSuggestions.value.length > 0) {
      selectedIndex.value = Math.max(selectedIndex.value - 1, -1)
    }
  } else if (event.key === 'Escape') {
    event.preventDefault()
    showSuggestions.value = false
    selectedIndex.value = -1
  } else if (event.key === 'Backspace' && inputValue.value === '' && tags.value.length > 0) {
    event.preventDefault()
    removeTag(tags.value.length - 1, event)
  } else if (event.key === ',') {
    // Don't confirm tag while IME is composing
    if (isComposing.value) {
      return
    }
    event.preventDefault()
    addTag()
  }
}

// IME確定開始
function handleCompositionStart() {
  isComposing.value = true
}

// IME確定終了
function handleCompositionEnd() {
  isComposing.value = false
}

// Load tags on mount
onMounted(() => {
  loadTags()
})
</script>

<style scoped>
.tag-input-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background-color: var(--theme-background-surface);
  min-height: 2.5rem;
  align-items: flex-start;
}

.tags-display {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: transparent;
  color: var(--theme-brand);
  border: 1px solid var(--theme-border);
  border-radius: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.tag-chip:hover {
  background-color: var(--theme-brand);
  color: var(--theme-background-surface);
}

.tag-link {
  color: inherit;
  text-decoration: none;
}

.tag-link:hover {
  text-decoration: none;
}

.remove-tag {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  padding: 0;
  margin-left: 0.25rem;
  line-height: 1;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.remove-tag:hover {
  opacity: 1;
}

.input-container {
  position: relative;
  flex: 1;
  min-width: 120px;
}

.tag-input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.875rem;
  color: var(--theme-text);
}

.tag-input::placeholder {
  color: var(--theme-text-muted);
}

.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: var(--theme-background);
  border: 1px solid var(--theme-border);
  border-radius: 0.375rem;
  box-shadow: var(--theme-shadow-md);
  z-index: 50;
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 10px;
}

.suggestion-item {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--theme-text);
  transition: background-color 0.15s ease;
}

.suggestion-item:hover,
.suggestion-item.selected {
  background-color: var(--theme-background-elevated);
}

.suggestion-item:first-child {
  border-top-left-radius: 0.375rem;
  border-top-right-radius: 0.375rem;
}

.suggestion-item:last-child {
  border-bottom-left-radius: 0.375rem;
  border-bottom-right-radius: 0.375rem;
}
</style> 