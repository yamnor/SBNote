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
          class="inline-flex items-center px-4 py-2 bg-color-button-primary-bg text-color-button-primary-fg rounded-lg hover:bg-color-button-primary-hover-bg transition-colors"
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

      <!-- Terminal panel -->
      <div
        v-if="showTerminal"
        :class="[
          'absolute bottom-0 left-0 right-0 z-20 border-t border-gray-700',
          isTerminalMinimized ? 'h-12 min-h-[40px] bg-gray-900/50 backdrop-blur-sm' : 'h-64 bg-gray-900/50 backdrop-blur-sm'
        ]"
      >
        <!-- Minimize/Restore Button -->
        <button
          @click.stop="toggleTerminal"
          class="absolute top-2 right-2 flex items-center justify-center w-8 h-8 rounded-full bg-gray-800/80 hover:bg-gray-700 border border-gray-600 shadow transition-colors focus:outline-none"
          :title="isTerminalMinimized ? 'Restore Terminal' : 'Minimize Terminal'"
          style="z-index:21;"
        >
          <ChevronUp v-if="isTerminalMinimized" class="w-5 h-5 text-gray-200" />
          <ChevronDown v-else class="w-5 h-5 text-gray-200" />
        </button>
        <div v-show="!isTerminalMinimized" ref="terminalContainer" class="w-full h-full"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { FileX, Loader2, RefreshCw, Terminal, X, ChevronDown, ChevronUp } from 'lucide-vue-next';
import Miew from 'miew';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';

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
const terminalContainer = ref(null);
const isLoading = ref(false);
const error = ref(null);
const showTerminal = ref(true);
let viewer = null;
let terminal = null;
let fitAddon = null;
const isTerminalMinimized = ref(false);

