<template>
  <div ref="viewerElement" class="w-full"></div>
</template>

<script setup>
import Viewer from "@toast-ui/editor/dist/toastui-editor-viewer";
import { onMounted, ref, watch } from "vue";

import baseOptions from "./ToastUIEditorOptions.js";

const props = defineProps({
  initialValue: String
});

const emit = defineEmits([]);

const viewerElement = ref();
let viewer = null;

onMounted(async () => {
  viewer = new Viewer({
    ...baseOptions,
    el: viewerElement.value,
    initialValue: props.initialValue,
  });
});

// Watch for changes in initialValue and update viewer content
watch(() => props.initialValue, (newValue) => {
  if (viewer && newValue !== undefined) {
    viewer.setMarkdown(newValue || '');
  }
});

function getMarkdown() {
  return viewer.getMarkdown();
}

defineExpose({ getMarkdown });
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor-viewer.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "../styles/ToastUIEditor.scss";
@import "../styles/ToastUIEditorCustom.scss";
</style>
