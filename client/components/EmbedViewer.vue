<template>
  <div class="h-full relative">
    <!-- Error message -->
    <div v-if="error" class="h-full flex items-center justify-center p-8">
      <div class="text-center">
        <FileX class="w-16 h-16 mx-auto text-theme-text-muted mb-4" />
        <h2 class="text-xl font-semibold text-theme-text mb-2">Failed to load embedded content</h2>
        <p class="text-theme-text-muted mb-4">{{ error }}</p>
        <div class="space-y-2">
          <button
            @click="retryLoad"
            class="inline-flex items-center px-4 py-2 bg-color-button-primary-bg text-color-button-primary-fg rounded-lg hover:bg-color-button-primary-hover-bg transition-colors mr-2"
          >
            <RefreshCw class="w-4 h-4 mr-2" />
            Retry
          </button>
          <a
            v-if="extractedUrl"
            :href="extractedUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            <ExternalLink class="w-4 h-4 mr-2" />
            Open in new tab
          </a>
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-else-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50">
      <div class="text-center">
        <Loader2 class="w-8 h-8 mx-auto text-theme-brand animate-spin mb-2" />
        <p class="text-sm text-theme-text-muted">Loading embedded content...</p>
      </div>
    </div>

    <!-- iframe container -->
    <div v-else class="h-full relative">
      <iframe
        v-if="extractedUrl"
        :src="extractedUrl"
        class="w-full h-full border-0"
        :class="{ 'opacity-50': isLoading }"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        referrerpolicy="no-referrer"
        @load="onIframeLoad"
        @error="onIframeError"
        title="Embedded content"
      ></iframe>
      
      <!-- Loading overlay for iframe -->
      <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-gray-900/50">
        <div class="text-center">
          <Loader2 class="w-8 h-8 mx-auto text-theme-brand animate-spin mb-2" />
          <p class="text-sm text-theme-text-muted">Loading embedded content...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { FileX, Loader2, RefreshCw, ExternalLink } from 'lucide-vue-next';

const props = defineProps({
  noteContent: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['error', 'loading', 'loaded']);

// State
const isLoading = ref(false);
const error = ref(null);
const extractedUrl = ref(null);

// Methods
function extractUrlFromContent(content) {
  if (!content) {
    throw new Error('No content provided');
  }

  // Split content into lines
  const lines = content.split('\n').map(line => line.trim()).filter(line => line);
  
  if (lines.length < 2) {
    throw new Error('Content must have at least 2 lines: title and URL');
  }

  // Get the second line (index 1) which should contain the URL
  const urlLine = lines[1];
  
  // Try to extract URL from markdown link format [text](url)
  const markdownLinkMatch = urlLine.match(/\[([^\]]+)\]\(([^)]+)\)/);
  if (markdownLinkMatch) {
    return markdownLinkMatch[2];
  }
  
  // Try to extract URL from plain text
  const urlMatch = urlLine.match(/https?:\/\/[^\s]+/);
  if (urlMatch) {
    return urlMatch[0];
  }
  
  // If no URL found, assume the entire line is a URL
  if (urlLine.startsWith('http://') || urlLine.startsWith('https://')) {
    return urlLine;
  }
  
  throw new Error('No valid URL found in the third line');
}

function validateUrl(url) {
  try {
    const urlObj = new URL(url);
    // Basic validation - ensure it's http or https
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      throw new Error('Only HTTP and HTTPS URLs are supported');
    }
    return url;
  } catch (err) {
    throw new Error(`Invalid URL: ${err.message}`);
  }
}

async function loadEmbeddedContent() {
  if (!props.noteContent) {
    error.value = 'No content provided';
    emit('error', error.value);
    return;
  }

  isLoading.value = true;
  error.value = null;
  emit('loading', true);

  try {
    // Extract URL from content
    const url = extractUrlFromContent(props.noteContent);
    
    // Validate URL
    const validatedUrl = validateUrl(url);
    
    extractedUrl.value = validatedUrl;
    
    // Small delay to show loading state
    await new Promise(resolve => setTimeout(resolve, 100));
    
    isLoading.value = false;
    emit('loaded', true);
    emit('loading', false);
    
  } catch (err) {
    console.error('Failed to load embedded content:', err);
    error.value = err.message;
    emit('error', error.value);
    isLoading.value = false;
    emit('loading', false);
  }
}

function onIframeLoad() {
  isLoading.value = false;
  emit('loaded', true);
  emit('loading', false);
}

function onIframeError() {
  error.value = 'Failed to load the embedded content. The website may not allow embedding.';
  emit('error', error.value);
  isLoading.value = false;
  emit('loading', false);
}

function retryLoad() {
  loadEmbeddedContent();
}

// Watch for content changes
watch(() => props.noteContent, () => {
  if (props.noteContent) {
    loadEmbeddedContent();
  }
}, { immediate: true });

// Lifecycle
onMounted(() => {
  if (props.noteContent) {
    loadEmbeddedContent();
  }
});
</script> 