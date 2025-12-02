/**
 * Base application JavaScript for Maybe Finance
 * Handles HTMX event handlers, loading states, optimistic updates, and UI interactions
 */

// Disable buttons during HTMX requests
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const form = evt.target.closest('form');
    if (form) {
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.disabled = true;
            btn.setAttribute('aria-disabled', 'true');
        });
        // Disable form inputs during submission
        const inputs = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
        inputs.forEach(input => {
            input.disabled = true;
        });
    }
});

// Re-enable buttons after HTMX requests complete
document.body.addEventListener('htmx:afterRequest', function(evt) {
    const form = evt.target.closest('form');
    if (form) {
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.disabled = false;
            btn.removeAttribute('aria-disabled');
        });
        const inputs = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
        inputs.forEach(input => {
            input.disabled = false;
        });
    }
});

// Re-enable buttons on error
document.body.addEventListener('htmx:responseError', function(evt) {
    const form = evt.target.closest('form');
    if (form) {
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(btn => {
            btn.disabled = false;
            btn.removeAttribute('aria-disabled');
        });
        const inputs = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
        inputs.forEach(input => {
            input.disabled = false;
        });
    }
});

// Announce loading states to screen readers
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const target = evt.target;
    const loadingEl = document.getElementById('loading-announcements');
    if (loadingEl) {
        // Check if it's a boost navigation
        if (target.tagName === 'A' && (
            target.hasAttribute('hx-boost') || 
            target.getAttribute('hx-target') === '#main-content'
        )) {
            const pageName = target.textContent.trim() || target.getAttribute('aria-label') || 'page';
            loadingEl.textContent = `Loading ${pageName}, please wait...`;
        } else if (target.tagName === 'FORM' || target.closest('form')) {
            loadingEl.textContent = 'Saving, please wait...';
        } else if (target.hasAttribute('hx-get') || target.hasAttribute('hx-post')) {
            loadingEl.textContent = 'Loading content, please wait...';
        }
    }
});

document.body.addEventListener('htmx:afterRequest', function(evt) {
    const loadingEl = document.getElementById('loading-announcements');
    if (loadingEl && !evt.detail.failed) {
        loadingEl.textContent = '';
    }
});

document.body.addEventListener('htmx:responseError', function(evt) {
    const loadingEl = document.getElementById('loading-announcements');
    if (loadingEl) {
        loadingEl.textContent = 'An error occurred. Please try again.';
    }
});

