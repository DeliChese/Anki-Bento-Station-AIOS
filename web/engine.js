// Onigiri Performance Engine - 60FPS Optimized

window.OnigiriEngine = {
    currentHoveredRow: null,
    _pendingProcess: null, // Debounce processing

    init: function() {
        this.deckListContainer = document.getElementById('deck-list-container');
        if (!this.deckListContainer) {
            return;
        }

        this.bindEvents();
        this.observeMutations();

        // Initial processing of already loaded nodes - use rAF for smooth first paint
        requestAnimationFrame(() => {
            this.processNewNodes(document.querySelectorAll('tr.deck, a.collapse'));
            this.restoreScrollPosition();
        });
    },

    /**
     * Replaces the deck tree's HTML content without a full page reload,
     * preserving scroll position. Optimized for 60FPS.
     * @param {string} newHtml The new HTML for the deck tree's <tbody>.
     */
    updateDeckTree: function(newHtml) {
        if (!this.deckListContainer) return;
        
        const tableBody = this.deckListContainer.querySelector('table.deck-table tbody');
        if (!tableBody) return;

        // Save scroll position BEFORE any DOM mutations
        const savedScroll = this.deckListContainer.scrollTop;
        this.deckListContainer.classList.add('scroll-restoring');

        // --- START: Flicker-fix logic with DocumentFragment for performance ---
        if (typeof OnigiriEditor !== 'undefined' && OnigiriEditor.EDIT_MODE) {
            const tempContainer = document.createElement('tbody');
            tempContainer.innerHTML = newHtml;
            
            // Batch checkbox operations
            const rows = tempContainer.querySelectorAll('tr.deck');
            const fragment = document.createDocumentFragment();
            
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                const did = row.dataset.did;
                if (!did) {
                    fragment.appendChild(row);
                    continue;
                }

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'deck-checkbox';
                checkbox.dataset.did = did;
                checkbox.checked = OnigiriEditor.SELECTED_DECKS.has(did);

                checkbox.onclick = (e) => {
                    e.stopPropagation();
                    if (e.target.checked) {
                        OnigiriEditor.SELECTED_DECKS.add(e.target.dataset.did);
                    } else {
                        OnigiriEditor.SELECTED_DECKS.delete(e.target.dataset.did);
                    }
                };

                const decktd = row.querySelector('td.decktd');
                if (decktd) {
                    decktd.insertBefore(checkbox, decktd.firstChild);
                }
                fragment.appendChild(row);
            }
            
            // Single DOM operation: clear and append fragment
            tableBody.textContent = '';
            tableBody.appendChild(fragment);
        } else {
            tableBody.innerHTML = newHtml;
        }
        // --- END: Flicker-fix logic ---

        // Restore scroll immediately to prevent visual jump
        this.deckListContainer.scrollTop = savedScroll;
        this.processNewNodes(tableBody.children);
        
        if (typeof window.updateDeckLayouts === 'function') {
            window.updateDeckLayouts();
        }

        // The logic below is no longer needed, as it's handled above
        // if (typeof OnigiriEditor !== 'undefined' && OnigiriEditor.EDIT_MODE) {
        //     OnigiriEditor.reapplyEditModeState();
        // }

        setTimeout(() => {
            this.deckListContainer.classList.remove('scroll-restoring');
        }, 50);
    },

    /** Saves the current scroll position to session storage (debounced). */
    saveScrollPosition: function() {
        if (this._scrollSaveTimer) clearTimeout(this._scrollSaveTimer);
        this._scrollSaveTimer = setTimeout(() => {
            if (this.deckListContainer) {
                sessionStorage.setItem('deckListScrollTop', this.deckListContainer.scrollTop);
            }
        }, 100);
    },

    /** Restores the scroll position from session storage - uses rAF. */
    restoreScrollPosition: function() {
        const savedScroll = sessionStorage.getItem('deckListScrollTop');
        if (savedScroll !== null && this.deckListContainer) {
            requestAnimationFrame(() => {
                this.deckListContainer.scrollTop = parseInt(savedScroll, 10);
            });
        }
    },

    /** Binds event listeners to handle interactions - optimized with passive where possible. */
    bindEvents: function() {
        if (this.deckListContainer.dataset.engineBound) return;
        this.deckListContainer.dataset.engineBound = 'true';

        // --- Listener: Keep row hovered while mouse is over it (capture phase) ---
        this.deckListContainer.addEventListener('mouseenter', (event) => {
            const deckRow = event.target.closest('tr.deck');
            if (deckRow && deckRow !== this.currentHoveredRow) {
                if (this.currentHoveredRow) {
                    this.currentHoveredRow.classList.remove('is-hovered');
                }
                this.currentHoveredRow = deckRow;
                deckRow.classList.add('is-hovered');
            }
        }, { capture: true, passive: true });

        this.deckListContainer.addEventListener('mouseleave', (event) => {
            const deckRow = event.target.closest('tr.deck');
            if (deckRow && deckRow === this.currentHoveredRow) {
                deckRow.classList.remove('is-hovered');
                this.currentHoveredRow = null;
            }
        }, { capture: true, passive: true });

        // --- Unified Click Handler for Deck List ---
        let clickTimer = null;
        this.deckListContainer.addEventListener('click', (event) => {
            const target = event.target;

            // Case 1: Click was on a collapse icon.
            // We save the scroll position and then simply let the event proceed.
            // The `onclick` attribute on the <a> tag will handle the pycmd call.
            // We must NOT call event.preventDefault() or return, as that would
            // block the pycmd from firing.
            const collapseLink = target.closest('a.collapse');
            if (collapseLink) {
                this.saveScrollPosition();
                // Allow the default action (onclick attribute) to happen.
                return; 
            }

            // Case 2: Click was on the options/gear icon. Ignore it.
            if (target.closest('.opts')) {
                return;
            }

            // Case 3: Click was on the favorite star. Ignore it.
            // This allows its own onclick attribute to fire without interference.
            if (target.closest('.favorite-star-icon')) {
                return;
            }

            // Case 3.5: Click was on the edit mode checkbox. Ignore it.
            if (target.closest('.deck-checkbox')) {
                return;
            }

            // Case 4: Click was on the deck row itself. Handle double-click to study.
            // This part of the listener will only be reached if the click was NOT on a collapse icon
            // AND not on the favorite star.
            const deckRow = target.closest('tr.deck');
            if (!deckRow) return;

            // Prevent the default link navigation, as we are managing it with a timer.
            event.preventDefault();

            if (!clickTimer) {
                // First click, start timer.
                clickTimer = setTimeout(() => { clickTimer = null; }, 300);
            } else {
                // Second click, fire study action and clear timer.
                clearTimeout(clickTimer);
                clickTimer = null;
                const mainLink = deckRow.querySelector('a.deck');
                if (mainLink) mainLink.click();
            }
        });

        // --- Listener: Restrict drag-and-drop to Editing Mode ---
        this.deckListContainer.addEventListener('dragstart', (event) => {
            const isEditingMode = document.body.classList.contains('deck-edit-mode');
            if (!isEditingMode) {
                event.preventDefault();
                event.stopPropagation();
                return false;
            }

            const dragElement = event.target.closest('tr.deck');
            if (dragElement && event.dataTransfer) {
                const dragImage = dragElement.cloneNode(true);
                dragImage.style.opacity = '0.8';
                dragImage.style.transform = 'scale(0.9)';
                event.dataTransfer.setDragImage(dragImage, -10, -10);
            }
        });
    },

    /** Watches for changes in the deck list - debounced & batched. */
    observeMutations: function() {
        let pendingNodes = [];
        let rafId = null;

        const flushPendingNodes = () => {
            if (pendingNodes.length > 0) {
                this.processNewNodes(pendingNodes);
                pendingNodes = [];
            }
            rafId = null;
        };

        const observer = new MutationObserver((mutations) => {
            for (let i = 0; i < mutations.length; i++) {
                const mutation = mutations[i];
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    for (let j = 0; j < mutation.addedNodes.length; j++) {
                        pendingNodes.push(mutation.addedNodes[j]);
                    }
                }
            }
            
            // Batch process using single rAF
            if (!rafId) {
                rafId = requestAnimationFrame(flushPendingNodes);
            }
        });

        observer.observe(this.deckListContainer, {
            childList: true,
            subtree: true,
        });
    },

    /** Processes a list of new nodes - batch write, no per-node reads. */
    processNewNodes: function(nodes) {
        const collapseIcons = [];
        const deckRows = [];

        for (let i = 0; i < nodes.length; i++) {
            const node = nodes[i];
            if (node.nodeType !== Node.ELEMENT_NODE) continue;

            if (node.matches('a.collapse')) {
                collapseIcons.push(node);
            } else if (node.matches('tr.deck')) {
                deckRows.push(node);
            }
            
            // Query children
            const childCollapses = node.querySelectorAll('a.collapse');
            for (let j = 0; j < childCollapses.length; j++) {
                collapseIcons.push(childCollapses[j]);
            }
            const childRows = node.querySelectorAll('tr.deck');
            for (let k = 0; k < childRows.length; k++) {
                deckRows.push(childRows[k]);
            }
        }

        // Batch write operations
        for (let i = 0; i < collapseIcons.length; i++) {
            this.classifyCollapseIcon(collapseIcons[i]);
        }
        for (let i = 0; i < deckRows.length; i++) {
            const clickableCell = deckRows[i].querySelector('td.decktd');
            if (clickableCell) clickableCell.style.cursor = 'pointer';
        }

        // Defer layout check to idle
        if (typeof window.updateDeckLayouts === 'function') {
            if (window.requestIdleCallback) {
                requestIdleCallback(() => window.updateDeckLayouts());
            } else {
                requestAnimationFrame(() => window.updateDeckLayouts());
            }
        }
    },

    /** Applies open/closed state classes to a collapse icon. */
    classifyCollapseIcon: function(el) {
        if (el.dataset.onigiriClassified) return;
        el.dataset.onigiriClassified = 'true';
        el.classList.remove('state-open', 'state-closed');
        
        if (el.textContent.trim() === '-') {
            el.classList.add('state-open');
        } else {
            el.classList.add('state-closed');
        }
        el.textContent = '';
    },
};

// Initialize the engine once the DOM is ready.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => OnigiriEngine.init());
} else {
    OnigiriEngine.init();
}