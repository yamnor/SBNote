<template>
  <div class="fixed inset-0 z-50 bg-white dark:bg-gray-900">
    <!-- Header -->
    <div class="absolute top-0 left-0 right-0 z-10 flex items-center justify-between p-4 bg-white/90 backdrop-blur-sm">
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <FileTextIcon 
            @click="goToNote" 
            class="w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors cursor-pointer"
            title="Go to note"
          />
          <h1 class="text-lg font-semibold text-theme-text-muted">
            {{ noteTitle }}
          </h1>
        </div>
      </div>
      
      <div class="flex items-center space-x-8">
        <!-- Raw button -->
        <button
          @click="goToRawView"
          class="flex items-center justify-center w-8 h-8 text-theme-muted hover:text-theme-text text-theme-text-muted transition-colors"
          title="Raw View"
        >
          <Grip class="w-8 h-8" />
        </button>
        
        <!-- Mol button (current view) -->
        <button
          class="flex items-center justify-center w-8 h-8 text-theme-brand text-theme-text transition-colors"
          title="Current view"
        >
          <Eye class="w-8 h-8" />
        </button>
      </div>
    </div>

    <!-- MolViewer component -->
    <div class="h-screen">
      <MolViewer 
        :attachment-filename="attachmentFilename"
        :note-title="noteTitle"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { FileText as FileTextIcon, Eye, Grip } from 'lucide-vue-next';
import { useNoteAttachment } from '../composables/useNoteAttachment.js';
import MolViewer from '../components/MolViewer.vue';

const props = defineProps({
  filename: String,
});

const router = useRouter();

// State
const attachmentFilename = ref(null);

// Use composable for note data and attachment handling
const { noteData, loadNoteDataAndAttachment } = useNoteAttachment();

// Computed
const noteTitle = computed(() => {
  return noteData.value?.title || 'Molecular Structure';
});

// Methods
function goToNote() {
  // Navigate to the note view using basename without extension
  const basename = props.filename.replace(/\.md$/, '');
  router.push({ name: 'note', params: { filename: basename } });
}

function goToRawView() {
  // Navigate to the raw view using basename
  router.push({ name: 'raw', params: { filename: props.filename } });
}

async function loadNoteData() {
  try {
    // Use composable to load note data and get attachment filename
    const { attachmentFilename: filename } = await loadNoteDataAndAttachment(props.filename);
    attachmentFilename.value = filename;
  } catch (err) {
    console.error('Failed to load note data:', err);
  }
}

// Lifecycle
onMounted(async () => {
  await loadNoteData();
});
</script>

<style scoped>
/* Ensure full screen coverage */
.fixed.inset-0 {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
</style> 