// Page loading overlay for HTMX boost navigation
(function() {
    const overlay = document.getElementById('page-loading-overlay');
    const loadingBar = document.getElementById('page-loading-bar');
    const mainContent = document.getElementById('main-content');
    let isBoostNavigation = false;
    let overlayTimeout = null;
    let progressInterval = null;
    
    function hideLoadingIndicators() {
        if (overlayTimeout) {
            clearTimeout(overlayTimeout);
            overlayTimeout = null;
        }
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
        if (loadingBar) {
            loadingBar.style.display = 'none';
            loadingBar.style.transform = 'scaleX(0)';
        }
        if (overlay) {
            overlay.classList.add('opacity-0', 'pointer-events-none');
            overlay.classList.remove('opacity-100');
        }
        isBoostNavigation = false;
    }
    
    function showSkeletonInMain() {
        // Show skeleton state in main content during boost navigation
        if (mainContent) {
            // Check if there's a skeleton template we can inject
            const contentContainers = mainContent.querySelectorAll('[id$="-content"]');
            contentContainers.forEach(container => {
                // Add skeleton class to show loading state
                container.classList.add('opacity-50');
            });
        }
    }
    
    function hideSkeletonInMain() {
        if (mainContent) {
            const contentContainers = mainContent.querySelectorAll('[id$="-content"]');
            contentContainers.forEach(container => {
                container.classList.remove('opacity-50');
            });
        }
    }
    
    // Show overlay/bar only for boost navigation (full page transitions)
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        const target = evt.target;
        // Check if this is a boost navigation (anchor tag with hx-boost or hx-target="#main-content")
        const isBoostLink = target.tagName === 'A' && (
            target.hasAttribute('hx-boost') || 
            target.getAttribute('hx-target') === '#main-content' ||
            target.closest('[hx-boost]')
        );
        
        if (isBoostLink) {
            isBoostNavigation = true;
            
            // Show skeleton state in main content
            showSkeletonInMain();
            
            // Show subtle loading bar at top immediately
            if (loadingBar) {
                loadingBar.style.transform = 'scaleX(0)';
                loadingBar.style.display = 'block';
                
                // Animate progress bar
                let progress = 0;
                progressInterval = setInterval(() => {
                    if (progress < 90 && isBoostNavigation) {
                        progress += Math.random() * 15;
                        if (progress > 90) progress = 90;
                        if (loadingBar) {
                            loadingBar.style.transform = `scaleX(${progress / 100})`;
                        }
                    }
                }, 100);
                
                // Initial progress
                requestAnimationFrame(() => {
                    if (isBoostNavigation && loadingBar) {
                        loadingBar.style.transform = 'scaleX(0.2)';
                    }
                });
            }
            
            // Show overlay after a delay (only if request takes time)
            overlayTimeout = setTimeout(() => {
                if (isBoostNavigation && overlay) {
                    overlay.classList.remove('opacity-0', 'pointer-events-none');
                    overlay.classList.add('opacity-100');
                }
            }, 500); // Show overlay only if loading takes more than 500ms
        } else {
            isBoostNavigation = false;
        }
    });
    
    // Complete loading bar and hide overlay
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        if (isBoostNavigation) {
            // Complete the loading bar
            if (loadingBar) {
                loadingBar.style.transform = 'scaleX(1)';
            }
            
            // Hide skeleton state
            hideSkeletonInMain();
            
            // Hide overlay immediately if visible
            if (overlayTimeout) {
                clearTimeout(overlayTimeout);
                overlayTimeout = null;
            }
            if (overlay) {
                overlay.classList.add('opacity-0', 'pointer-events-none');
                overlay.classList.remove('opacity-100');
            }
            
            // Hide loading bar after animation completes
            setTimeout(() => {
                hideLoadingIndicators();
            }, 200);
        }
    });
    
    // Handle errors - hide loading indicators
    document.body.addEventListener('htmx:responseError', function(evt) {
        if (isBoostNavigation) {
            hideSkeletonInMain();
            hideLoadingIndicators();
        }
    });
    
    // Handle timeouts
    document.body.addEventListener('htmx:timeout', function(evt) {
        if (isBoostNavigation) {
            hideSkeletonInMain();
            hideLoadingIndicators();
        }
    });
    
    // Also handle history navigation (back/forward)
    window.addEventListener('htmx:pushedIntoHistory', function() {
        hideSkeletonInMain();
        hideLoadingIndicators();
    });
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        hideSkeletonInMain();
        hideLoadingIndicators();
    });
})();

// Store original values for optimistic updates
const optimisticState = new Map();

// Optimistic UI updates for inline edits
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const target = evt.target;
    const form = target.closest('form');
    
    // Account name inline edit
    if (form && form.action && form.action.includes('edit-inline')) {
        const nameInput = form.querySelector('input[name="name"]');
        if (nameInput) {
            const newName = nameInput.value.trim();
            const nameDisplay = document.getElementById('account-name');
            if (nameDisplay && newName) {
                // Store original value
                optimisticState.set('account-name', nameDisplay.textContent.trim());
                // Optimistically update UI
                nameDisplay.textContent = newName;
                nameDisplay.classList.add('opacity-70');
            }
        }
    }
    
    // Transaction category inline edit
    if (form && form.action && form.action.includes('update-category')) {
        const select = form.querySelector('select[name="category_id"]');
        if (select) {
            const selectedOption = select.options[select.selectedIndex];
            const newCategoryName = selectedOption ? selectedOption.text : '—';
            const td = form.closest('td');
            if (td) {
                // Store original value
                const originalText = td.textContent.trim();
                optimisticState.set('transaction-category', originalText);
                // Optimistically update UI
                td.innerHTML = `<span class="opacity-70">${newCategoryName}</span>`;
            }
        }
    }
    
    // Transaction amount inline edit
    if (form && form.action && form.action.includes('update-amount')) {
        const amountInput = form.querySelector('input[name="amount"]');
        if (amountInput) {
            const newAmount = amountInput.value.trim();
            const td = form.closest('td');
            if (td && newAmount) {
                // Store original value
                const originalText = td.textContent.trim();
                optimisticState.set('transaction-amount', originalText);
                // Optimistically update UI (format as currency)
                const formatted = newAmount.replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
                td.innerHTML = `<span class="opacity-70 tabular-nums tracking-tight font-mono">R$ ${formatted}</span>`;
            }
        }
    }
    
    // Account form submissions
    if (form && form.action && (form.action.includes('account_new') || form.action.includes('account_edit'))) {
        const formContent = document.getElementById('account-form-content');
        if (formContent) {
            // Store original form state
            optimisticState.set('account-form', formContent.innerHTML);
            // Add loading state
            formContent.classList.add('opacity-70', 'pointer-events-none');
        }
    }
    
    // Transaction form submissions
    if (form && form.action && (form.action.includes('transaction_new') || form.action.includes('transaction_edit'))) {
        const formContent = document.querySelector('[id*="transaction-form"], [id*="form-content"]');
        if (formContent) {
            // Store original form state
            optimisticState.set('transaction-form', formContent.innerHTML);
            // Add loading state
            formContent.classList.add('opacity-70', 'pointer-events-none');
        }
    }
});

