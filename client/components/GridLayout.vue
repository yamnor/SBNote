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
      <Transition
        v-else-if="item.type === 'note'"
        name="note-fade"
        appear
      >
        <div 
          :style="{ '--animation-index': getNoteAnimationIndex(index) }"
          class="note-card-wrapper"
        >
          <NoteCard :note="item.data" />
        </div>
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import NoteCard from './NoteCard.vue';
import TagCard from './TagCard.vue';

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
  
  // Calculate animation index: right to left, bottom to top
  // Start from the bottom-right corner
  const maxRow = Math.floor((noteItems.length - 1) / columns);
  const maxCol = columns - 1;
  
  // Calculate distance from bottom-right corner
  const rowDistance = maxRow - row;
  const colDistance = maxCol - col;
  
  // Animation index: higher number = earlier animation
  // This makes cards appear from bottom-right to top-left
  return (rowDistance * columns) + colDistance;
}

// Resize observer to watch container width changes
let resizeObserver = null;

onMounted(() => {
  if (gridContainer.value) {
    // Initial width measurement
    containerWidth.value = gridContainer.value.offsetWidth;
    
    // Set up resize observer
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        containerWidth.value = entry.contentRect.width;
      }
    });
    
    resizeObserver.observe(gridContainer.value);
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
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
/* Note card staged animation with CSS animation-delay */
.note-fade-enter-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  transition-delay: calc(var(--animation-index, 0) * 0.1s);
}

.note-fade-leave-active {
  transition: all 0.3s ease-in;
}

.note-fade-enter-from {
  opacity: 0;
  transform: translateX(-40px) scale(0.95);
}

.note-fade-leave-to {
  opacity: 0;
  transform: translateX(15px) scale(0.95);
}

.note-fade-enter-to {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.note-fade-leave-from {
  opacity: 1;
  transform: translateX(0) scale(1);
}

/* Wrapper for note card */
.note-card-wrapper {
  display: contents;
}
</style> 