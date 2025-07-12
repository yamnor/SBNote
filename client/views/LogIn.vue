<template>
  <div class="flex h-screen flex-col items-center justify-center">
    <form @submit.prevent="logIn" class="flex max-w-80 flex-col items-center">
      <input
        v-model="username"
        type="text"
        id="username"
        placeholder="Username"
        class="w-full rounded-md border border-color-border-primary px-3 py-2 focus:outline-none dark:bg-color-bg-elevated mb-3"
        autocomplete="username"
        required
      />
      <input
        v-model="password"
        type="password"
        id="password"
        placeholder="Password"
        class="w-full rounded-md border border-color-border-primary px-3 py-2 focus:outline-none dark:bg-color-bg-elevated mb-3"
        autocomplete="current-password"
        required
      />
      <input
        v-if="globalStore.config.authType == authTypes.totp"
        v-model="totp"
        type="text"
        id="one-time-code"
        placeholder="2FA Code"
        class="w-full rounded-md border border-color-border-primary px-3 py-2 focus:outline-none dark:bg-color-bg-elevated mb-3"
        autocomplete="one-time-code"
        required
      />
      <div class="mb-6 flex items-center">
        <input
          type="checkbox"
          id="remember-me"
          v-model="rememberMe"
          class="mr-2"
        />
        <label for="remember-me" class="text-color-text-primary text-sm">Remember Me</label>
      </div>
      <button type="submit" class="flex items-center justify-center px-4 py-2 rounded-lg bg-color-button-primary-bg text-color-button-primary-fg hover:bg-color-button-primary-hover-bg transition-colors">
        <LogIn class="w-4 h-4 mr-2" />
        Log In
      </button>
    </form>
  </div>
</template>

<script setup>
import { LogIn } from "lucide-vue-next";

import { ref, watch } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getToken } from "../api.js";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";

import { storeToken } from "../tokenStorage.js";

const props = defineProps({ redirect: String });

const globalStore = useGlobalStore();
const router = useRouter();


const username = ref("");
const password = ref("");
const totp = ref("");
const rememberMe = ref(false);

function logIn() {
  getToken(username.value, password.value, totp.value)
    .then((access_token) => {
      storeToken(access_token, rememberMe.value);
      globalStore.isAuthenticated = true;
      if (props.redirect) {
        router.push(props.redirect);
      } else {
        router.push({ name: "home" });
      }
    })
    .catch((error) => {
      username.value = "";
      password.value = "";
      totp.value = "";

      if (error.response?.status === 401) {
        // Login failed
      } else {
        apiErrorHandler(error);
      }
    });
}

// Redirect to home if authentication is disabled.
if (globalStore.config.authType === authTypes.none) {
  router.push({ name: "home" });
}
</script>
