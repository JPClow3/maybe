/**
 * Feature Detection
 * Detects backdrop-filter support and applies fallback classes
 */

(function() {
  'use strict';
  
  // Check if backdrop-filter is supported
  function supportsBackdropFilter() {
    // Check CSS.supports first (modern browsers)
    if (window.CSS && CSS.supports) {
      return CSS.supports('backdrop-filter', 'blur(1px)') || 
             CSS.supports('-webkit-backdrop-filter', 'blur(1px)');
    }
    
    // Fallback: check if the property exists in style
    const testEl = document.createElement('div');
    testEl.style.backdropFilter = 'blur(1px)';
    const hasBackdropFilter = testEl.style.backdropFilter !== '';
    
    // Also check webkit prefix
    testEl.style.webkitBackdropFilter = 'blur(1px)';
    const hasWebkitBackdropFilter = testEl.style.webkitBackdropFilter !== '';
    
    return hasBackdropFilter || hasWebkitBackdropFilter;
  }
  
  // Apply fallback class if backdrop-filter is not supported
  function applyFallback() {
    if (!supportsBackdropFilter()) {
      document.documentElement.classList.add('no-backdrop-filter');
    }
  }
  
  // Run immediately
  applyFallback();
  
  // Also run on DOMContentLoaded as a safety check
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyFallback);
  } else {
    applyFallback();
  }
})();

