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

    <!-- 3Dmol viewer container -->
    <div v-else class="h-full relative">
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
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { FileX, Loader2, RefreshCw } from 'lucide-vue-next';

const props = defineProps({
  attachmentFilename: {
    type: String,
    required: true
  },
  noteTitle: {
    type: String,
    default: 'Molecular Structure'
  }
});

const emit = defineEmits(['error', 'loading', 'loaded']);

// State
const molViewer = ref(null);
const isLoading = ref(false);
const error = ref(null);
let viewer = null;

// Methods
async function loadMolecule() {
  if (!props.attachmentFilename) {
    error.value = 'No attachment filename provided';
    emit('error', error.value);
    return;
  }

  isLoading.value = true;
  error.value = null;
  emit('loading', true);

  try {
    // Check if 3Dmol.js is loaded
    if (!window.$3Dmol) {
      throw new Error('3Dmol.js library not loaded. Please refresh the page.');
    }

    // Fetch attachment file content
    const response = await fetch(`/files/${encodeURIComponent(props.attachmentFilename)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch attachment file: ${response.statusText}`);
    }
    
    const fileContent = await response.text();
    
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
    const fileExtension = props.attachmentFilename.split('.').pop().toLowerCase();
    
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
    
    isLoading.value = false;
    emit('loaded', true);
    emit('loading', false);
    
    // Update browser title
    updateBrowserTitle();
    
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

function updateBrowserTitle() {
  if (props.noteTitle) {
    document.title = `${props.noteTitle} - SBNote`;
  } else {
    document.title = "Molecule - SBNote";
  }
}

// Watch for attachment filename changes
watch(() => props.attachmentFilename, (newFilename) => {
  if (newFilename) {
    loadMolecule();
  }
}, { immediate: true });

// Watch for note title changes to update browser title
watch(() => props.noteTitle, () => {
  updateBrowserTitle();
}, { immediate: true });

// Lifecycle
onMounted(() => {
  // Initial load will be handled by the watcher
  updateBrowserTitle();
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
</style> 