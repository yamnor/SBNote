<template>
  <div 
    ref="cardElement"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    class="p-2 cursor-pointer group h-36 w-full flex flex-col relative rounded-lg border"
    :class="[getBackgroundClass(), { 'pin-animation': showPinAnimation }]"
    style="touch-action: manipulation; user-select: none; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; z-index: 5;"
  >

    
    <!-- Priority indicator in top-left corner -->
    <div class="absolute top-1 left-1">
      <div class="flex">
        <span v-for="i in 5" :key="i" 
              class="text-xs"
              :class="i <= tagData.priority ? (isSelected ? 'text-color-on-primary' : 'text-color-primary') : (isSelected ? 'text-color-primary' : 'text-color-background')">
          ★
        </span>
      </div>
    </div>
    
    <!-- Recent note modification indicator in top-right corner -->
    <div v-if="hasRecentlyModifiedNote" class="absolute top-1 right-1">
      <div class="w-2 h-2 rounded-full" style="background-color: var(--color-accent);"></div>
    </div>
    
    <!-- Pin icon in bottom-left corner for pinned tags -->
    <div v-if="isPinned" class="absolute bottom-1 left-1">
      <Pin class="w-5 h-5"
      :class="isSelected ? 'text-color-text-inverse' : 'text-color-primary'"/>
    </div>
    
    <!-- Note count badge in bottom-right corner -->
    <div class="absolute bottom-1 right-1">
      <span class="inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-medium rounded min-w-[1.25rem]"
            :class="isSelected ? 'bg-color-surface text-color-text-base' : 'bg-color-primary-light text-color-text-base'">
        <span v-if="tagData.searchResultCount !== undefined && tagData.otherCount !== undefined">
          <span class="text-color-text-light">{{ tagData.searchResultCount }}</span>
          <span class="text-color-primary">+{{ tagData.otherCount }}</span>
        </span>
        <span v-else>{{ tagData.count }}</span>
      </span>
    </div>
    
    <!-- Centered tag name -->
    <div class="flex-1 flex items-center justify-center min-w-0">
      <h3 class="text-sm font-medium leading-tight text-center"
          :class="isSelected ? 'text-white group-hover:text-gray-100' : 'text-gray-800 group-hover:text-gray-900'">
        <span :class="isSelected ? 'text-color-text-inverse' : 'text-color-primary'"># </span>{{ displayTagName }}
      </h3>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, onUnmounted, computed, watch } from "vue";
import { createDoubleClickHandler, addTouchEventListeners } from "../lib/helpers.js";
import { Pin } from "lucide-vue-next";

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

const emit = defineEmits(['click', 'dblclick']);

// Pin animation state tracking
const showPinAnimation = ref(false);
const previousPinnedState = ref(props.isPinned);

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
    return 'bg-color-primary border-color-primary text-color-inverse';
  } else {
    return 'bg-color-surface border-color-background hover:border-color-primary';
  }
}

const cardElement = ref(null);
let clickTimeout = null;
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



// Watch for pin state changes to trigger animation
watch(() => props.isPinned, (newPinnedState, oldPinnedState) => {
  // Only trigger animation if the pin state actually changed
  if (newPinnedState !== oldPinnedState) {
    // Trigger pin animation after a short delay to ensure smooth transition
    setTimeout(() => {
      showPinAnimation.value = true;
      // Remove animation class after animation completes
      setTimeout(() => {
        showPinAnimation.value = false;
      }, 600); // Match animation duration
    }, 50);
  }
});

// Setup component lifecycle
onMounted(() => {
  // Component mounted
});

onUnmounted(() => {
  if (clickTimeout) {
    clearTimeout(clickTimeout);
  }
});


</script>

<style scoped>
/* Card pin animation - from small size back to normal */
.pin-animation {
  animation: pinPulse 0.6s ease-out;
}

@keyframes pinPulse {
  0% {
    transform: scale(0.95);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    transform: scale(1);
  }
}


</style> // another test comment