// Confirm or revert optimistic updates
document.body.addEventListener('htmx:afterRequest', function(evt) {
    // Success - remove opacity class to show final state
    if (!evt.detail.failed) {
        const nameDisplay = document.getElementById('account-name');
        if (nameDisplay) {
            nameDisplay.classList.remove('opacity-70');
        }
        
        // Check for redirect (successful form submission)
        if (evt.detail.xhr) {
            const redirect = evt.detail.xhr.getResponseHeader('HX-Redirect');
            if (redirect) {
                // Form submission was successful, redirect will happen
                // Remove loading state
                const formContent = document.getElementById('account-form-content') || 
                                   document.querySelector('[id*="transaction-form"], [id*="form-content"]');
                if (formContent) {
                    formContent.classList.remove('opacity-70', 'pointer-events-none');
                }
            }
        }
        optimisticState.clear();
    }
});

// Revert optimistic updates on error
document.body.addEventListener('htmx:responseError', function(evt) {
    // Revert account name
    const nameDisplay = document.getElementById('account-name');
    if (nameDisplay && optimisticState.has('account-name')) {
        nameDisplay.textContent = optimisticState.get('account-name');
        nameDisplay.classList.remove('opacity-70');
    }
    
    // Revert transaction category
    const categoryForms = document.querySelectorAll('form[action*="update-category"]');
    categoryForms.forEach(form => {
        const td = form.closest('td');
        if (td && optimisticState.has('transaction-category')) {
            // Server will return the correct state, but we can show a brief error
            td.classList.add('text-danger-600');
            setTimeout(() => td.classList.remove('text-danger-600'), 2000);
        }
    });
    
    // Revert transaction amount
    const amountForms = document.querySelectorAll('form[action*="update-amount"]');
    amountForms.forEach(form => {
        const td = form.closest('td');
        if (td && optimisticState.has('transaction-amount')) {
            // Server will return the correct state, but we can show a brief error
            td.classList.add('text-danger-600');
            setTimeout(() => td.classList.remove('text-danger-600'), 2000);
        }
    });
    
    // Remove loading state from forms
    const formContent = document.getElementById('account-form-content') || 
                       document.querySelector('[id*="transaction-form"], [id*="form-content"]');
    if (formContent) {
        formContent.classList.remove('opacity-70', 'pointer-events-none');
    }
    
    optimisticState.clear();
});

// Real-time form validation on blur
function setupFieldValidation(form, validateUrl) {
    if (!form) return;
    
    const fields = form.querySelectorAll('input[type="text"], input[type="date"], input[type="email"], select, textarea');
    fields.forEach(field => {
        if (field.name && field.name !== 'csrfmiddlewaretoken' && field.type !== 'hidden') {
            // Add validation on blur
            field.addEventListener('blur', function() {
                const fieldValue = this.value.trim();
                if (fieldValue || field.hasAttribute('required')) {
                    const url = new URL(validateUrl, window.location.origin);
                    url.searchParams.set('field', this.name);
                    url.searchParams.set('value', fieldValue);
                    
                    // Use HTMX to validate
                    if (typeof htmx !== 'undefined') {
                        htmx.ajax('GET', url.toString(), {
                            target: '#' + this.id + '_validation',
                            swap: 'innerHTML'
                        }).then(() => {
                            // Check validation result and update field styling
                            const validationEl = document.getElementById(this.id + '_validation');
                            const errorEl = document.getElementById(this.id + '_error');
                            
                            if (validationEl) {
                                const hasError = validationEl.querySelector('.text-danger-600');
                                const hasSuccess = validationEl.querySelector('.text-success-600');
                                
                                // Update field border color
                                this.classList.remove('border-danger-500', 'ring-danger-500', 'border-success-500', 'ring-success-500');
                                if (hasError) {
                                    this.classList.add('border-danger-500', 'ring-danger-500');
                                    if (errorEl) errorEl.style.display = 'block';
                                } else if (hasSuccess && fieldValue) {
                                    this.classList.add('border-success-500', 'ring-success-500');
                                    if (errorEl) errorEl.style.display = 'none';
                                }
                            }
                        }).catch(() => {
                            // Silently fail validation requests (network errors, etc.)
                        });
                    }
                } else {
                    // Clear validation indicator if field is empty
                    const validationEl = document.getElementById(this.id + '_validation');
                    if (validationEl) validationEl.innerHTML = '';
                    this.classList.remove('border-danger-500', 'ring-danger-500', 'border-success-500', 'ring-success-500');
                }
            });
        }
    });
}

