/**
 * Performance Detector
 * Detects device capabilities and sets data-performance-mode attribute
 * Values: 'high', 'medium', 'low'
 */

(function() {
  'use strict';
  
  // Check if user prefers reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  // Detect device capabilities
  function detectPerformanceMode() {
    let score = 0;
    
    // Check hardware concurrency (CPU cores)
    const cores = navigator.hardwareConcurrency || 2;
    if (cores >= 8) score += 3;
    else if (cores >= 4) score += 2;
    else if (cores >= 2) score += 1;
    
    // Check device memory (if available)
    if (navigator.deviceMemory) {
      const memory = navigator.deviceMemory;
      if (memory >= 8) score += 3;
      else if (memory >= 4) score += 2;
      else if (memory >= 2) score += 1;
    }
    
    // Check connection type (if available)
    if (navigator.connection) {
      const connection = navigator.connection;
      if (connection.effectiveType === '4g' && !connection.saveData) {
        score += 1;
      }
    }
    
    // Check for power-saving mode hints
    if (navigator.getBattery) {
      navigator.getBattery().then(function(battery) {
        if (battery.charging === false && battery.level < 0.2) {
          score -= 2; // Reduce score if battery is low and not charging
        }
      }).catch(function() {
        // Battery API not available, ignore
      });
    }
    
    // Check screen resolution (4K displays may struggle with backdrop-filter)
    const width = window.screen.width;
    const height = window.screen.height;
    const pixelRatio = window.devicePixelRatio || 1;
    const totalPixels = width * height * pixelRatio;
    
    if (totalPixels > 8_000_000) { // > 4K equivalent
      score -= 1; // Slight penalty for very high resolution
    }
    
    // Determine performance mode
    let mode = 'medium';
    if (score >= 5) {
      mode = 'high';
    } else if (score <= 2) {
      mode = 'low';
    }
    
    // Override to low if reduced motion is preferred
    if (prefersReducedMotion) {
      mode = 'low';
    }
    
    return mode;
  }
  
  // Set performance mode attribute on html element
  function setPerformanceMode() {
    const mode = detectPerformanceMode();
    document.documentElement.setAttribute('data-performance-mode', mode);
    
    // Also add class for CSS targeting
    document.documentElement.classList.add('performance-mode-' + mode);
  }
  
  // Run on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setPerformanceMode);
  } else {
    setPerformanceMode();
  }
  
  // Re-check on battery level changes (if available)
  if (navigator.getBattery) {
    navigator.getBattery().then(function(battery) {
      battery.addEventListener('levelchange', function() {
        if (battery.charging === false && battery.level < 0.2) {
          document.documentElement.setAttribute('data-performance-mode', 'low');
        }
      });
    }).catch(function() {
      // Battery API not available, ignore
    });
  }
  
  // Re-check on connection changes
  if (navigator.connection) {
    navigator.connection.addEventListener('change', setPerformanceMode);
  }
})();

