<template>
  <div class="fixed inset-0 z-50 bg-white dark:bg-gray-900">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm border-b border-theme-border">
      <div class="flex items-center space-x-3">
        <div>
          <h1 class="text-lg font-semibold text-theme-text">{{ noteTitle }}</h1>
        </div>
      </div>
      
      <div class="flex items-center space-x-2">
        <!-- Loading indicator -->
        <div v-if="isLoading" class="flex items-center space-x-2 text-theme-text-muted">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span class="text-sm">Loading molecule...</span>
        </div>
        
        <!-- Note button -->
        <button
          @click="goToNote"
          class="flex items-center justify-center w-9 h-9 rounded-lg bg-theme-button hover:bg-theme-brand hover:text-white text-theme-text transition-colors shadow-sm"
          title="Go to note"
        >
          <StickyNote class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="h-screen flex items-center justify-center p-8">
      <div class="text-center">
        <FileX class="w-16 h-16 mx-auto text-theme-text-muted mb-4" />
        <h2 class="text-xl font-semibold text-theme-text mb-2">Failed to load molecule</h2>
        <p class="text-theme-text-muted mb-4">{{ error }}</p>
        <button
          @click="retryLoad"
          class="inline-flex items-center px-4 py-2 bg-theme-brand text-white rounded-lg hover:bg-theme-brand-dark transition-colors"
        >
          <RefreshCw class="w-4 h-4 mr-2" />
          Retry
        </button>
      </div>
    </div>

    <!-- 3Dmol viewer container -->
    <div v-else class="h-screen relative">
      <div
        ref="molViewer"
        class="w-full h-full"
        :class="{ 'opacity-50': isLoading }"
      ></div>
      
      <!-- Loading overlay -->
      <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50">
        <div class="text-center">
          <Loader2 class="w-8 h-8 mx-auto text-theme-brand animate-spin mb-2" />
          <p class="text-sm text-theme-text-muted">Loading molecular structure...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ArrowLeft, FileX, Loader2, RefreshCw, StickyNote } from 'lucide-vue-next';
import { getNote } from '../api.js';

const props = defineProps({
  filename: String,
});

const router = useRouter();
const route = useRoute();

// State
const molViewer = ref(null);
const isLoading = ref(true);
const error = ref(null);
const noteData = ref(null);
let viewer = null;

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Molecular Structure';
});

// Methods
function goBack() {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push({ name: 'home' });
  }
}

function goToNote() {
  // Navigate to the note view
  router.push({ name: 'note', params: { filename: props.filename } });
}

async function loadNoteData() {
  try {
    isLoading.value = true;
    error.value = null;
    
    // Get note data to extract XYZ file information
    const filenameWithExtension = props.filename + '.md';
    const note = await getNote(filenameWithExtension);
    noteData.value = note;
    
    // Extract XYZ filename from note content
    const xyzFilename = extractXyzFilename(note.content);
    if (!xyzFilename) {
      throw new Error('XYZ file not found in note content');
    }
    
    await loadMolecule(xyzFilename);
  } catch (err) {
    console.error('Failed to load note data:', err);
    error.value = err.message || 'Failed to load molecule data';
  } finally {
    isLoading.value = false;
  }
}

function extractXyzFilename(content) {
  // Look for XYZ file link in the note content
  // Format: [XYZ File](/files/filename.xyz)
  const match = content.match(/\[XYZ File\]\(\/files\/([^)]+\.xyz)\)/);
  if (match) {
    return match[1];
  }
  
  // Alternative: look for direct file path
  const directMatch = content.match(/\/files\/([^\s]+\.xyz)/);
  if (directMatch) {
    return directMatch[1];
  }
  
  return null;
}

async function loadMolecule(xyzFilename) {
  try {
    // Fetch XYZ file content
    const response = await fetch(`/files/${xyzFilename}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch XYZ file: ${response.statusText}`);
    }
    
    const xyzContent = await response.text();
    
    // Initialize 3Dmol viewer
    if (!window.$3Dmol) {
      throw new Error('3Dmol.js library not loaded');
    }
    
    // Clear previous viewer
    if (viewer) {
      viewer.clear();
    }
    
    // Create new viewer
    viewer = window.$3Dmol.createViewer(molViewer.value, {
      backgroundColor: 'white',
      antialias: true,
      defaultcolors: window.$3Dmol.rasmolElementColors
    });
    
    // Load XYZ data
    viewer.addModel(xyzContent, 'xyz');
    
    // Set view style
    viewer.setStyle({}, {
      stick: { radius: 0.15 },
      sphere: { radius: 0.5 }
    });
    
    // Center and zoom the molecule
    viewer.zoomTo();
    viewer.render();
    
  } catch (err) {
    console.error('Failed to load molecule:', err);
    throw new Error(`Failed to load molecular structure: ${err.message}`);
  }
}

function retryLoad() {
  loadNoteData();
}

// Lifecycle
onMounted(async () => {
  // Check if 3Dmol.js is loaded (from CDN)
  if (!window.$3Dmol) {
    error.value = '3Dmol.js library not loaded. Please refresh the page.';
    isLoading.value = false;
    return;
  }
  
  await loadNoteData();
});

onUnmounted(() => {
  // Clean up viewer
  if (viewer) {
    viewer.clear();
    viewer = null;
  }
});
</script>

<style scoped>
/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
}

/* Ensure full screen coverage */
.fixed.inset-0 {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style> 