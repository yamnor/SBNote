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
        :class="{ 
          'opacity-50': isLoading,
          'opacity-50 pointer-events-none': isResizing 
        }"
        @mousedown.stop
        @mousemove.stop
        @mouseup.stop
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
        ref="terminalPanel"
        :class="[
          'absolute bottom-0 left-0 right-0 z-toolbar border-t border-color-border-primary terminal-panel',
          isTerminalMinimized ? 'h-12 min-h-[40px] backdrop-blur-md' : 'backdrop-blur-md'
        ]"
        :style="!isTerminalMinimized ? { height: `${terminalHeight}px`, zIndex: 30 } : { zIndex: 30 }"
      >
        <!-- Resize handle -->
        <div 
          v-if="!isTerminalMinimized"
          class="absolute top-0 left-0 right-0 h-1 hover:bg-color-border-primary cursor-ns-resize transition-colors"
          @mousedown.stop="startResize"
          title="Drag to resize terminal"
        ></div>
        <!-- Minimize/Restore Button -->
        <button 
          @click.stop="toggleTerminal"
          class="absolute top-2 right-2 flex items-center justify-center w-8 h-8 rounded-full bg-color-button-secondary-bg hover:bg-color-button-secondary-hover-bg border border-color-border-primary transition-colors focus:outline-none"
          :title="isTerminalMinimized ? 'Restore Terminal' : 'Minimize Terminal'"
          style="z-index:30;"
        >
          <ChevronUp v-if="isTerminalMinimized" class="w-5 h-5 text-color-button-secondary-fg hover:text-color-button-secondary-hover-fg" />
          <ChevronDown v-else class="w-6 h-6 text-color-button-secondary-fg hover:text-color-button-secondary-hover-fg" />
        </button>
        <div v-show="!isTerminalMinimized" ref="terminalContainer" class="w-full h-full pt-1"></div>
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

// Props
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
const terminalPanel = ref(null);
const isLoading = ref(false);
const error = ref(null);
const showTerminal = ref(true);
let viewer = null;
let terminal = null;
let fitAddon = null;
const isTerminalMinimized = ref(false);
const currentLine = ref('');
const commandHistory = ref([]);
const historyIndex = ref(-1);
const molecularData = ref(null); // Store molecular data from ccget

// Resize state
const terminalHeight = ref(300); // Default 30% of screen height
const isResizing = ref(false);
const resizeStartY = ref(0);
const resizeStartHeight = ref(0);
let resizeObserver = null; // Store resize observer reference

// Command parsing function
function parseCommand(input) {
  const trimmed = input.trim();
  
  // ccgetコマンドの識別（大文字小文字無視）
  if (trimmed.toLowerCase().startsWith('ccget ')) {
    const attributes = trimmed.substring(6).trim();
    // ccget helpの場合は特別処理
    if (attributes.toLowerCase() === 'help') {
      return { type: 'ccget_help' };
    }
    return {
      type: 'ccget',
      attributes: attributes.split(/\s+/), // スペース区切り
      original: trimmed
    };
  }
  
  // miewコマンドの識別
  if (trimmed.toLowerCase().startsWith('miew ')) {
    return {
      type: 'miew',
      command: trimmed.substring(5).trim(),
      original: trimmed
    };
  }
  
  // ヘルプコマンド（直接入力）
  if (trimmed.toLowerCase() === 'ccget help') {
    return { type: 'ccget_help' };
  }
  
  if (trimmed.toLowerCase() === 'miew help') {
    return { type: 'miew_help' };
  }
  
  // clearコマンド
  if (trimmed.toLowerCase() === 'clear') {
    return { type: 'clear' };
  }
  
  // 認識されないコマンドはエラーとして扱う
  return {
    type: 'unknown',
    command: trimmed,
    original: trimmed
  };
}

// Display array data with formatting
function displayArray(arr, indent = '  ') {
  if (arr.length === 0) {
    terminal.writeln(`${indent}[]`);
    return;
  }
  
  if (arr.length <= 10) {
    arr.forEach((item, index) => {
      if (typeof item === 'number') {
        terminal.writeln(`${indent}[${index}]: ${item.toFixed(6)}`);
      } else {
        terminal.writeln(`${indent}[${index}]: ${item}`);
      }
    });
  } else {
    // Show first 5 and last 5 elements
    for (let i = 0; i < 5; i++) {
      const item = arr[i];
      if (typeof item === 'number') {
        terminal.writeln(`${indent}[${i}]: ${item.toFixed(6)}`);
      } else {
        terminal.writeln(`${indent}[${i}]: ${item}`);
      }
    }
    terminal.writeln(`${indent}...`);
    for (let i = arr.length - 5; i < arr.length; i++) {
      const item = arr[i];
      if (typeof item === 'number') {
        terminal.writeln(`${indent}[${i}]: ${item.toFixed(6)}`);
      } else {
        terminal.writeln(`${indent}[${i}]: ${item}`);
      }
    }
  }
}

