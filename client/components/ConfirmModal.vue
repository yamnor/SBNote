<template>
  <TransitionRoot appear :show="isVisible" as="template">
    <Dialog as="div" @close="emitClose('cancel')" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-lg bg-theme-background border border-theme-border p-6 text-left align-middle shadow-2xl transition-all">
              <DialogTitle
                v-if="title"
                as="h3"
                class="text-lg font-medium leading-6 text-theme-text mb-4"
              >
                {{ title }}
              </DialogTitle>
              
              <div class="mt-2">
                <p class="text-sm text-theme-text-muted">
                  {{ message }}
                </p>
                <!-- Custom content slot -->
                <div v-if="$slots.default" class="mt-4">
                  <slot />
                </div>
              </div>

              <div class="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  :class="getButtonClasses(cancelButtonStyle, 'cancel')"
                  @click="emitClose('cancel')"
                >
                  {{ cancelButtonText }}
                </button>
                
                <button
                  v-if="rejectButtonText"
                  type="button"
                  :class="getButtonClasses(rejectButtonStyle, 'reject')"
                  @click="emitClose('reject')"
                >
                  {{ rejectButtonText }}
                </button>
                
                <button
                  type="button"
                  :class="getButtonClasses(confirmButtonStyle, 'confirm')"
                  @click="emitClose('confirm')"
                >
                  {{ confirmButtonText }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue'

const props = defineProps({
  title: { type: String, default: "Confirmation" },
  message: String,
  confirmButtonStyle: { type: String, default: "cta" },
  confirmButtonText: { type: String, default: "Confirm" },
  cancelButtonStyle: { type: String, default: "subtle" },
  cancelButtonText: { type: String, default: "Cancel" },
  rejectButtonStyle: { type: String, default: "danger" },
  rejectButtonText: { type: String },
});
const emit = defineEmits(["confirm", "reject", "cancel"]);
const isVisible = defineModel({ type: Boolean });

function emitClose(closeEvent = "cancel") {
  isVisible.value = false;
  emit(closeEvent);
}

function getButtonClasses(style, type) {
  const baseClasses = "inline-flex justify-center rounded-md border border-transparent px-4 py-2 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2";
  
  const styleClasses = {
    cta: "bg-theme-brand text-white hover:bg-theme-brand-dark focus-visible:ring-theme-brand",
    subtle: "bg-theme-background-subtle text-theme-text hover:bg-theme-background-elevated focus-visible:ring-theme-brand",
    danger: "bg-theme-brand-accent text-white hover:bg-pink-600 focus-visible:ring-theme-brand-accent",
    secondary: "bg-theme-button text-theme-text hover:bg-theme-button-hover focus-visible:ring-theme-brand"
  };
  
  return `${baseClasses} ${styleClasses[style] || styleClasses.cta}`;
}
</script>
