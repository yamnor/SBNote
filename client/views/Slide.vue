<template>
  <div class="slide-container">
    <Loading ref="loadingIndicator" class="h-screen">
      <div ref="revealContainer" class="reveal-container"></div>
    </Loading>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { FileX } from "lucide-vue-next";
import Reveal from 'reveal.js';
import 'reveal.js/dist/reveal.css';
import 'reveal.js/dist/theme/white.css';
import RevealMarkdown from 'reveal.js/plugin/markdown/markdown.esm.js';

import { getNote } from "../api.js";
import { noteConstants } from "../constants.js";
import Loading from "../components/Loading.vue";

const props = defineProps({
  filename: String,
});

const route = useRoute();
const router = useRouter();
const loadingIndicator = ref();
const revealContainer = ref();
let deck = null;
let note = ref({});

// Initialize reveal.js presentation
async function initializeReveal() {
  if (!revealContainer.value || !note.value.content) {
    return;
  }

  // Destroy existing deck if any
  if (deck) {
    deck.destroy();
    deck = null;
  }

  // Clear container
  revealContainer.value.innerHTML = '';

  // Create reveal.js structure using DOM manipulation
  createRevealStructure(note.value.content);

  // Wait for DOM to be ready
  await new Promise(resolve => setTimeout(resolve, 100));

  try {
    // Create new reveal.js instance
    deck = new Reveal(revealContainer.value.querySelector('.reveal'), {
      hash: true,
      transition: 'slide',
      transitionSpeed: 'default',
      backgroundTransition: 'fade',
      controls: true,
      progress: true,
      center: true,
      touch: true,
      loop: false,
      rtl: false,
      navigationMode: 'default',
      shuffle: false,
      fragments: true,
      fragmentInURL: false,
      embedded: false,
      help: true,
      showNotes: false,
      autoPlayMedia: null,
      preloadIframes: null,
      autoSlide: 0,
      autoSlideStoppable: true,
      autoSlideMethod: Reveal.navigateNext,
      defaultTiming: null,
      mouseWheel: false,
      hideInactiveCursor: true,
      hideCursorTime: 5000,
      previewLinks: false,
      postMessage: true,
      postMessageEvents: false,
      focusBodyOnPageVisibilityChange: true,
      viewDistance: 3,
      mobileViewDistance: 2,
      display: 'block',
      hideEmptyElements: true,
      plugins: [RevealMarkdown]
    });

    // Initialize the presentation
    deck.initialize();
  } catch (error) {
    console.error('Failed to initialize reveal.js:', error);
  }
}

// Create reveal.js structure with markdown content using DOM manipulation
function createRevealStructure(markdown) {
  // Split content by slide separators (--- or horizontal rules)
  const slideSeparators = /^---\s*$/gm;
  const slides = markdown.split(slideSeparators);
  
  // Create reveal container
  const revealDiv = document.createElement('div');
  revealDiv.className = 'reveal';
  
  const slidesDiv = document.createElement('div');
  slidesDiv.className = 'slides';
  
  // If no slide separators found, treat the entire content as one slide
  if (slides.length === 1) {
    const section = document.createElement('section');
    section.setAttribute('data-markdown', '');
    
    const script = document.createElement('script');
    script.setAttribute('type', 'text/template');
    script.textContent = markdown;
    
    section.appendChild(script);
    slidesDiv.appendChild(section);
  } else {
    // Convert each slide to reveal.js format
    slides.forEach((slide, index) => {
      const trimmedSlide = slide.trim();
      if (!trimmedSlide) return;
      
      const section = document.createElement('section');
      section.setAttribute('data-markdown', '');
      
      const script = document.createElement('script');
      script.setAttribute('type', 'text/template');
      script.textContent = trimmedSlide;
      
      section.appendChild(script);
      slidesDiv.appendChild(section);
    });
  }
  
  revealDiv.appendChild(slidesDiv);
  revealContainer.value.appendChild(revealDiv);
}

// Load note content
async function loadNote() {
  if (!props.filename) {
    loadingIndicator.value.setFailed("No filename provided", FileX);
    return;
  }

  try {
    // Add .md extension for API call
    const filenameWithExtension = props.filename + noteConstants.MARKDOWN_EXTENSION;
    const data = await getNote(filenameWithExtension);
    
    note.value = data;
    
    if (data.title && data.title.trim()) {
      document.title = `${data.title} - Slide - SBNote`;
    }
    
    loadingIndicator.value.setLoaded();
    
    // Wait for DOM to be ready before initializing reveal.js
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Initialize reveal.js after content is loaded and DOM is ready
    await initializeReveal();
  } catch (error) {
    console.error('Failed to load note:', error);
    if (error.response?.status === 404) {
      loadingIndicator.value.setFailed("Note not found", FileX);
    } else {
      loadingIndicator.value.setFailed();
    }
  }
}

// Watch for filename changes
watch(() => props.filename, async () => {
  await loadNote();
});

// Handle keyboard shortcuts
function handleKeydown(event) {
  if (!deck) return;

  switch (event.key) {
    case 'Escape':
      // Exit fullscreen and go back to note
      router.push({ name: 'note', params: { filename: props.filename } });
      break;
    case 'f':
      // Toggle fullscreen
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen();
      }
      break;
  }
}

onMounted(async () => {
  await loadNote();
  
  // Add keyboard event listener
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  // Clean up reveal.js
  if (deck) {
    deck.destroy();
    deck = null;
  }
  
  // Remove keyboard event listener
  document.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.slide-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 9999;
  background: white;
}

.reveal-container {
  width: 100%;
  height: 100vh;
  position: relative;
}

/* Override reveal.js styles for better integration */
:deep(.reveal) {
  font-family: inherit;
  height: 100vh;
}

:deep(.reveal .slides) {
  height: 100vh;
}

:deep(.reveal .slides section) {
  text-align: left;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

:deep(.reveal .slides section h1),
:deep(.reveal .slides section h2),
:deep(.reveal .slides section h3),
:deep(.reveal .slides section h4),
:deep(.reveal .slides section h5),
:deep(.reveal .slides section h6) {
  color: #333;
  margin-bottom: 0.5em;
}

:deep(.reveal .slides section p) {
  margin-bottom: 0.5em;
}

:deep(.reveal .slides section code) {
  background-color: #f5f5f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

:deep(.reveal .slides section pre) {
  background-color: #f5f5f5;
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}

:deep(.reveal .slides section blockquote) {
  border-left: 4px solid #ccc;
  padding-left: 1em;
  margin-left: 0;
  color: #666;
}

:deep(.reveal .slides section ul),
:deep(.reveal .slides section ol) {
  margin-bottom: 0.5em;
}

:deep(.reveal .slides section li) {
  margin-bottom: 0.2em;
}

/* Loading indicator positioning */
:deep(.loading-container) {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
</style> 