// Display object data with formatting
function displayObject(obj, indent = '  ') {
  const keys = Object.keys(obj);
  if (keys.length === 0) {
    terminal.writeln(`${indent}{}`);
    return;
  }
  
  keys.slice(0, 10).forEach(key => {
    const value = obj[key];
    if (typeof value === 'number') {
      terminal.writeln(`${indent}${key}: ${value.toFixed(6)}`);
    } else if (Array.isArray(value)) {
      terminal.writeln(`${indent}${key}: Array[${value.length}]`);
      if (value.length > 0 && value.length <= 5) {
        displayArray(value, indent + '  ');
      }
    } else {
      terminal.writeln(`${indent}${key}: ${value}`);
    }
  });
  
  if (keys.length > 10) {
    terminal.writeln(`${indent}... and ${keys.length - 10} more properties`);
  }
}

// Display ccget results with formatting
function displayCcgetResults(data, requestedAttrs) {
  requestedAttrs.forEach(attr => {
    const value = data[attr.toLowerCase()];
    
    if (value === null || value === undefined) {
      terminal.writeln(`\x1b[1;33m${attr}: \x1b[0m\x1b[3mNot available\x1b[0m`);
      return;
    }
    
    terminal.writeln(`\x1b[1;32m${attr}:\x1b[0m`);
    
    // データサイズに応じた表示制限
    if (Array.isArray(value)) {
      if (value.length > 100) {
        terminal.writeln(`  Array[${value.length}] - showing first 100 elements:`);
        displayArray(value.slice(0, 100));
        terminal.writeln(`  ... and ${value.length - 100} more elements`);
      } else {
        displayArray(value);
      }
    } else if (typeof value === 'object' && value !== null) {
      displayObject(value);
    } else {
      terminal.writeln(`  ${value}`);
    }
    terminal.writeln('');
  });
}

