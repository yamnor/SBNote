<template>
  <div class="flex-1 editor-container">
    <ToastUIEditor
      v-if="canModify"
      ref="toastEditor"
      :key="note.filename || 'new-note'"
      :initialValue="getInitialEditorValue()"
      :initialEditType="loadDefaultEditorMode()"
      :addImageBlobHook="addImageBlobHook"
      :previewStyle="globalStore.previewStyle"
      @change="handleEditorChange"
    />
    <ToastUIEditorViewer
      v-else
      :initialValue="note.content"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import ToastUIEditor from '../editor/ToastUIEditor.vue';
import ToastUIEditorViewer from '../editor/ToastUIEditorViewer.vue';
import { useGlobalStore } from '../../lib/globalStore.js';
import { useNoteEditor } from '../../composables/useNoteEditor.js';

const props = defineProps({
  note: {
    type: Object,
    required: true
  },
  canModify: {
    type: Boolean,
    required: true
  },
  isNewNote: {
    type: Boolean,
    required: true
  },
  addImageBlobHook: {
    type: Function,
    required: true
  }
});

const emit = defineEmits(['editor-change']);

const globalStore = useGlobalStore();
const { 
  toastEditor, 
  getInitialEditorValue, 
  loadDefaultEditorMode,
  generateTitleFromContent 
} = useNoteEditor();

function handleEditorChange() {
  if (props.canModify) {
    const content = toastEditor.value.getMarkdown();
    const generatedTitle = generateTitleFromContent(content);
    
    emit('editor-change', {
      content,
      generatedTitle
    });
  }
}
</script>

<style scoped>
.editor-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: visible;
}
</style> 