export function getToastOptions(description, title, severity) {
  return {
    summary: title,
    detail: description,
    severity: severity,
    closable: false,
    life: 5000,
  };
}

// Local storage helpers for persisting UI state
export const localStorageKeys = {
  HOME_SELECTED_TAG: 'sbnote_home_selected_tag',
  HOME_SORT_BY: 'sbnote_home_sort_by',
  HOME_SORT_ORDER: 'sbnote_home_sort_order',
  HOME_NOTE_SORT_BY: 'sbnote_home_note_sort_by',
  HOME_NOTE_SORT_ORDER: 'sbnote_home_note_sort_order',
  HOME_PINNED_TAGS: 'sbnote_home_pinned_tags'
};

export function saveToLocalStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn('Failed to save to localStorage:', error);
  }
}

export function loadFromLocalStorage(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.warn('Failed to load from localStorage:', error);
    return defaultValue;
  }
}

export function removeFromLocalStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.warn('Failed to remove from localStorage:', error);
  }
}

/**
 * Handle double click/touch events for mobile compatibility
 * @param {Function} singleClickHandler - Function to call on single click
 * @param {Function} doubleClickHandler - Function to call on double click
 * @param {number} delay - Delay in milliseconds to distinguish between single and double click (default: 300)
 * @returns {Function} Event handler function
 */
export function createDoubleClickHandler(singleClickHandler, doubleClickHandler, delay = 300) {
  let clickTimeout = null;
  
  return function(event) {
    // Note: Double-tap zoom prevention is now handled by CSS (touch-action: manipulation)
    // and the improved touch event listeners, so we don't need to prevent default here
    
    if (clickTimeout) {
      // Double click/touch detected
      clearTimeout(clickTimeout);
      clickTimeout = null;
      if (doubleClickHandler) {
        doubleClickHandler(event);
      }
    } else {
      // Single click/touch - wait to see if it becomes a double click
      clickTimeout = setTimeout(() => {
        if (singleClickHandler) {
          singleClickHandler(event);
        }
        clickTimeout = null;
      }, delay);
    }
  };
}

/**
 * Add touch event listeners to prevent double-tap zoom while allowing scrolling
 * @param {HTMLElement} element - Element to add listeners to
 * @param {Function} clickHandler - Click handler function
 */
export function addTouchEventListeners(element, clickHandler) {
  if (!element) return;
  
  let touchStartTime = 0;
  let touchStartX = 0;
  let touchStartY = 0;
  let hasMoved = false;
  let touchTimeout = null;
  
  const handleTouchStart = (event) => {
    touchStartTime = Date.now();
    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
    hasMoved = false;
    
    // Set a timeout to prevent double-tap zoom only if no movement occurs
    touchTimeout = setTimeout(() => {
      // Only prevent default if we haven't moved significantly
      if (!hasMoved) {
        event.preventDefault();
      }
    }, 10); // Small delay to allow scroll detection
  };
  
  const handleTouchMove = (event) => {
    if (touchTimeout) {
      clearTimeout(touchTimeout);
      touchTimeout = null;
    }
    
    const touchX = event.touches[0].clientX;
    const touchY = event.touches[0].clientY;
    const deltaX = Math.abs(touchX - touchStartX);
    const deltaY = Math.abs(touchY - touchStartY);
    
    // If moved more than 10px, consider it a scroll gesture
    if (deltaX > 10 || deltaY > 10) {
      hasMoved = true;
    }
  };
  
  const handleTouchEnd = (event) => {
    if (touchTimeout) {
      clearTimeout(touchTimeout);
      touchTimeout = null;
    }
    
    // Only trigger click if no significant movement occurred
    if (!hasMoved) {
      clickHandler(event);
    }
  };
  
  // Add touch event listeners
  element.addEventListener('touchstart', handleTouchStart, { passive: false });
  element.addEventListener('touchmove', handleTouchMove, { passive: true });
  element.addEventListener('touchend', handleTouchEnd, { passive: true });
  
  // Return cleanup function
  return () => {
    element.removeEventListener('touchstart', handleTouchStart);
    element.removeEventListener('touchmove', handleTouchMove);
    element.removeEventListener('touchend', handleTouchEnd);
    if (touchTimeout) {
      clearTimeout(touchTimeout);
    }
  };
}


