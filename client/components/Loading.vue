<template>
  <div :class="{ 'flex items-center justify-center': loadSuccessful !== true }">
    <!-- Loading -->
    <div
      v-if="gracePeriodExpired && loadSuccessful === null && !props.hideLoader"
      class="loader"
    ></div>

    <!-- Failed -->
    <div
      v-else-if="loadSuccessful === false"
      class="flex flex-col items-center"
    >
      <component
        v-if="failedIconComponent"
        :is="failedIconComponent"
        size="48"
        class="mb-4 text-color-primary"
      />
      <span class="max-w-80 text-center text-lg text-color-text-light">{{
        failedMessage
      }}</span>
    </div>

    <!-- Loaded -->
    <slot v-else-if="loadSuccessful"></slot>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { AlertTriangle } from "lucide-vue-next";

const props = defineProps({ hideLoader: Boolean });

const loadSuccessful = ref(null);
const failedIconComponent = ref(null);
const failedMessage = ref("");
const gracePeriodExpired = ref(false);

// Don't show loading animation within the first 400ms.
onMounted(() => {
  startGracePeriodTimer();
});

function startGracePeriodTimer() {
  gracePeriodExpired.value = false;
  setTimeout(() => {
    gracePeriodExpired.value = true;
  }, 400);
}

function setLoading() {
  loadSuccessful.value = null;
  startGracePeriodTimer();
}

function setFailed(message, iconComponent) {
  failedMessage.value = message || "Loading Failed";
  failedIconComponent.value = iconComponent || AlertTriangle;
  loadSuccessful.value = false;
}

function setLoaded() {
  loadSuccessful.value = true;
}

defineExpose({ setLoading, setFailed, setLoaded });
</script>

<style scoped>
.loader,
.loader:before,
.loader:after {
  background: var(--color-primary);
  -webkit-animation: load1 1s infinite ease-in-out;
  animation: load1 1s infinite ease-in-out;
  width: 1em;
  height: 4em;
}
.loader {
  color: var(--color-primary);
  text-indent: -9999em;
  /* margin: 33% auto; */
  position: relative;
  font-size: 11px;
  -webkit-transform: translateZ(0);
  -ms-transform: translateZ(0);
  transform: translateZ(0);
  -webkit-animation-delay: -0.16s;
  animation-delay: -0.16s;
}
.loader:before,
.loader:after {
  position: absolute;
  top: 0;
  content: "";
}
.loader:before {
  left: -1.5em;
  -webkit-animation-delay: -0.32s;
  animation-delay: -0.32s;
}
.loader:after {
  left: 1.5em;
}
@-webkit-keyframes load1 {
  0%,
  80%,
  100% {
    box-shadow: 0 0;
    height: 4em;
  }
  40% {
    box-shadow: 0 -2em;
    height: 5em;
  }
}
@keyframes load1 {
  0%,
  80%,
  100% {
    box-shadow: 0 0;
    height: 4em;
  }
  40% {
    box-shadow: 0 -2em;
    height: 5em;
  }
}
</style>
