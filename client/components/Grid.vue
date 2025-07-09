<template>
  <div class="flex h-full justify-center">
    <div class="flex flex-1 flex-col items-center" style="max-width: var(--layout-width-grid);">
      <Loading
        ref="loadingIndicator"
        class="flex min-h-56 flex-col items-center w-full"
        hideLoader
      >
        <!-- Sort Controls -->
        <div v-if="showSortControls" class="flex items-center justify-end w-full mb-2 space-x-2">
          <slot name="sort-controls" />
        </div>

        <!-- Grid Content -->
        <GridLayout
          :items="items"
          v-bind="$attrs"
          @tag-click="$emit('tag-click', $event)"
          @tag-dblclick="$emit('tag-dblclick', $event)"
          @tag-longpress="$emit('tag-longpress', $event)"
        />
      </Loading>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import Loading from "./Loading.vue";
import GridLayout from "./GridLayout.vue";

const props = defineProps({
  showSortControls: {
    type: Boolean,
    default: true
  },
  items: {
    type: Array,
    required: true
  }
});

defineEmits(['tag-click', 'tag-dblclick', 'tag-longpress']);

const loadingIndicator = ref();

// Expose loading methods for parent components
defineExpose({
  setLoading: () => loadingIndicator.value?.setLoading(),
  setLoaded: () => loadingIndicator.value?.setLoaded(),
  setFailed: () => loadingIndicator.value?.setFailed()
});
</script> 