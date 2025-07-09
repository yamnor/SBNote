<template>
  <div class="relative">
    <!-- Trigger Button -->
    <button
      @click="toggleMenu"
      class="relative flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--theme-button)] hover:bg-[var(--theme-brand)] hover:text-white text-theme-text transition-colors shadow-sm"
      :class="triggerClass"
    >
      <component :is="triggerIcon" class="w-4 h-4" />
      
      <!-- Indicator Slot -->
      <slot name="indicator" />
    </button>
    
    <!-- Dropdown Menu -->
    <div
      v-if="isOpen"
      class="absolute mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
      :class="[
        menuClass,
        menuPosition === 'left' ? 'left-0' : 'right-0'
      ]"
    >
      <div class="py-1">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  triggerIcon: {
    type: [String, Object, Function],
    required: true
  },
  triggerClass: {
    type: String,
    default: ''
  },
  menuClass: {
    type: String,
    default: ''
  },
  menuPosition: {
    type: String,
    default: 'right',
    validator: (value) => ['left', 'right'].includes(value)
  },
  closeOnClickOutside: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['open', 'close']);

const isOpen = ref(false);

function toggleMenu() {
  isOpen.value = !isOpen.value;
  emit(isOpen.value ? 'open' : 'close');
}

function closeMenu() {
  isOpen.value = false;
  emit('close');
}

// Close menu when clicking outside
function handleClickOutside(event) {
  if (!props.closeOnClickOutside) return;
  
  const dropdownContainer = event.target.closest('.relative');
  
  if (!dropdownContainer && isOpen.value) {
    closeMenu();
  }
}

onMounted(() => {
  if (props.closeOnClickOutside) {
    document.addEventListener('click', handleClickOutside);
  }
});

onUnmounted(() => {
  if (props.closeOnClickOutside) {
    document.removeEventListener('click', handleClickOutside);
  }
});

// Expose methods for parent components
defineExpose({ 
  open: () => { isOpen.value = true; emit('open'); },
  close: closeMenu,
  toggle: toggleMenu
});
</script> 