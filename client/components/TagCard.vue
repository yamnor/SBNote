<template>
  <div 
    ref="cardElement"
    @click="handleClick"
    @dblclick="handleDoubleClick"
    class="p-2 cursor-pointer transition-all duration-300 group h-36 w-full flex flex-col border relative rounded-lg"
    :class="[getBackgroundClass(), { 'pin-animation': showPinAnimation, 'long-press-active': isLongPressing }]"
    style="touch-action: manipulation; user-select: none; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none;"
  >
    <!-- Corner triangle for pinned tags in top-right -->
    <div 
      v-if="isPinned"
      class="absolute top-0 right-0 w-0 h-0 border-l-[20px] border-l-transparent border-t-[20px] border-t-color-primary"
    >
    </div>
    
    <!-- Recent note modification indicator in top-left corner -->
    <div v-if="hasRecentlyModifiedNote" class="absolute top-1 left-1">
      <div class="w-2 h-2 rounded-full" style="background-color: var(--color-accent);"></div>
    </div>
    
    <!-- Note count badge in bottom-right corner -->
    <div class="absolute bottom-1 right-1">
      <span class="inline-flex items-center justify-center w-5 h-5 text-xs font-medium rounded bg-gray-200 text-gray-600">
        {{ tagData.count }}
      </span>
    </div>
    
    <!-- Centered tag name -->
    <div class="flex-1 flex items-center justify-center min-w-0">
      <h3 class="text-sm font-medium transition-colors leading-tight text-center"
          :class="isSelected ? 'text-white group-hover:text-gray-100' : 'text-gray-800 group-hover:text-gray-900'">
        <span :class="isSelected ? 'text-color-text-inverse' : 'text-color-primary'"># </span>{{ displayTagName }}
      </h3>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, onUnmounted, computed, watch } from "vue";
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

// Long press state tracking
const isLongPressing = ref(false);
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
    return 'bg-color-button-primary-bg border-color-button-primary-bg text-color-button-primary-fg';
  } else if (props.hasAnySelection) {
    return 'bg-color-bg-neutral border-color-bg-neutral hover:border-color-primary';
  } else {
    return 'bg-color-bg-neutral border-color-bg-neutral hover:border-color-primary';
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

function handleLongPressStart() {
  // Start long press animation
  isLongPressing.value = true;
}

function handleLongPressEnd() {
  // End long press animation
  isLongPressing.value = false;
}

function handleLongPress() {
  // Handle long press for pinning/unpinning
  if (clickTimeout) {
    clearTimeout(clickTimeout);
    clickTimeout = null;
  }
  emit('longpress', props.tagData.tag);
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

// Setup touch event listeners on mount
onMounted(() => {
  if (cardElement.value) {
    // Add custom long press detection with start/end callbacks
    cleanupLongPress = addLongPressDetectionWithCallbacks(
      cardElement.value, 
      handleLongPress, 
      handleLongPressStart,
      handleLongPressEnd,
      500
    );
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

// Custom long press detection with start/end callbacks
function addLongPressDetectionWithCallbacks(element, longPressHandler, startHandler, endHandler, duration = 500) {
  if (!element) return () => {};
  
  let pressTimer = null;
  let isLongPress = false;
  let hasTriggeredLongPress = false;
  let hasMoved = false;
  let startX = 0;
  let startY = 0;
  
  const startPress = (event) => {
    isLongPress = false;
    hasTriggeredLongPress = false;
    hasMoved = false;
    
    // Store initial touch position
    if (event.touches && event.touches[0]) {
      startX = event.touches[0].clientX;
      startY = event.touches[0].clientY;
    } else if (event.clientX !== undefined) {
      startX = event.clientX;
      startY = event.clientY;
    }
    
    // Start long press animation immediately
    if (startHandler) {
      startHandler(event);
    }
    
    pressTimer = setTimeout(() => {
      // Only trigger long press if no significant movement occurred
      if (!hasMoved) {
        isLongPress = true;
        hasTriggeredLongPress = true;
        longPressHandler(event);
      }
    }, duration);
  };
  
  const handleMove = (event) => {
    if (!startX && !startY) return;
    
    let currentX, currentY;
    if (event.touches && event.touches[0]) {
      currentX = event.touches[0].clientX;
      currentY = event.touches[0].clientY;
    } else if (event.clientX !== undefined) {
      currentX = event.clientX;
      currentY = event.clientY;
    } else {
      return;
    }
    
    const deltaX = Math.abs(currentX - startX);
    const deltaY = Math.abs(currentY - startY);
    
    // If moved more than 10px, consider it a scroll gesture
    if (deltaX > 10 || deltaY > 10) {
      hasMoved = true;
      if (pressTimer) {
        clearTimeout(pressTimer);
        pressTimer = null;
      }
      // End long press animation if moved
      if (endHandler) {
        endHandler(event);
      }
    }
  };
  
  const endPress = () => {
    if (pressTimer) {
      clearTimeout(pressTimer);
      pressTimer = null;
    }
    // End long press animation
    if (endHandler) {
      endHandler();
    }
    // Reset long press flag after a short delay to allow click events to be cancelled
    setTimeout(() => {
      isLongPress = false;
    }, 100);
  };
  
  const cancelPress = () => {
    if (pressTimer) {
      clearTimeout(pressTimer);
      pressTimer = null;
    }
    isLongPress = false;
    hasTriggeredLongPress = false;
    hasMoved = false;
    // End long press animation
    if (endHandler) {
      endHandler();
    }
  };
  
  // Mouse events for desktop
  element.addEventListener('mousedown', startPress);
  element.addEventListener('mousemove', handleMove);
  element.addEventListener('mouseup', endPress);
  element.addEventListener('mouseleave', cancelPress);
  
  // Touch events for mobile
  element.addEventListener('touchstart', startPress);
  element.addEventListener('touchmove', handleMove);
  element.addEventListener('touchend', endPress);
  element.addEventListener('touchcancel', cancelPress);
  
  // Prevent context menu on long press
  element.addEventListener('contextmenu', (event) => {
    if (isLongPress) {
      event.preventDefault();
    }
  });
  
  // Add click event listener to prevent click when long press was triggered
  const clickHandler = (event) => {
    if (hasTriggeredLongPress) {
      event.preventDefault();
      event.stopPropagation();
      hasTriggeredLongPress = false;
    }
  };
  
  element.addEventListener('click', clickHandler, true);
  
  // Return cleanup function
  return () => {
    element.removeEventListener('mousedown', startPress);
    element.removeEventListener('mousemove', handleMove);
    element.removeEventListener('mouseup', endPress);
    element.removeEventListener('mouseleave', cancelPress);
    element.removeEventListener('touchstart', startPress);
    element.removeEventListener('touchmove', handleMove);
    element.removeEventListener('touchend', endPress);
    element.removeEventListener('touchcancel', cancelPress);
    element.removeEventListener('click', clickHandler, true);
    if (pressTimer) {
      clearTimeout(pressTimer);
    }
  };
}
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

/* Long press animation - card gets smaller */
.long-press-active {
  transform: scale(0.95);
  transition: transform 0.2s ease-out;
}
</style> 