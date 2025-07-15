import { ref, watch } from 'vue';
import { localStorageKeys, saveToLocalStorage, loadFromLocalStorage } from '../lib/helpers.js';

export function useLocalStorage() {
  // Create reactive ref with localStorage persistence
  const createPersistentRef = (key, defaultValue) => {
    const value = ref(loadFromLocalStorage(key, defaultValue));
    
    watch(value, (newValue) => {
      saveToLocalStorage(key, newValue);
    });
    
    return value;
  };

  // Save value to localStorage
  const saveValue = (key, value) => {
    saveToLocalStorage(key, value);
  };

  // Load value from localStorage
  const loadValue = (key, defaultValue) => {
    return loadFromLocalStorage(key, defaultValue);
  };

  return {
    createPersistentRef,
    saveValue,
    loadValue,
    localStorageKeys
  };
} 