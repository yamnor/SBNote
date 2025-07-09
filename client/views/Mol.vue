<template>
  <div class="fixed inset-0 z-50 bg-white dark:bg-gray-900">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-white/90 backdrop-blur-sm">
      <div class="flex items-center space-x-3">
        <div>
          <h1 class="text-lg font-semibold text-theme-text-muted">{{ noteTitle }}</h1>
        </div>
      </div>
      
      <div class="flex items-center space-x-8">
        <!-- Loading indicator -->
        <div v-if="isLoading" class="flex items-center space-x-2 text-theme-text-muted">
          <Loader2 class="w-4 h-4 animate-spin" />
          <span class="text-sm">Loading molecule...</span>
        </div>
        
        <!-- Raw button -->
        <button
          @click="goToCode"
          class="flex items-center justify-center w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors"
          title="Go to raw view"
        >
          <FileText class="w-8 h-8" />
        </button>
        
        <!-- Mol button (current view) -->
        <button
          class="flex items-center justify-center w-8 h-8 text-theme-brand text-theme-text transition-colors"
          title="Current view"
        >
          <Eye class="w-8 h-8" />
        </button>
        
        <!-- Note button -->
        <button
          @click="goToNote"
          class="flex items-center justify-center w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors"
          title="Go to note"
        >
          <Info class="w-8 h-8" />
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ArrowLeft, FileX, Loader2, RefreshCw, Info, FileText, Eye } from 'lucide-vue-next';
import { useNoteAttachment } from '../composables/useNoteAttachment.js';

const props = defineProps({
  filename: String,
});

const router = useRouter();
const route = useRoute();

// State
const molViewer = ref(null);
let viewer = null;

// Use composable for note data and attachment handling
const { noteData, isLoading, error, loadNoteDataAndAttachment } = useNoteAttachment();

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
  // Navigate to the note view using basename without extension
  const basename = props.filename.replace(/\.md$/, '');
  router.push({ name: 'note', params: { filename: basename } });
}

function goToCode() {
  // Navigate to the code view using basename
  router.push({ name: 'code', params: { filename: props.filename } });
}

async function loadNoteData() {
  try {
    // Use composable to load note data and get attachment filename
    const { attachmentFilename } = await loadNoteDataAndAttachment(props.filename);
    
    await loadMolecule(attachmentFilename);
  } catch (err) {
    console.error('Failed to load note data:', err);
    error.value = err.message || 'Failed to load molecule data';
  }
}

async function loadMolecule(attachmentFilename) {
  try {
    // Fetch attachment file content
    const response = await fetch(`/files/${encodeURIComponent(attachmentFilename)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch attachment file: ${response.statusText}`);
    }
    
    const fileContent = await response.text();
    
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
    
    // Determine file format from extension
    const fileExtension = attachmentFilename.split('.').pop().toLowerCase();
    
    // Load file data based on format
    if (fileExtension === 'xyz') {
      viewer.addModel(fileContent, 'xyz');
    } else if (fileExtension === 'pdb') {
      viewer.addModel(fileContent, 'pdb');
    } else if (fileExtension === 'mol') {
      viewer.addModel(fileContent, 'mol');
    } else if (fileExtension === 'sdf') {
      viewer.addModel(fileContent, 'sdf');
    } else {
      // Default to XYZ format
      viewer.addModel(fileContent, 'xyz');
    }
    
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

// Watch for note data changes to update browser title
watch(noteData, (newNoteData) => {
  if (newNoteData?.title) {
    document.title = `${newNoteData.title} - SBNote`;
  } else {
    document.title = "Molecule - SBNote";
  }
}, { immediate: true });

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