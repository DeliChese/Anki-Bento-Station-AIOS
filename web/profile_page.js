document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const themeBtn = document.getElementById('nav-theme');
    const statsBtn = document.getElementById('nav-stats');
    const themePage = document.getElementById('page-theme');
    const statsPage = document.getElementById('page-stats');
    const exportBtn = document.getElementById('export-btn');
    const mainEl = document.querySelector('main');

    if (!themeBtn || !statsBtn || !themePage || !statsPage || !exportBtn) {
        return;
    }

    // --- Page Switching with Smooth Transition ---
    let isTransitioning = false;

    function fadeOut(el, callback) {
        el.style.transition = 'opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
        el.style.opacity = '0';
        el.style.transform = 'translateY(8px)';
        el.style.pointerEvents = 'none';
        setTimeout(callback, 180);
    }

    function fadeIn(el) {
        el.style.display = 'block';
        el.style.opacity = '0';
        el.style.transform = 'translateY(8px)';
        // Force reflow
        el.offsetHeight;
        el.style.transition = 'opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1), transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)';
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
        el.style.pointerEvents = 'auto';
    }

    function showThemePage() {
        if (isTransitioning) return;
        isTransitioning = true;
        themeBtn.classList.add('active');
        statsBtn.classList.remove('active');

        if (statsPage.style.display !== 'none') {
            fadeOut(statsPage, () => {
                statsPage.style.display = 'none';
                fadeIn(themePage);
                isTransitioning = false;
            });
        } else {
            fadeIn(themePage);
            isTransitioning = false;
        }
    }

    function showStatsPage() {
        if (isTransitioning) return;
        isTransitioning = true;
        themeBtn.classList.remove('active');
        statsBtn.classList.add('active');

        if (themePage.style.display !== 'none') {
            fadeOut(themePage, () => {
                themePage.style.display = 'none';
                fadeIn(statsPage);
                isTransitioning = false;
            });
        } else {
            fadeIn(statsPage);
            isTransitioning = false;
        }
    }

    themeBtn.addEventListener('click', showThemePage);
    statsBtn.addEventListener('click', showStatsPage);
    showThemePage();

    // --- IMPROVED EXPORT FUNCTION ---
    function exportFullPage() {
        const elementToCapture = document.querySelector('.onigiri-profile-page');
        if (!elementToCapture) return;

        // Temporarily flatten pseudo-elements for html2canvas compatibility
        const styleElements = document.querySelectorAll('style');
        const originalStyles = [];
        const pseudoBackup = [];

        styleElements.forEach((styleEl, idx) => {
            originalStyles.push(styleEl.textContent);
            let css = styleEl.textContent;

            // Convert ::before background-image to actual inline styles for html2canvas
            css = css.replace(/\.onigiri-profile-page::before\s*\{([^}]*)\}/g, (match, rules) => {
                pseudoBackup.push({ el: elementToCapture, rules: rules });
                return match; // Keep original
            });

            // Convert .profile-header-banner::before if exists
            const bannerEl = document.querySelector('.profile-header-banner');
            if (bannerEl) {
                css = css.replace(/\.profile-header-banner::before\s*\{([^}]*)\}/g, (match, rules) => {
                    pseudoBackup.push({ el: bannerEl, rules: rules });
                    return match;
                });
            }

            if (css !== originalStyles[idx]) {
                styleEl.textContent = css;
            }
        });

        // Apply ::before content as actual div elements for rendering
        const tempDivs = [];
        pseudoBackup.forEach(item => {
            const bgImageMatch = item.rules.match(/background-image:\s*url\(['"]?([^'")\s]+)['"]?\)/);
            const bgColorMatch = item.rules.match(/background-color:\s*([^;]+)/);
            const gradientMatch = item.rules.match(/background-image:\s*linear-gradient\([^)]+\)/);

            if (bgImageMatch || bgColorMatch || gradientMatch) {
                const div = document.createElement('div');
                div.style.cssText = item.rules;
                div.style.position = 'absolute';
                div.style.top = '0';
                div.style.left = '0';
                div.style.width = '100%';
                div.style.height = '100%';
                div.style.pointerEvents = 'none';
                div.style.zIndex = '-1';
                div.style.borderRadius = 'inherit';
                div.setAttribute('data-onigiri-temp', 'true');
                item.el.style.position = item.el.style.position || 'relative';
                item.el.insertBefore(div, item.el.firstChild);
                tempDivs.push(div);
            }
        });

        const options = {
            useCORS: true,
            scale: 2,
            backgroundColor: null,
            allowTaint: true,
            logging: false,
            onclone: function(clonedDoc) {
                // Ensure cloned document has proper rendering
                const clonedEl = clonedDoc.querySelector('.onigiri-profile-page');
                if (clonedEl) {
                    clonedEl.style.overflow = 'visible';
                }
            }
        };

        html2canvas(elementToCapture, options)
            .then(canvas => {
                // Clean up temp divs
                tempDivs.forEach(d => d.remove());
                // Restore original styles
                styleElements.forEach((styleEl, idx) => {
                    if (idx < originalStyles.length) {
                        styleEl.textContent = originalStyles[idx];
                    }
                });

                const imageData = canvas.toDataURL("image/png");
                // Use a safer delimiter that won't conflict with base64
                const base64Data = imageData.split(',')[1];
                if (base64Data) {
                    pycmd("saveImage:" + base64Data);
                } else {
                    pycmd("saveImage:" + imageData);
                }
            })
            .catch(error => {
                // Clean up on error too
                tempDivs.forEach(d => d.remove());
                styleElements.forEach((styleEl, idx) => {
                    if (idx < originalStyles.length) {
                        styleEl.textContent = originalStyles[idx];
                    }
                });
                alert("Error rendering image: " + error);
            });
    }

    exportBtn.addEventListener('click', exportFullPage);
});