<template>
  <button
    @click="handleClick"
    class="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
    :class="itemClass"
  >
    <component v-if="icon" :is="icon" class="w-4 h-4 mr-3" />
    <slot />
  </button>
</template>

<script setup>
const props = defineProps({
  icon: {
    type: [String, Object, Function],
    default: null
  },
  itemClass: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['click']);

function handleClick(event) {
  emit('click', event);
}
</script> 