// Setup validation for account forms
document.addEventListener('DOMContentLoaded', function() {
    const accountForm = document.querySelector('form[action*="account"]');
    if (accountForm) {
        setupFieldValidation(accountForm, '/accounts/validate-field/');
    }
});

// Re-setup validation after HTMX swaps
document.body.addEventListener('htmx:afterSwap', function(evt) {
    const accountForm = document.querySelector('form[action*="account"]');
    if (accountForm) {
        setupFieldValidation(accountForm, '/accounts/validate-field/');
    }
});

// Fix duplicate headers - remove any nav elements that appear inside main-content
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Small delay to ensure DOM is fully updated
    setTimeout(function() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            // Remove any nav elements that might have been accidentally included in the swap
            const duplicateNavs = mainContent.querySelectorAll('nav');
            duplicateNavs.forEach(nav => nav.remove());
            
            // Also remove any elements with "Maybe Finance" text that appear inside main-content
            const allElements = mainContent.querySelectorAll('*');
            allElements.forEach(function(el) {
                if (el.textContent && el.textContent.includes('Maybe Finance') && 
                    (el.tagName === 'NAV' || el.closest('nav'))) {
                    const nav = el.tagName === 'NAV' ? el : el.closest('nav');
                    if (nav && mainContent.contains(nav)) {
                        nav.remove();
                    }
                }
            });
            
            // Final check: count all nav elements and remove duplicates inside main-content
            const allNavs = document.querySelectorAll('nav[role="navigation"]');
            if (allNavs.length > 1) {
                // Keep only the first nav (the one outside main-content)
                for (let i = 1; i < allNavs.length; i++) {
                    // Only remove navs that are inside main-content
                    if (mainContent.contains(allNavs[i])) {
                        allNavs[i].remove();
                    }
                }
            }
        }
    }, 10);
});

// Dark mode: enforce always-on and create ambient orbs based on performance mode
(function() {
    const html = document.documentElement;
    html.classList.add('dark');
    
    // Create ambient orbs based on performance mode
    function createAmbientOrbs() {
        const ambientLight = document.getElementById('ambient-light');
        if (!ambientLight) return;
        
        const performanceMode = html.getAttribute('data-performance-mode') || 'medium';
        
        // Limit orb count based on performance mode
        let orbCount = 0;
        if (performanceMode === 'high') {
            orbCount = 4;
        } else if (performanceMode === 'medium') {
            orbCount = 2;
        } else {
            orbCount = 0; // Low performance - no orbs
        }
        
        // Clear existing orbs
        ambientLight.innerHTML = '';
        
        // Create orbs
        const orbColors = ['emerald', 'indigo', 'rose', 'emerald'];
        for (let i = 0; i < orbCount; i++) {
            const orb = document.createElement('div');
            orb.className = `orb orb-${orbColors[i]} orb-${i + 1} will-change-transform`;
            
            // Random initial positions
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            orb.style.left = x + '%';
            orb.style.top = y + '%';
            orb.style.width = (200 + Math.random() * 300) + 'px';
            orb.style.height = orb.style.width;
            
            ambientLight.appendChild(orb);
        }
    }
    
    // Create orbs after performance mode is detected
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Wait a bit for performance detector to run
            setTimeout(createAmbientOrbs, 100);
        });
    } else {
        setTimeout(createAmbientOrbs, 100);
    }
    
    // Recreate orbs if performance mode changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-performance-mode') {
                createAmbientOrbs();
            }
        });
    });
    
    observer.observe(html, {
        attributes: true,
        attributeFilter: ['data-performance-mode']
    });
})();

// Spotlight interaction for cards
function setupCardSpotlight() {
    const cards = document.querySelectorAll('.card-spotlight');
    cards.forEach(card => {
        card.addEventListener('mousemove', function (event) {
            const rect = card.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupCardSpotlight);
} else {
    setupCardSpotlight();
}

document.body.addEventListener('htmx:afterSwap', function() {
    setupCardSpotlight();
});

// Initialize Lucide Icons after DOM is ready and Lucide is loaded
(function() {
    function initLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        } else {
            // Retry if Lucide hasn't loaded yet (deferred script may not be ready)
            setTimeout(initLucideIcons, 50);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLucideIcons);
    } else {
        // DOM already loaded, but Lucide might still be loading (deferred)
        initLucideIcons();
    }
    
    // Re-initialize icons after HTMX swaps
    document.body.addEventListener('htmx:afterSwap', function() {
        initLucideIcons();
    });
})();