<template>
  <div 
    ref="gridContainer"
    class="w-full grid gap-2"
    :class="gridColsClass"
  >

    <template v-for="(item, index) in items" :key="item.key">
      <!-- Tag Card -->
      <TagCard
        v-if="item.type === 'tag'"
        :tag-data="item.data"
        :is-selected="item.isSelected"
        :has-any-selection="item.hasAnySelection"
        :is-pinned="item.isPinned"
        @click="onTagClick"
        @dblclick="onTagDoubleClick"
        @longpress="onTagLongPress"
      />
      
      <!-- Note Card with CSS animation delay -->
      <div 
        v-else-if="item.type === 'note'"
        :style="{ '--animation-index': getNoteAnimationIndex(index) }"
        class="note-card-wrapper"
        :key="item.key"
      >
        <NoteCard :note="item.data" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import NoteCard from '../card/NoteCard.vue';
import TagCard from '../card/TagCard.vue';

const props = defineProps({
  items: {
    type: Array,
    required: true,
    // Each item should have: { type: 'tag'|'note', data: Object, key: String, ... }
  }
});

const emit = defineEmits(['tag-click', 'tag-dblclick', 'tag-longpress']);

const gridContainer = ref(null);
const containerWidth = ref(0);
const isMobile = ref(false);

// Calculate grid columns based on container width
const gridColsClass = computed(() => {
  const width = containerWidth.value;
  
  if (width <  400) return 'grid-cols-3';
  if (width <  550) return 'grid-cols-4';
  if (width <  700) return 'grid-cols-5';
  if (width <  850) return 'grid-cols-6';
  if (width < 1000) return 'grid-cols-7';
  if (width < 1150) return 'grid-cols-8';
  return 'grid-cols-8';
});

// Get the number of columns from the grid class
function getGridColumns() {
  const width = containerWidth.value;
  
  if (width <  400) return 3;
  if (width <  550) return 4;
  if (width <  700) return 5;
  if (width <  850) return 6;
  if (width < 1000) return 7;
  if (width < 1150) return 8;
  return 8;
}

// Calculate animation index for each note card based on grid position
function getNoteAnimationIndex(index) {
  // Find the note index within the current note group
  const noteItems = props.items.filter(item => item.type === 'note');
  const noteIndex = noteItems.findIndex(item => item.key === props.items[index].key);
  
  if (noteIndex === -1) return 0;
  
  const columns = getGridColumns();
  
  // Calculate grid position (row and column)
  const row = Math.floor(noteIndex / columns);
  const col = noteIndex % columns;
  
  // Calculate animation index: left to right, top to bottom for leave animation
  // This makes cards disappear from left to right, top to bottom
  // For leave animation, we want the opposite of enter animation
  return (row * columns) + col;
}

// Resize observer to watch container width changes
let resizeObserver = null;

onMounted(() => {
  if (gridContainer.value) {
    // Initial width measurement
    containerWidth.value = gridContainer.value.offsetWidth;
    
    // Check if mobile device
    isMobile.value = window.innerWidth < 768;
    
    // Set up resize observer
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerWidth.value = entry.contentRect.width;
      }
    });
    
    resizeObserver.observe(gridContainer.value);
    
    // Listen for window resize to update mobile detection
    window.addEventListener('resize', () => {
      isMobile.value = window.innerWidth < 768;
    });
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  // Remove resize listener
  window.removeEventListener('resize', () => {
    isMobile.value = window.innerWidth < 768;
  });
});

// Event handlers for tag interactions
function onTagClick(tagName) {
  emit('tag-click', tagName);
}

function onTagDoubleClick(tagName) {
  emit('tag-dblclick', tagName);
}

function onTagLongPress(tagName) {
  emit('tag-longpress', tagName);
}
</script>

<style scoped>
/* Note card animation styles */
.note-card-wrapper {
  display: contents;
  position: relative;
}

.note-card-wrapper.leaving {
  transition: all 0.5s ease-in-out !important;
  transform: translateX(-100px) !important;
  opacity: 0 !important;
  z-index: 1 !important;
}


</style> 