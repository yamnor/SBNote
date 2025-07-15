import { defineStore } from "pinia";
import { ref } from "vue";

export const useGlobalStore = defineStore("global", () => {
  const config = ref({});
  const toast = ref(null);
  const isAuthenticated = ref(false);
  
  // Current note information
  const currentNoteTitle = ref('');
  const currentNoteCategory = ref('');
  const currentNoteTags = ref([]);
  
  // Load editMode from localStorage or default to true
  const storedEditMode = localStorage.getItem('editMode');
  const editMode = ref(storedEditMode !== null ? storedEditMode === 'true' : true);
  
  // Load previewStyle from localStorage or default to 'vertical'
  const storedPreviewStyle = localStorage.getItem('previewStyle');
  const previewStyle = ref(storedPreviewStyle || 'vertical');
  
  // Watch for editMode changes and save to localStorage
  const setEditMode = (value) => {
    editMode.value = value;
    localStorage.setItem('editMode', value.toString());
  };

  // Watch for previewStyle changes and save to localStorage
  const setPreviewStyle = (value) => {
    previewStyle.value = value;
    localStorage.setItem('previewStyle', value);
  };

  return { 
    config, 
    toast, 
    isAuthenticated, 
    editMode, 
    setEditMode, 
    previewStyle, 
    setPreviewStyle,
    currentNoteTitle,
    currentNoteCategory,
    currentNoteTags
  };
});