// Execute ccget command
async function executeCcgetCommand(attributes) {
  try {
    
    // 属性名を大文字小文字無視で正規化
    const normalizedAttrs = attributes.map(attr => attr.toLowerCase());
    
    // Extract basename from attachment filename
    const basename = props.attachmentFilename.split('/')[0];
    
    // API呼び出し
    const response = await fetch(`/api/ccget/${basename}?attributes=${normalizedAttrs.join(',')}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      if (response.status === 404) {
        terminal.writeln('\x1b[1;31mError: Molecular data file not found\x1b[0m');
      } else if (response.status === 500) {
        terminal.writeln('\x1b[1;31mError: Server error processing molecular data\x1b[0m');
      } else {
        terminal.writeln(`\x1b[1;31mError: ${errorData.detail}\x1b[0m`);
      }
      // エラー時もプロンプトを表示
      terminal.write('\x1b[1;32m>\x1b[0m ');
      return;
    }
    
    const data = await response.json();
    
    // Store molecular data for potential use
    molecularData.value = data;
    
    // 整形表示
    displayCcgetResults(data, attributes);
    
    // 処理完了後にプロンプトを表示
    terminal.write('\x1b[1;32m>\x1b[0m ');
    
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      terminal.writeln('\x1b[1;31mError: Network connection failed\x1b[0m');
    } else {
      terminal.writeln(`\x1b[1;31mError: ${error.message}\x1b[0m`);
    }
    // エラー時もプロンプトを表示
    terminal.write('\x1b[1;32m>\x1b[0m ');
  }
}

// Show ccget help
function showCcgetHelp() {
  terminal.writeln('Usage: ccget <attribute1> [<attribute2> ...]');
  terminal.writeln('');
  terminal.writeln('Available attributes:');
  terminal.writeln('  xyz          - Molecular coordinates in XYZ format');
  terminal.writeln('  natom        - Number of atoms');
  terminal.writeln('  atomnos      - Atomic numbers');
  terminal.writeln('  atomcoords   - Atomic coordinates');
  terminal.writeln('  atommasses   - Atomic masses');
  terminal.writeln('  charge       - Total charge');
  terminal.writeln('  mult         - Multiplicity');
  terminal.writeln('  energy       - Total energy');
  terminal.writeln('  scfenergies  - SCF energies');
  terminal.writeln('  vibfreqs     - Vibrational frequencies');
  terminal.writeln('  ... and more');
  terminal.writeln('');
  terminal.writeln('Examples:');
  terminal.writeln('  ccget xyz');
  terminal.writeln('  ccget natom atomnos');
  terminal.writeln('  ccget energy scfenergies');
  // ヘルプ表示後にプロンプトを表示
  terminal.write('\x1b[1;32m>\x1b[0m ');
}

// Show miew help
function showMiewHelp() {
  terminal.writeln('Usage: miew <command>');
  terminal.writeln('');
  terminal.writeln('Available commands:');
  terminal.writeln('  load <file>     - Load molecular file');
  terminal.writeln('  show            - Show current molecule');
  terminal.writeln('  hide            - Hide current molecule');
  terminal.writeln('  color <scheme>  - Set color scheme');
  terminal.writeln('  style <style>   - Set representation style');
  terminal.writeln('  reset           - Reset view');
  terminal.writeln('  help            - Show this help');
  terminal.writeln('');
  terminal.writeln('Examples:');
  terminal.writeln('  miew show');
  terminal.writeln('  miew color cpk');
  terminal.writeln('  miew style ball');
  // ヘルプ表示後にプロンプトを表示
  terminal.write('\x1b[1;32m>\x1b[0m ');
}

// Show unknown command error
function showUnknownCommandError(command) {
  terminal.writeln(`\x1b[1;31mError: Unknown command '${command}'\x1b[0m`);
  terminal.writeln('\x1b[1;33mAvailable commands:\x1b[0m');
  terminal.writeln('  ccget <attributes>  - Get molecular data attributes');
  terminal.writeln('  miew <command>      - Execute Miew viewer command');
  terminal.writeln('  clear               - Clear terminal screen');
  terminal.writeln('  ccget help          - Show ccget help');
  terminal.writeln('  miew help           - Show miew help');
  terminal.writeln('');
  terminal.writeln('Examples:');
  terminal.writeln('  ccget natom scfenergies');
  terminal.writeln('  miew show');
  terminal.writeln('  miew color cpk');
  // エラー表示後にプロンプトを表示
  terminal.write('\x1b[1;32m>\x1b[0m ');
}

// Execute clear command
function executeClearCommand() {
  // ターミナルの画面をクリア
  terminal.clear();
    
  // プロンプトを表示
  terminal.write('\x1b[1;32m>\x1b[0m ');
}

// Format Miew help output
function formatMiewHelpOutput(output) {
  // 出力を改行で分割
  const lines = output.split('\n');
  
  lines.forEach(line => {
    // 行の前後の空白を削除
    const trimmedLine = line.trim();
    
    if (trimmedLine) {
      // 長い行を適切に折り返し
      if (trimmedLine.length > 80) {
        // 80文字で折り返し
        const words = trimmedLine.split(' ');
        let currentLine = '';
        
        words.forEach(word => {
          if ((currentLine + word).length > 80) {
            if (currentLine) {
              terminal.writeln(currentLine.trim());
              currentLine = word + ' ';
            } else {
              // 単語が80文字を超える場合は強制改行
              terminal.writeln(word);
            }
          } else {
            currentLine += word + ' ';
          }
        });
        
        if (currentLine.trim()) {
          terminal.writeln(currentLine.trim());
        }
      } else {
        terminal.writeln(trimmedLine);
      }
    }
  });
  
  // ヘルプ表示後に改行を追加してプロンプトとの間隔を確保
  terminal.writeln('');
}

// Execute miew command
function executeMiewCommand(command) {
  if (!command.trim()) {
    // 空のコマンドの場合は何もしない（プロンプトは既に表示されている）
    return;
  }
  
  if (viewer && typeof viewer.script === 'function') {
    try {
      viewer.script(command, (str) => {
        // helpコマンドの場合は整形して表示
        if (command.toLowerCase() === 'help') {
          formatMiewHelpOutput(str);
        } else {
          terminal.writeln(str);
        }
      }, (str) => {
        terminal.writeln(`\x1b[1;31mError: ${str}\x1b[0m`);
      });
      
      // helpコマンドの場合は特別な処理
      if (command.toLowerCase() === 'help') {
        // helpコマンドの場合は非同期でプロンプトを表示
        setTimeout(() => {
          terminal.write('\x1b[1;32m>\x1b[0m ');
        }, 100);
      } else {
        // その他のコマンドは即座にプロンプトを表示
        terminal.write('\x1b[1;32m>\x1b[0m ');
      }
    } catch (err) {
      terminal.writeln(`\x1b[1;31mError: ${err.message}\x1b[0m`);
      // エラー時もプロンプトを表示
      terminal.write('\x1b[1;32m>\x1b[0m ');
    }
  } else {
    terminal.writeln('\x1b[1;31mError: Miew viewer not available\x1b[0m');
    // エラー時もプロンプトを表示
    terminal.write('\x1b[1;32m>\x1b[0m ');
  }
}

// Handle command execution
async function handleCommand(command) {
  if (!command.trim()) {
    // 空のコマンドの場合は何もしない（プロンプトは既に表示されている）
    return;
  }
  
  // 履歴に保存
  commandHistory.value.push(command);
  historyIndex.value = -1;
  
  const parsed = parseCommand(command);
  
  switch (parsed.type) {
    case 'ccget':
      await executeCcgetCommand(parsed.attributes);
      break;
    case 'miew':
      executeMiewCommand(parsed.command);
      break;
    case 'ccget_help':
      showCcgetHelp();
      break;
    case 'miew_help':
      showMiewHelp();
      break;
    case 'clear':
      executeClearCommand();
      break;
    case 'unknown':
      showUnknownCommandError(parsed.command);
      break;
  }
}

// Terminal command history
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
    currentLine.value = historyCommand;
  } else {
    currentLine.value = '';
  }
  terminal.write('\x1b[1;32m>\x1b[0m ');
}

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
        bg: { color: '#ffffff' },
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
    
    // Check if this is a pickle file and use ccget API
    if (fileExtension === 'pkl') {
      await loadMoleculeFromPickle();
    } else {
      // Use existing logic for other file formats
      await loadMoleculeFromFile();
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

async function loadMoleculeFromPickle() {
  // Extract basename from attachment filename
  const basename = props.attachmentFilename.split('/')[0];
  
  try {
    // Get molecular data from ccget API
    const response = await fetch(`/api/ccget/${basename}?attributes=xyz,natom,atomnos,scfenergies`);
    if (!response.ok) {
      throw new Error(`Failed to fetch molecular data: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.xyz) {
      throw new Error('XYZ data not available in pickle file');
    }
    
    // Load XYZ content into Miew
    if (typeof viewer.load === 'function') {
      // Create a blob URL for the XYZ content
      const blob = new Blob([data.xyz], { type: 'chemical/x-xyz' });
      const url = URL.createObjectURL(blob);
      
      try {
        await viewer.load(url);
      } finally {
        // Clean up the blob URL
        URL.revokeObjectURL(url);
      }
    }
    
    // Store additional molecular data for terminal commands
    if (data.natom) {
      viewer.molecularInfo = {
        atomCount: data.natom,
        atomicNumbers: data.atomnos,
        energies: data.scfenergies
      };
    }
    
    // Store molecular data for ccget commands
    molecularData.value = data;
    
  } catch (err) {
    console.error('Failed to load molecule from pickle:', err);
    throw err;
  }
}

async function loadMoleculeFromFile() {
  // Load file data based on format
  let format = 'pdb'; // Default format
  const fileExtension = props.attachmentFilename.split('.').pop().toLowerCase();
  
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
}

function retryLoad() {
  loadMolecule();
}

function toggleTerminal() {
  isTerminalMinimized.value = !isTerminalMinimized.value;
  
  // Set default height (30%) when restoring from minimized state
  if (!isTerminalMinimized.value && terminalHeight.value < 100) {
    terminalHeight.value = window.innerHeight * 0.3;
  }
}

// Resize functions
function startResize(event) {
  isResizing.value = true;
  resizeStartY.value = event.clientY;
  resizeStartHeight.value = terminalHeight.value;
  
  // Disconnect resize observer during resize to prevent interference
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
  
  // Add resizing class to disable transitions
  if (terminalPanel.value) {
    terminalPanel.value.classList.add('resizing');
  }
  
  // Disable xterm.js resize handling during resize
  if (terminal && typeof terminal.resize === 'function') {
    // Store current terminal size to prevent auto-resize
    const currentCols = terminal.cols;
    const currentRows = terminal.rows;
    terminal.resize(currentCols, currentRows);
  }
  
  // Disable Miew hot keys and focus during resize
  if (viewer && typeof viewer.enableHotKeys === 'function') {
    viewer.enableHotKeys(false);
  }
  
  // Focus terminal to prevent Miew from stealing focus
  if (terminal) {
    terminal.focus();
  }
  
  // Add global event listeners with capture to ensure they're called first
  document.addEventListener('mousemove', handleResize, { capture: true });
  document.addEventListener('mouseup', stopResize, { capture: true });
  
  // Set cursor style
  document.body.style.cursor = 'ns-resize';
  document.body.style.userSelect = 'none';
  
  // Stop event propagation to prevent Miew from handling the event
  event.stopPropagation();
  event.preventDefault();
}

function handleResize(event) {
  if (!isResizing.value) return;
  
  const deltaY = resizeStartY.value - event.clientY;
  const newHeight = resizeStartHeight.value + deltaY;
  
  // Apply height constraints
  const minHeight = 100;
  const maxHeight = window.innerHeight * 0.9;
  const clampedHeight = Math.max(minHeight, Math.min(maxHeight, newHeight));
  
  // Direct DOM manipulation to avoid Vue reactivity delays
  if (terminalPanel.value) {
    terminalPanel.value.style.height = `${clampedHeight}px`;
  }
  
  // Update Vue state for consistency
  terminalHeight.value = clampedHeight;
}

function stopResize() {
  isResizing.value = false;
  
  // Remove global event listeners with capture
  document.removeEventListener('mousemove', handleResize, { capture: true });
  document.removeEventListener('mouseup', stopResize, { capture: true });
  
  // Restore cursor style
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
  
  // Remove resizing class to re-enable transitions
  if (terminalPanel.value) {
    terminalPanel.value.classList.remove('resizing');
  }
  
  // Re-enable Miew hot keys
  if (viewer && typeof viewer.enableHotKeys === 'function') {
    viewer.enableHotKeys(true);
  }
  
  // Reconnect resize observer to terminal panel
  if (resizeObserver && terminalPanel.value) {
    resizeObserver.observe(terminalPanel.value);
  }
  
  // Force xterm.js to recalculate size with a delay to ensure DOM is stable
  setTimeout(() => {
    if (fitAddon) {
      fitAddon.fit();
    }
  }, 50);
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
      fontSize: 14,
      fontFamily: 'Noto Sans Mono, Consolas, Lucida Console, Monaco, monospace',
      theme: {
        background: '#ffffff',
        foreground: '#000000',
        cursor: '#3ea8ff',
        brightGreen: '#10b981',
        selectionBackground: '#e0efff',
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
    terminal.write('\x1b[1;32m>\x1b[0m ');
    
    // Handle input
    terminal.onData((data) => {
      const code = data.charCodeAt(0);
      
      if (code === 13) { // Enter
        if (currentLine.value.trim()) {
          // コマンドが入力されている場合のみ改行
          terminal.write('\r\n');
        }
        handleCommand(currentLine.value);
        currentLine.value = '';
        // プロンプトは非同期処理完了後に表示される（空のコマンドの場合は除く）
      } else if (code === 127) { // Backspace
        if (currentLine.value.length > 0) {
          currentLine.value = currentLine.value.slice(0, -1);
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
        currentLine.value += data;
        terminal.write(data);
      }
    });
    
    // Handle window resize - simplified to only handle non-resize events
    resizeObserver = new ResizeObserver(() => {
      // Only fit if not currently resizing and terminal is ready
      if (fitAddon && !isResizing.value && terminal) {
        // Small delay to ensure DOM is stable
        setTimeout(() => {
          if (!isResizing.value) {
            fitAddon.fit();
          }
        }, 10);
      }
    });
    resizeObserver.observe(terminalPanel.value);
    
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
  
  // Disconnect resize observer
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
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
  // Set default height to 30% of screen height
  terminalHeight.value = window.innerHeight * 0.3;
  
  // Handle window resize
  const handleWindowResize = () => {
    if (!isTerminalMinimized.value) {
      // Adjust height if it exceeds maximum
      const maxHeight = window.innerHeight * 0.9;
      if (terminalHeight.value > maxHeight) {
        terminalHeight.value = maxHeight;
      }
    }
  };
  
  window.addEventListener('resize', handleWindowResize);
  
  // Cleanup
  onUnmounted(() => {
    window.removeEventListener('resize', handleWindowResize);
  });
  
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

/* Resize handle styles */
.resize-handle {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background-color: #d1d5db;
  cursor: ns-resize;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background-color: #9ca3af;
}

/* Resizing state */
.resizing {
  user-select: none;
  transition: none !important;
}

/* Terminal panel styles */
.terminal-panel {
  transition: height 0.2s ease;
}

.terminal-panel.resizing {
  transition: none !important;
}

/* Miew viewer during resize */
.miew-viewer-resizing {
  opacity: 0.5;
  pointer-events: none;
}
</style> 