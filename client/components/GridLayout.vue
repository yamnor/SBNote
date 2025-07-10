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
      
      <!-- Note Card -->
      <Transition
        v-else-if="item.type === 'note'"
        name="note-fade"
        appear
      >
        <NoteCard :note="item.data" />
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
/* Note card fade-in animation */
.note-fade-enter-active {
  transition: all 0.4s ease-out;
}

.note-fade-leave-active {
  transition: all 0.3s ease-in;
}

.note-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.note-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.98);
}

.note-fade-enter-to {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.note-fade-leave-from {
  opacity: 1;
  transform: translateY(0) scale(1);
}
</style> 