// Terminal command history
const commandHistory = ref([]);
const historyIndex = ref(-1);

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
        bg: { color: '#000000' },
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
      let mimeType = 'text/plain';
      if (fileExtension === 'xyz') {
        mimeType = 'chemical/x-xyz';
      } else if (fileExtension === 'pdb') {
        mimeType = 'chemical/x-pdb';
      } else if (fileExtension === 'mol' || fileExtension === 'sdf') {
        mimeType = 'chemical/x-mdl-molfile';
      }
      
      // Ensure proper line endings for Miew
      let processedContent = props.fileContent;
      if (!processedContent.endsWith('\n')) {
        processedContent += '\n';
      }
      
      const blob = new Blob([processedContent], { type: mimeType });
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
    
    // Initialize terminal after viewer is ready
    if (showTerminal.value) {
      initializeTerminal();
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

function toggleTerminal() {
  isTerminalMinimized.value = !isTerminalMinimized.value;
}

function initializeTerminal() {
  if (!terminalContainer.value || !viewer) return;
  
  try {
    // Clear any existing terminal
    if (terminal) {
      destroyTerminal();
    }
    
    // Create new xterm.js terminal
    terminal = new XTerm({
      cursorBlink: true,
      fontSize: 12,
      fontFamily: 'Noto Sans Mono, Consolas, Lucida Console, Monaco, monospace',
      theme: {
        background: '#1f2937',
        foreground: '#f9fafb',
        cursor: '#f9fafb',
        selection: '#374151',
        black: '#000000',
        red: '#ef4444',
        green: '#10b981',
        yellow: '#f59e0b',
        blue: '#3b82f6',
        magenta: '#8b5cf6',
        cyan: '#06b6d4',
        white: '#f9fafb',
        brightBlack: '#6b7280',
        brightRed: '#f87171',
        brightGreen: '#34d399',
        brightYellow: '#fbbf24',
        brightBlue: '#60a5fa',
        brightMagenta: '#a78bfa',
        brightCyan: '#22d3ee',
        brightWhite: '#ffffff'
      }
    });
    
    // Add addons
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.loadAddon(new WebLinksAddon());
    
    // Open terminal
    terminal.open(terminalContainer.value);
    fitAddon.fit();
    
    // Write welcome message
    terminal.writeln('\x1b[1;32mMiew - 3D Molecular Viewer\x1b[0m');
    terminal.writeln('\x1b[3;36mCopyright © 2015-2024 EPAM Systems, Inc.\x1b[0m');
    terminal.writeln('');
    terminal.write('\x1b[1;32mmiew>\x1b[0m ');
    
    // Handle input
    let currentLine = '';
    terminal.onData((data) => {
      const code = data.charCodeAt(0);
      
      if (code === 13) { // Enter
        handleCommand(currentLine);
        currentLine = '';
        terminal.write('\r\n\x1b[1;32mmiew>\x1b[0m ');
      } else if (code === 127) { // Backspace
        if (currentLine.length > 0) {
          currentLine = currentLine.slice(0, -1);
          terminal.write('\b \b');
        }
      } else if (code === 27) { // Escape sequence
        // Handle arrow keys
        if (data.length > 2) {
          const arrowCode = data.charCodeAt(2);
          if (arrowCode === 65) { // Up arrow
            navigateHistory('up');
          } else if (arrowCode === 66) { // Down arrow
            navigateHistory('down');
          }
        }
      } else if (code >= 32) { // Printable characters
        currentLine += data;
        terminal.write(data);
      }
    });
    
    // Handle window resize
    const resizeObserver = new ResizeObserver(() => {
      if (fitAddon) {
        fitAddon.fit();
      }
    });
    resizeObserver.observe(terminalContainer.value);
    
    // Focus the terminal
    terminal.focus();
    
    // Disable hot keys to prevent conflicts
    if (typeof viewer.enableHotKeys === 'function') {
      viewer.enableHotKeys(false);
    }
    
  } catch (err) {
    console.error('Failed to initialize terminal:', err);
  }
}

function handleCommand(command) {
  if (!command.trim()) return;
  
  // Add to history
  commandHistory.value.push(command);
  historyIndex.value = -1;
  
  // Execute command through Miew
  if (viewer && typeof viewer.script === 'function') {
    try {
      viewer.script(command, (str) => {
        terminal.writeln(str);
      }, (str) => {
        terminal.writeln(`\x1b[1;31mError: ${str}\x1b[0m`);
      });
    } catch (err) {
      terminal.writeln(`\x1b[1;31mError: ${err.message}\x1b[0m`);
    }
  } else {
    terminal.writeln('\x1b[1;31mError: Miew viewer not available\x1b[0m');
  }
}

function navigateHistory(direction) {
  if (commandHistory.value.length === 0) return;
  
  if (direction === 'up') {
    if (historyIndex.value < commandHistory.value.length - 1) {
      historyIndex.value++;
    }
  } else if (direction === 'down') {
    if (historyIndex.value > 0) {
      historyIndex.value--;
    } else if (historyIndex.value === 0) {
      historyIndex.value = -1;
    }
  }
  
  // Clear current line and show history item
  terminal.write('\r\x1b[K'); // Clear line
  if (historyIndex.value >= 0) {
    const historyCommand = commandHistory.value[commandHistory.value.length - 1 - historyIndex.value];
    terminal.write(historyCommand);
    // Update currentLine (this would need to be handled in the main input handler)
  }
  terminal.write('\x1b[1;32mmiew>\x1b[0m ');
}

function destroyTerminal() {
  if (terminal) {
    try {
      terminal.dispose();
    } catch (e) {
      console.warn('Could not dispose terminal:', e);
    }
    terminal = null;
    fitAddon = null;
  }
  
  // Re-enable hot keys
  if (viewer && typeof viewer.enableHotKeys === 'function') {
    viewer.enableHotKeys(true);
  }
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
  // Clean up terminal
  destroyTerminal();
  
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

/* xterm.js custom styles */
.xterm {
  padding: 8px;
  background: transparent !important;
}

.xterm .xterm-viewport {
  overflow-y: hidden;
  background-color: transparent !important;
}

</style> 