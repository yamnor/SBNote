<template>
  <div class="relative">
    <!-- Trigger Button -->
    <button
      @click="toggleMenu"
      class="relative flex items-center justify-center w-10 h-10 rounded-lg bg-color-button-secondary-bg hover:bg-color-button-secondary-hover-bg hover:text-color-button-secondary-hover-fg text-color-button-secondary-fg transition-colors"
      :class="triggerClass"
    >
      <component :is="triggerIcon" class="w-6 h-6" />
      
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
import { ref, onMounted, onUnmounted, provide } from 'vue';

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

// Provide closeMenu function to child components
provide('closeDropdownMenu', closeMenu);

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