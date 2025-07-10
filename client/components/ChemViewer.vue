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

    <!-- JSmol viewer container -->
    <div v-else class="h-full relative">
      <div
        ref="chemViewer"
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
const chemViewer = ref(null);
const isLoading = ref(false);
const error = ref(null);
let jmolApplet = null;

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
    
    // Additional wait for DOM element to be fully ready
    await new Promise(resolve => requestAnimationFrame(resolve));
    
    // Check if JSmol is loaded
    if (typeof Jmol === 'undefined') {
      throw new Error('JSmol library not loaded. Please refresh the page.');
    }

    // Wait for DOM element to be ready
    if (!chemViewer.value) {
      throw new Error('Viewer container not ready');
    }

    // Clear previous viewer
    if (jmolApplet) {
      Jmol.script(jmolApplet, 'zap');
    }
    
    // Determine file format from extension
    const fileExtension = props.attachmentFilename.split('.').pop().toLowerCase();
    
    // Create JSmol applet
    const appletId = 'chemViewer_' + Date.now();
    chemViewer.value.innerHTML = '';
    
    jmolApplet = Jmol.getApplet(appletId, {
      width: '100%',
      height: '100%',
      color: 'white',
      antialias: true,
      use: 'HTML5',
      script: 'set antialiasDisplay ON; set showHydrogens ON;'
    });
    
    // Add applet to container
    chemViewer.value.appendChild(jmolApplet);
    
    // Load file data based on format
    let loadScript = '';
    if (fileExtension === 'xyz') {
      loadScript = `load DATA "${props.fileContent}" XYZ`;
    } else if (fileExtension === 'pdb') {
      loadScript = `load DATA "${props.fileContent}" PDB`;
    } else if (fileExtension === 'mol') {
      loadScript = `load DATA "${props.fileContent}" MOL`;
    } else if (fileExtension === 'sdf') {
      loadScript = `load DATA "${props.fileContent}" SDF`;
    } else if (fileExtension === 'cif') {
      loadScript = `load DATA "${props.fileContent}" CIF`;
    } else if (fileExtension === 'mol2') {
      loadScript = `load DATA "${props.fileContent}" MOL2`;
    } else {
      // Default to XYZ format
      loadScript = `load DATA "${props.fileContent}" XYZ`;
    }
    
    // Load molecule and set style
    Jmol.script(jmolApplet, loadScript);
    Jmol.script(jmolApplet, 'set antialiasDisplay ON');
    Jmol.script(jmolApplet, 'set showHydrogens ON');
    Jmol.script(jmolApplet, 'wireframe OFF');
    Jmol.script(jmolApplet, 'spacefill OFF');
    Jmol.script(jmolApplet, 'sticks ON');
    Jmol.script(jmolApplet, 'zoomTo');
    
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

// Watch for file content changes
watch(() => props.fileContent, (newContent) => {
  if (newContent) {
    loadMolecule();
  }
}, { immediate: true });

// Watch for attachment filename changes
watch(() => props.attachmentFilename, (newFilename) => {
  if (newFilename && props.fileContent) {
    loadMolecule();
  }
}, { immediate: true });

// Lifecycle
onMounted(() => {
  // Initial load will be handled by the watcher
});

onUnmounted(() => {
  // Clean up viewer
  if (jmolApplet) {
    Jmol.script(jmolApplet, 'zap');
    jmolApplet = null;
  }
});
</script>

<style scoped>
/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
}
</style> 