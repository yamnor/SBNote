<template>
  <div 
    ref="cardElement"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    class="p-2 cursor-pointer transition-all duration-300 group hover:shadow-lg h-36 w-full flex flex-col border shadow-sm relative"
    :class="[getBackgroundClass(), { 'pin-animation': isPinned }]"
    style="touch-action: manipulation;"
  >
    <!-- Corner triangle for pinned tags in top-right -->
    <div 
      v-if="isPinned"
      class="absolute top-0 right-0 w-0 h-0 border-l-[20px] border-l-transparent border-t-[20px] border-t-theme-brand"
    >
    </div>
    
    <!-- Recent note modification indicator in bottom-left corner -->
    <div v-if="hasRecentlyModifiedNote" class="absolute bottom-1 left-1">
      <div class="w-2 h-2 rounded-full" style="background-color: var(--theme-brand-accent);"></div>
    </div>
    
    <!-- Note count badge in bottom-right corner -->
    <div class="absolute bottom-1 right-1">
      <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-medium rounded"
            :class="isSelected ? 'bg-white text-theme-brand' : 'bg-theme-brand text-white'">
        {{ tagData.count }}
      </span>
    </div>
    
    <!-- Centered tag name -->
    <div class="flex-1 flex items-center justify-center min-w-0">
      <h3 class="text-sm font-medium transition-colors leading-tight text-center"
          :class="isSelected ? 'text-white group-hover:text-gray-100' : 'text-gray-800 group-hover:text-gray-900'">
        <span :class="isSelected ? 'text-white' : 'text-theme-brand'"># </span>{{ displayTagName }}
      </h3>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, onUnmounted, computed } from "vue";
import { createDoubleClickHandler, addTouchEventListeners, addLongPressDetection } from "../helpers.js";

const props = defineProps({
  tagData: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  },
  hasAnySelection: {
    type: Boolean,
    default: false
  },
  isPinned: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['click', 'dblclick', 'longpress']);

// Computed property to display tag name (show "_untagged" as "Untagged")
const displayTagName = computed(() => {
  return props.tagData.tag === "_untagged" ? "Untagged" : props.tagData.tag;
});

// Check if tag has recently modified notes (within 1 hour)
const hasRecentlyModifiedNote = computed(() => {
  if (!props.tagData.recentModified) return false;
  
  const recentModified = new Date(props.tagData.recentModified * 1000);
  const now = new Date();
  const diffInHours = (now - recentModified) / (1000 * 60 * 60);
  
  return diffInHours < 1;
});

function getBackgroundClass() {
  if (props.isSelected) {
    return 'bg-theme-brand border-theme-brand shadow-md text-white';
  } else if (props.hasAnySelection) {
    return 'bg-gray-100 border-gray-300';
  } else {
    return 'bg-white border-gray-300';
  }
}

const cardElement = ref(null);
let clickTimeout = null;
let cleanupLongPress = null;
let isProcessingClick = false;

function handleClick() {
  // Prevent multiple rapid clicks
  if (isProcessingClick) {
    return;
  }
  
  isProcessingClick = true;
  
  if (props.isSelected) {
    // For selected tags, use timer to distinguish between single and double click
    if (clickTimeout) {
      // Double click detected
      clearTimeout(clickTimeout);
      clickTimeout = null;
      emit('dblclick', props.tagData.tag);
      setTimeout(() => { isProcessingClick = false; }, 100);
    } else {
      // Single click - wait to see if it becomes a double click
      clickTimeout = setTimeout(() => {
        emit('click', props.tagData.tag);
        clickTimeout = null;
        isProcessingClick = false;
      }, 300); // 300ms delay to distinguish between single and double click
    }
  } else {
    // For unselected tags, emit click immediately
    emit('click', props.tagData.tag);
    setTimeout(() => { isProcessingClick = false; }, 100);
  }
}

function handleDoubleClick() {
  // Handle double click for both desktop and mobile
  if (clickTimeout) {
    clearTimeout(clickTimeout);
    clickTimeout = null;
  }
  emit('dblclick', props.tagData.tag);
}

function handleLongPress() {
  // Handle long press for pinning/unpinning
  if (clickTimeout) {
    clearTimeout(clickTimeout);
    clickTimeout = null;
  }
  emit('longpress', props.tagData.tag);
}

// Setup touch event listeners on mount
onMounted(() => {
  if (cardElement.value) {
    // Don't add touch event listeners here since we're handling clicks manually
    // to avoid conflicts with the double-click detection logic
    cleanupLongPress = addLongPressDetection(cardElement.value, handleLongPress, 500);
  }
});

onUnmounted(() => {
  if (cleanupLongPress) {
    cleanupLongPress();
  }
  if (clickTimeout) {
    clearTimeout(clickTimeout);
  }
});
</script>

<style scoped>
/* Card pin animation */
.pin-animation {
  animation: pinPulse 0.6s ease-out;
}

@keyframes pinPulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}
</style> 