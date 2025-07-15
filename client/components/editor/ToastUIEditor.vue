<template>
  <div ref="editorElement" class="w-full"></div>
</template>

<script setup>
import Editor from "@toast-ui/editor";
import { onMounted, ref, watch, nextTick } from "vue";

import { getEditorOptions } from "./ToastUIEditorOptions.js";

const props = defineProps({
  initialValue: String,
  initialEditType: {
    type: String,
    default: "markdown",
  },
  addImageBlobHook: Function,
  previewStyle: {
    type: String,
    default: "vertical",
  },
});

const emit = defineEmits(["change"]);

const editorElement = ref();
let toastEditor;

onMounted(async () => {
  toastEditor = new Editor({
    ...getEditorOptions(props.previewStyle),
    el: editorElement.value,
    initialValue: props.initialValue,
    initialEditType: props.initialEditType,
    events: {
      change: () => {
        emit("change");
      },
    },
    hooks: props.addImageBlobHook
      ? { addImageBlobHook: props.addImageBlobHook }
      : {},
  });
  
  // Wait for DOM update and then set content
  await nextTick();
  if (props.initialValue) {
    toastEditor.setMarkdown(props.initialValue);
  }
});

// Watch for changes in initialValue and update editor content
watch(() => props.initialValue, (newValue) => {
  if (toastEditor && newValue !== undefined) {
    const currentContent = toastEditor.getMarkdown();
    // Only update if content actually changed to preserve cursor position
    if (currentContent !== newValue) {
      toastEditor.setMarkdown(newValue || '');
    }
  }
});

// Watch for changes in previewStyle and update editor
watch(() => props.previewStyle, (newStyle) => {
  if (toastEditor) {
    toastEditor.changePreviewStyle(newStyle);
  }
});

function getMarkdown() {
  return toastEditor.getMarkdown();
}

function isWysiwygMode() {
  return toastEditor.isWysiwygMode();
}

defineExpose({ getMarkdown, isWysiwygMode });
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "../styles/ToastUIEditor.scss";
@import "../styles/ToastUIEditorCustom.scss";

</style>
