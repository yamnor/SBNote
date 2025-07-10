<template>
  <div class="h-full relative">
    <!-- Error message -->
    <div v-if="error" class="h-full flex items-center justify-center p-8">
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

    <!-- Miew viewer container -->
    <div v-else class="h-full relative">
      <div
        ref="miewViewer"
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
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { FileX, Loader2, RefreshCw } from 'lucide-vue-next';
import Miew from 'miew';

const props = defineProps({
  attachmentFilename: {
    type: String,
    required: true
  },
  noteTitle: {
    type: String,
    default: 'Molecular Structure'
  },
  fileContent: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['error', 'loading', 'loaded']);

// State
const miewViewer = ref(null);
const isLoading = ref(false);
const error = ref(null);
let viewer = null;

// Methods
async function loadMolecule() {
  if (!props.fileContent) {
    error.value = 'No file content provided';
    emit('error', error.value);
    return;
  }
  
  isLoading.value = true;
  error.value = null;
  emit('loading', true);

  try {
    // Wait for DOM to be ready
    await nextTick();
    
    // Check if Miew library is loaded
    if (!Miew) {
      throw new Error('Miew library not loaded. Please refresh the page.');
    }
    
    // Check if DOM element is ready
    if (!miewViewer.value) {
      throw new Error('Viewer container not ready');
    }

    // Clear previous viewer
    if (viewer) {
      // Try to stop the viewer if possible
      try {
        if (typeof viewer.stop === 'function') {
          viewer.stop();
        }
      } catch (e) {
        console.warn('Could not stop previous viewer:', e);
      }
      // Clear the container
      miewViewer.value.innerHTML = '';
    }
    
    // Create new Miew viewer
    viewer = new Miew({
      container: miewViewer.value,
      settings: {
        backgroundColor: { r: 1, g: 1, b: 1 }, // White background
        camera: {
          position: { x: 0, y: 0, z: 10 }
        }
      }
    });
    
    // Initialize the viewer
    if (typeof viewer.init === 'function') {
      if (!viewer.init()) {
        throw new Error('Failed to initialize Miew viewer');
      }
    }
    
    // Determine file format from extension
    const fileExtension = props.attachmentFilename.split('.').pop().toLowerCase();
    
    // Load file data based on format
    let format = 'pdb'; // Default format
    if (fileExtension === 'xyz') {
      format = 'xyz';
    } else if (fileExtension === 'mol' || fileExtension === 'sdf') {
      format = 'sdf';
    } else if (fileExtension === 'pdb') {
      format = 'pdb';
    }
    
    // Load the molecule
    if (typeof viewer.load === 'function') {
      // Create a blob URL for the file content
      const blob = new Blob([props.fileContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      try {
        await viewer.load(url);
      } finally {
        // Clean up the blob URL
        URL.revokeObjectURL(url);
      }
    }
    
    // Set default representation (ball and stick)
    if (typeof viewer.rep === 'function') {
      viewer.rep({
        mode: 'BS',
        colorer: 'EL',
        material: 'DF'
      });
    }
    
    // Auto-fit the molecule
    if (typeof viewer.autoFit === 'function') {
      viewer.autoFit();
    }
    
    // Start the viewer
    if (typeof viewer.run === 'function') {
      viewer.run();
    }
    
    isLoading.value = false;
    emit('loaded', true);
    emit('loading', false);
    
  } catch (err) {
    console.error('Failed to load molecule:', err);
    error.value = `Failed to load molecular structure: ${err.message}`;
    isLoading.value = false;
    emit('error', error.value);
    emit('loading', false);
  }
}

function retryLoad() {
  loadMolecule();
}

// Watch for file content and filename changes
watch([() => props.fileContent, () => props.attachmentFilename], ([newContent, newFilename]) => {
  if (newContent && newFilename) {
    loadMolecule();
  }
}, { immediate: true });

// Lifecycle
onMounted(() => {
  // Initial load will be handled by the watcher
});

onUnmounted(() => {
  // Clean up viewer
  if (viewer) {
    try {
      if (typeof viewer.stop === 'function') {
        viewer.stop();
      }
    } catch (e) {
      console.warn('Could not stop viewer on unmount:', e);
    }
    viewer = null;
  }
});
</script>

<style>
@import 'miew/dist/Miew.min.css';

/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
}
</style> 