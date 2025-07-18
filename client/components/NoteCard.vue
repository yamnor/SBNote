<template>
  <div>
    <div 
      ref="cardElement"
      @click="handleClick"
      @mousedown="handleMouseDown"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseLeave"
      @touchstart="handleTouchStart"
      @touchend="handleTouchEnd"
      @touchcancel="handleTouchCancel"
      class="bg-color-surface p-2 cursor-pointer duration-200 group h-36 w-full flex flex-col border-t-4 border-t-color-primary relative border border-color-surface hover:border-color-primary note-card"
      :class="{ 
        'click-active': isClicking,
        'opacity-50': isSearchResult
      }"
      style="touch-action: manipulation; user-select: none; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; z-index: 1;"
      :title="globalStore.editMode ? 'Click to preview' : 'Click to preview'"
    >
      <!-- Recent edit indicator in top-right corner -->
      <div v-if="isRecentlyEdited" class="absolute top-1 right-1">
        <div class="w-2 h-2 rounded-full" style="background-color: var(--color-accent);"></div>
      </div>
      
      <!-- Priority star indicator in top-left corner -->
      <div v-if="note.priority" class="absolute top-1 left-1">
        <div class="flex">
          <span v-for="i in 5" :key="i" 
                class="text-xs"
                :class="i <= note.priority ? 'text-color-complementary' : 'text-gray-300'">
            ★
          </span>
        </div>
      </div>
      
      <!-- Category icon in bottom-left corner -->
      <div class="absolute bottom-1 left-1 flex flex-row items-center gap-1">
        <div class="w-5 h-5 flex items-center justify-center text-gray-500">
          <component :is="categoryIcon" class="w-4 h-4" />
        </div>
        <div class="w-5 h-5 flex items-center justify-center" :class="visibilityIconColor">
          <component :is="visibilityIcon" class="w-4 h-4" />
        </div>
      </div>
            
      <div class="flex-1 min-w-0">
        <h3 class="text-gray-800 text-sm font-medium group-hover:text-gray-900 transition-colors leading-tight line-clamp-3 search-highlights">
          <span v-if="note.titleHighlights" v-html="note.titleHighlights"></span>
          <span v-else>{{ note.title }}</span>
        </h3>
        <!-- Note content preview -->
        <div v-if="note.contentHighlights" class="text-gray-500 text-xs mt-1 line-clamp-3 search-highlights">
          <span v-html="note.contentHighlights"></span>
        </div>
        <div v-else-if="note.content" class="text-gray-500 text-xs mt-1 line-clamp-3">
          {{ contentPreview }}
        </div>
      </div>
    </div>

    <!-- Note Preview Modal -->
    <QuickNoteModal
      v-if="note.category !== 'image' && note.category !== 'coordinate' && note.category !== 'output'"
      v-model="showPreviewModal"
      :note="note"
      @close="showPreviewModal = false"
      @note-updated="handleNoteUpdated"
    />
    
    <!-- Image Preview Modal -->
    <PreviewImageModal
      v-else-if="note.category === 'image'"
      v-model="showPreviewModal"
      :note="note"
      @close="showPreviewModal = false"
    />
    
    <!-- Molecular Preview Modal (for coordinate and output) -->
    <PreviewCoordinateModal
      v-else-if="note.category === 'coordinate' || note.category === 'output'"
      v-model="showPreviewModal"
      :note="note"
      @close="showPreviewModal = false"
    />
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { useGlobalStore } from "../lib/globalStore.js";
import QuickNoteModal from "./QuickNoteModal.vue";
import PreviewImageModal from "./PreviewImageModal.vue";
import PreviewCoordinateModal from "./PreviewCoordinateModal.vue";
import { StickyNote, FileText, Bolt, Image, Lock, Users, Globe, Scroll } from "lucide-vue-next";

const props = defineProps({
  note: {
    type: Object,
    required: true
  },
  isSearchResult: {
    type: Boolean,
    default: false
  }
});

const globalStore = useGlobalStore();
const showPreviewModal = ref(false);

