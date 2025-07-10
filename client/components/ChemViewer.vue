<template>
  <div class="h-full relative pt-12 pb-4">
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
    
    // Check if Jmol library is loaded
    if (!window.Jmol) {
      throw new Error('Jmol library not loaded. Please refresh the page.');
    }
    
    let JmolInstance = window.Jmol;

    // Check if DOM element is ready
    if (!chemViewer.value) {
      throw new Error('Viewer container not ready');
    }

    const appletId = 'chemViewer_' + Date.now();
    chemViewer.value.innerHTML = `<div id="${appletId}" style="width: 100%; height: 100%;"></div>`;

    $(`#${appletId}`).html(JmolInstance.getAppletHtml("myJmol", {
      width: '100%',
      height: '100%',
      j2sPath: 'assets/j2s',
      use: 'HTML5'
    }));
    
    let loadScript = `load INLINE "${props.fileContent}";`;

    try {
      JmolInstance.script(myJmol, loadScript);
      JmolInstance.script(myJmol, 'set defaultColors Rasmol;');
      JmolInstance.script(myJmol, 'console;');
    } catch (scriptError) {
      console.warn('Script execution warning:', scriptError);
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
  if (myJmol) {
    const JmolInstance = window.Jmol || Jmol;
    if (JmolInstance) {
      JmolInstance.script(myJmol, 'zap');
    }
    myJmol = null;
  }
});
</script>

<style scoped>
/* Ensure the viewer container takes full height */
.w-full.h-full {
  min-height: 0;
}
</style> 