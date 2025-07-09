<template>
  <TransitionRoot appear :show="isVisible" as="template">
    <Dialog as="div" @close="closeModal" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full transform overflow-hidden rounded-lg bg-theme-background border border-theme-border shadow-2xl transition-all" style="max-width: var(--layout-width-note);">
              <!-- Header -->
              <div class="flex items-center justify-end p-2 pb-0">
                <div class="flex items-center space-x-3">
                  <!-- Tags -->
                  <div v-if="note.tags && note.tags.length > 0" class="flex items-center space-x-1">
                    <span class="text-xs text-theme-text-muted">Tags:</span>
                    <span 
                      v-for="tag in note.tags" 
                      :key="tag"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium rounded bg-theme-background-subtle text-theme-text-muted"
                    >
                      {{ tag }}
                    </span>
                  </div>
                  
                  <!-- Close button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md border border-theme-border bg-theme-background-subtle p-2 text-theme-text hover:bg-theme-background-elevated focus:outline-none focus-visible:ring-2 focus-visible:ring-theme-brand"
                    @click="closeModal"
                    title="Close"
                  >
                    <X class="w-4 h-4" />
                  </button>
                  
                  <!-- Open in editor button -->
                  <button
                    type="button"
                    class="inline-flex justify-center rounded-md border border-transparent bg-theme-brand p-2 text-white hover:bg-theme-brand-dark focus:outline-none focus-visible:ring-2 focus-visible:ring-theme-brand"
                    @click="openInEditor"
                    :title="globalStore.editMode ? 'Edit' : 'Open in editor'"
                  >
                    <Edit v-if="globalStore.editMode" class="w-4 h-4" />
                    <Eye v-else class="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <!-- Content -->
              <div class="pt-2 max-h-96 overflow-y-auto overflow-x-hidden">
                <div ref="viewerElement" class="w-full"></div>
              </div>
              

            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { Dialog, DialogPanel, TransitionRoot, TransitionChild } from '@headlessui/vue'
import Viewer from "@toast-ui/editor/dist/toastui-editor-viewer";
import { onMounted, ref, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { X, Edit, Eye } from "lucide-vue-next";
import baseOptions from "./EditorOptions.js";
import { useGlobalStore } from "../globalStore.js";

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["close"]);
const isVisible = defineModel({ type: Boolean });
const router = useRouter();
const globalStore = useGlobalStore();
const viewerElement = ref();
const viewerCreated = ref(false);
let viewer = null;

function closeModal() {
  isVisible.value = false;
  emit("close");
}

function openInEditor() {
  closeModal();
  router.push({ 
    name: 'note', 
    params: { filename: props.note.filename.replace(/\.md$/, '') } 
  });
}



// Initialize viewer when modal becomes visible
watch(isVisible, async (visible) => {
  if (visible && props.note.content) {
    // Wait for Vue DOM update
    await nextTick();
    
    // Wait for DOM to be ready and then initialize viewer
    setTimeout(() => {
      if (viewerElement.value && !viewer) {
        viewer = new Viewer({
          ...baseOptions,
          el: viewerElement.value,
          initialValue: props.note.content,
        });
        viewerCreated.value = true;
      } else if (viewer) {
        viewer.setMarkdown(props.note.content || '');
      }
    }, 100); // Reduced timeout since we're using nextTick
  }
});

// Clean up viewer when modal closes
watch(isVisible, (visible) => {
  if (!visible && viewer) {
    viewer.destroy();
    viewer = null;
    viewerCreated.value = false;
  }
});
</script>

<style>
@import "@toast-ui/editor/dist/toastui-editor-viewer.css";
@import "prismjs/themes/prism.css";
@import "@toast-ui/editor-plugin-code-syntax-highlight/dist/toastui-editor-plugin-code-syntax-highlight.css";
@import "./EditorStyles.scss";
@import "./EditorStylesCustom.scss";
</style> 