// Click state tracking
const isClicking = ref(false);

// Handle click to show preview modal
function handleClick() {
  showPreviewModal.value = true;
}

// Handle note updates from QuickNoteModal
function handleNoteUpdated(updatedNote) {
  // Update the note object with the updated data
  Object.assign(props.note, updatedNote);
}

// Mouse event handlers for desktop
function handleMouseDown() {
  isClicking.value = true;
}

function handleMouseUp() {
  isClicking.value = false;
}

function handleMouseLeave() {
  isClicking.value = false;
}

// Touch event handlers for mobile
function handleTouchStart() {
  isClicking.value = true;
}

function handleTouchEnd() {
  isClicking.value = false;
}

function handleTouchCancel() {
  isClicking.value = false;
}

// Content preview (first 200 characters)
const contentPreview = computed(() => {
  if (!props.note.content) return "";
  const cleanContent = props.note.content.replace(/#[a-zA-Z0-9_\-\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+/g, '').trim();
  return cleanContent.substring(0, 200) + (cleanContent.length > 200 ? '...' : '');
});

// Check if note was edited recently (within 1 hour)
const isRecentlyEdited = computed(() => {
  if (!props.note.lastModified) return false;
  
  const lastModified = new Date(props.note.lastModified * 1000);
  const now = new Date();
  const diffInHours = (now - lastModified) / (1000 * 60 * 60);
  
  return diffInHours < 1;
});

// Get category icon based on note category
const categoryIcon = computed(() => {
  const category = props.note.category || 'note';
  
  switch (category.toLowerCase()) {
    case 'image':
      return Image;
    case 'coordinate':
      return Bolt;
    case 'output':
      return Scroll;

    case 'note':
    default:
      return StickyNote;
  }
});

// Get visibility icon based on note visibility
const visibilityIcon = computed(() => {
  const visibility = props.note.visibility || 'private';
  
  switch (visibility) {
    case 'public':
      return Globe;
    case 'limited':
      return Users;
    case 'private':
    default:
      return Lock;
  }
});

// Get visibility icon color based on note visibility
const visibilityIconColor = computed(() => {
  const visibility = props.note.visibility || 'private';
  
  switch (visibility) {
    case 'public':
      return 'text-color-label-public';
    case 'limited':
      return 'text-color-label-limited';
    case 'private':
    default:
      return 'text-color-label-private';
  }
});

// Format date
function formatDate(timestamp) {
  if (!timestamp) return '';
  
  // Server returns timestamp in seconds, so multiply by 1000 to get milliseconds
  const date = new Date(timestamp * 1000);
  
  // Check if date is valid
  if (isNaN(date.getTime())) {
    console.warn('Invalid timestamp:', timestamp);
    return '';
  }
  
  const now = new Date();
  const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) {
    return 'Today';
  } else if (diffInDays === 1) {
    return 'Yesterday';
  } else if (diffInDays < 7) {
    return `${diffInDays} days ago`;
  } else if (diffInDays < 30) {
    const weeks = Math.floor(diffInDays / 7);
    return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
  } else if (diffInDays < 365) {
    const months = Math.floor(diffInDays / 30);
    return `${months} month${months > 1 ? 's' : ''} ago`;
  } else {
    const years = Math.floor(diffInDays / 365);
    return `${years} year${years > 1 ? 's' : ''} ago`;
  }
}
</script>

<style scoped>
/* Click animation - card gets smaller when clicked */
.click-active {
  transform: scale(0.98);
  transition: transform 0.1s ease-out;
}

/* Smooth transition for all card properties */
.bg-color-surface {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}



/* Animation styles for note cards */
.note-card.leaving {
  transition: all 0.5s ease-in-out !important;
  transform: translateX(-100px) !important;
  opacity: 0 !important;
  z-index: 1;
}

/* General leaving animation class */
.leaving {
  transition: all 0.5s ease-in-out !important;
  transform: translateX(-100px) !important;
  opacity: 0 !important;
  z-index: 1;
}


</style> // test comment
// test after restart
