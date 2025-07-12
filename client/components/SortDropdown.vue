<template>
  <div class="relative">
    <!-- Dropdown button -->
    <button
      @click="toggleDropdown"
      class="flex items-center space-x-2 px-3 text-gray-600 hover:text-color-primary transition-colors rounded"
      :class="{ 'text-color-primary': isOpen }"
    >
      <component :is="currentSortIcon" class="w-4 h-4" />
      <span class="text-sm font-medium">{{ currentSortLabel }}</span>
      <ChevronDown class="w-4 h-4 transition-transform" :class="{ 'rotate-180': isOpen }" />
    </button>

    <!-- Dropdown menu -->
    <div
      v-if="isOpen"
      class="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-300 rounded-md shadow-lg z-10"
    >
      <div class="py-1">
        <!-- Label -->
        <div v-if="label" class="px-4 py-2 text-xs text-gray-500 font-medium">
          {{ label }}
        </div>
        <button
          v-for="option in sortOptions"
          :key="option.value"
          @click="selectOption(option)"
          class="flex items-center space-x-3 w-full px-4 py-2 text-left text-sm hover:bg-gray-100 transition-colors"
          :class="{ 'bg-gray-100 text-color-primary': modelValue === option.value }"
        >
          <component :is="getOptionIcon(option)" class="w-4 h-4" />
          <span>{{ option.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { ChevronDown, ArrowUpAZ, ArrowDownAZ, ArrowUp01, ArrowDown01, ArrowDownNarrowWide, ArrowDownWideNarrow, CalendarArrowUp, CalendarArrowDown, ClockArrowUp, ClockArrowDown } from 'lucide-vue-next';

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  sortOrder: {
    type: String,
    required: true
  },
  options: {
    type: Array,
    default: null
  },
  label: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['update:modelValue', 'update:sortOrder']);

const isOpen = ref(false);

const defaultSortOptions = [
  {
    value: 'name',
    label: 'Name',
    icon: ArrowUpAZ
  },
  {
    value: 'count',
    label: 'Count',
    icon: ArrowUp01
  },
  {
    value: 'updated',
    label: 'Updated',
    icon: ClockArrowDown
  }
];

const sortOptions = computed(() => {
  return props.options || defaultSortOptions;
});

const currentSortLabel = computed(() => {
  const option = sortOptions.value.find(opt => opt.value === props.modelValue);
  return option ? option.label : 'Sort';
});

const currentSortIcon = computed(() => {
  const option = sortOptions.value.find(opt => opt.value === props.modelValue);
  if (!option) return ArrowUpAZ;
  
  // Handle string icon names
  if (typeof option.icon === 'string') {
    if (option.icon === 'Clock') {
      return props.sortOrder === 'asc' ? CalendarArrowUp : CalendarArrowDown;
    } else if (option.icon === 'FileText') {
      return props.sortOrder === 'asc' ? ArrowUpAZ : ArrowDownAZ;
    } else if (option.icon === 'Score') {
      return props.sortOrder === 'asc' ? ArrowDownNarrowWide : ArrowDownWideNarrow;
    } else if (option.icon === 'Calendar') {
      return props.sortOrder === 'asc' ? CalendarArrowUp : CalendarArrowDown;
    }
  }
  
  // Handle component icons
  if (props.modelValue === 'name') {
    return props.sortOrder === 'asc' ? ArrowUpAZ : ArrowDownAZ;
  } else if (props.modelValue === 'count') {
    return props.sortOrder === 'asc' ? ArrowUp01 : ArrowDown01;
  } else if (props.modelValue === 'updated') {
    return props.sortOrder === 'asc' ? CalendarArrowUp : CalendarArrowDown;
  }
  
  return option.icon;
});

function toggleDropdown() {
  isOpen.value = !isOpen.value;
}

function getOptionIcon(option) {
  if (typeof option.icon === 'string') {
    if (option.icon === 'Clock') {
      return CalendarArrowDown;
    } else if (option.icon === 'FileText') {
      return ArrowUpAZ;
    } else if (option.icon === 'Score') {
      return ArrowDownNarrowWide;
    } else if (option.icon === 'Calendar') {
      return CalendarArrowDown;
    }
  }
  
  // Handle specific option values
  if (option.value === 'updated') {
    return CalendarArrowDown;
  }
  
  return option.icon;
}

function selectOption(option) {
  if (props.modelValue === option.value) {
    // Toggle sort order if same option is selected
    const newOrder = props.sortOrder === 'asc' ? 'desc' : 'asc';
    emit('update:sortOrder', newOrder);
  } else {
    // Switch to new sort option with default order
    emit('update:modelValue', option.value);
    emit('update:sortOrder', option.value === 'count' ? 'desc' : 'asc');
  }
  isOpen.value = false;
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
  if (!event.target.closest('.relative')) {
    isOpen.value = false;
  }
}

// Add click outside listener
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script> 