<template>
  <div class="flex h-full justify-center">
    <div class="flex flex-1 flex-col items-center" style="max-width: var(--layout-width-grid);">
      <Loading
        v-if="showLoading"
        ref="loadingIndicator"
        class="flex flex-col items-center w-full"
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
        />
      </Loading>
      
      <!-- Grid Content without Loading wrapper -->
      <div v-else class="w-full">
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
        />
      </div>
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
  },
  showLoading: {
    type: Boolean,
    default: true
  }
});

defineEmits(['tag-click', 'tag-dblclick']);

const loadingIndicator = ref();

// Expose loading methods for parent components
defineExpose({
  setLoading: () => loadingIndicator.value?.setLoading(),
  setLoaded: () => loadingIndicator.value?.setLoaded(),
  setFailed: () => loadingIndicator.value?.setFailed()
});
</script> 