/**
 * 🎌 Onigiri Animated Mascot Engine — "Nakama" (仲間)
 * =================================================
 * Run-time JavaScript engine for rendering 2D animated characters.
 *
 * Supports 3 modes:
 *   - "sprite"  : Canvas 2D sprite sheet animation
 *   - "lottie"  : Lottie JSON vector animation
 *   - "rive"    : Rive runtime animation
 *
 * States: idle | happy | sad | celebrate | curious
 */

(function () {
    "use strict";

    const CONFIG = window.__ONIGIRI_MASCOT_CONFIG__;
    if (!CONFIG) return; // Mascot not enabled

    // ── DOM References ──────────────────────────────────────────
    const container = document.getElementById("onigiri-mascot-container");
    const canvas = document.getElementById("onigiri-mascot-canvas");
    const lottieDiv = document.getElementById("onigiri-mascot-lottie");
    if (!container || !canvas) return;

    const ctx = canvas.getContext("2d");

    // ── State Machine ──────────────────────────────────────────
    const STATE = {
        current: "idle",
        previous: "idle",
        frame: 0,
        frameTimer: 0,
        images: {},        // { state: Image }
        loaded: false,
        lottieInstances: {}, // { state: AnimationItem }
        riveInstance: null,
        bubbleTimer: null,
        isDragging: false,
        dragStartX: 0,
        dragStartY: 0,
        posX: null,       // Custom position (set by drag)
        posY: null,
        entranceDone: false,
    };

    // ── Preload Images (Sprite Mode) ───────────────────────────
    function preloadSpriteImages() {
        const spriteCfg = CONFIG.sprite;
        const states = ["idle", "happy", "sad", "celebrate", "curious"];
        let loadedCount = 0;
        const total = Object.values(spriteCfg).filter(v => typeof v === "string" && v).length;

        if (total === 0) {
            console.warn("[Onigiri Mascot] No sprite images configured. Mascot will not render.");
            return;
        }

        states.forEach(state => {
            const url = spriteCfg[state];
            if (!url) return;

            const img = new Image();
            img.onload = () => {
                loadedCount++;
                if (loadedCount >= total) {
                    STATE.loaded = true;
                    console.log(`[Onigiri Mascot] All ${loadedCount} sprite(s) loaded. Starting animation.`);
                }
            };
            img.onerror = () => {
                console.warn(`[Onigiri Mascot] Failed to load sprite: ${url}`);
                loadedCount++;
                if (loadedCount >= total) STATE.loaded = true;
            };
            img.src = url;
            STATE.images[state] = img;
        });
    }

    // ── Lottie Mode ────────────────────────────────────────────
    function initLottie() {
        if (typeof lottie === "undefined") {
            console.warn("[Onigiri Mascot] Lottie library not found. Falling back to sprite mode.");
            CONFIG.mode = "sprite";
            preloadSpriteImages();
            return;
        }

        const lottieCfg = CONFIG.lottie;
        lottieDiv.style.display = "block";
        canvas.style.display = "none";

        // Load idle animation by default
        if (lottieCfg.idle) {
            STATE.lottieInstances.idle = lottie.loadAnimation({
                container: lottieDiv,
                renderer: "svg",
                loop: true,
                autoplay: true,
                path: lottieCfg.idle,
            });
            STATE.current = "idle";
        }

        // Preload other states
        ["happy", "sad", "celebrate", "curious"].forEach(state => {
            if (lottieCfg[state]) {
                // Store path for lazy loading
                STATE.images[state] = { _lottiePath: lottieCfg[state] };
            }
        });
        
        STATE.loaded = true;
    }

    function switchLottieState(newState) {
        if (STATE.current === newState) return;

        // Destroy current animation
        if (STATE.lottieInstances[STATE.current]) {
            STATE.lottieInstances[STATE.current].destroy();
            delete STATE.lottieInstances[STATE.current];
        }

        // Load new animation
        const path = CONFIG.lottie[newState];
        if (path) {
            STATE.lottieInstances[newState] = lottie.loadAnimation({
                container: lottieDiv,
                renderer: "svg",
                loop: true,
                autoplay: true,
                path: path,
            });
            STATE.previous = STATE.current;
            STATE.current = newState;
        }
    }

    // ── Rive Mode ──────────────────────────────────────────────
    function initRive() {
        if (typeof rive === "undefined") {
            console.warn("[Onigiri Mascot] Rive library not found. Falling back to sprite mode.");
            CONFIG.mode = "sprite";
            preloadSpriteImages();
            return;
        }

        const riveCfg = CONFIG.rive;
        if (!riveCfg.src) {
            console.warn("[Onigiri Mascot] No Rive source configured.");
            return;
        }

        try {
            STATE.riveInstance = new rive.Rive({
                src: riveCfg.src,
                canvas: canvas,
                artboard: riveCfg.artboard || undefined,
                stateMachines: "default",
                autoplay: true,
                onLoad: () => {
                    STATE.loaded = true;
                    console.log("[Onigiri Mascot] Rive animation loaded.");
                },
            });

            // Trigger idle state
            if (riveCfg.idle_state) {
                triggerRiveState(riveCfg.idle_state);
            }
        } catch (e) {
            console.error("[Onigiri Mascot] Rive initialization failed:", e);
        }
    }

    function triggerRiveState(stateName) {
        if (!STATE.riveInstance) return;
        try {
            // Rive state machine input trigger
            const inputs = STATE.riveInstance.stateMachineInputs("default");
            if (inputs) {
                inputs.forEach(input => {
                    if (input.name === stateName || input.name.toLowerCase() === stateName.toLowerCase()) {
                        input.value = true;
                    }
                });
            }
        } catch (e) {
            // Some Rive files use different state machine APIs
            console.warn("[Onigiri Mascot] Could not trigger Rive state:", stateName, e);
        }
    }

    // ── Sprite Rendering ───────────────────────────────────────
    function renderSprite(timestamp) {
        if (!STATE.loaded) {
            requestAnimationFrame(renderSprite);
            return;
        }

        const spriteCfg = CONFIG.sprite;
        const img = STATE.images[STATE.current];
        if (!img || !img.complete || img.naturalWidth === 0) {
            requestAnimationFrame(renderSprite);
            return;
        }

        const frameCount = spriteCfg.frame_count || 8;
        const frameW = spriteCfg.frame_width || 128;
        const frameH = spriteCfg.frame_height || 128;
        const fps = spriteCfg.fps || 8;
        const frameInterval = 1000 / fps;

        // Update frame
        if (!STATE._lastTimestamp) STATE._lastTimestamp = timestamp;
        STATE.frameTimer += timestamp - STATE._lastTimestamp;
        STATE._lastTimestamp = timestamp;

        if (STATE.frameTimer >= frameInterval) {
            STATE.frame = (STATE.frame + 1) % frameCount;
            STATE.frameTimer -= frameInterval;
        }

        // Clear & draw
        const dpr = window.devicePixelRatio || 1;
        const displayW = canvas.clientWidth;
        const displayH = canvas.clientHeight;
        canvas.width = displayW * dpr;
        canvas.height = displayH * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, displayW, displayH);

        // Calculate source rect (sprite sheet may have frames in a row)
        const sx = STATE.frame * frameW;
        const sy = 0;

        ctx.drawImage(
            img,
            sx, sy, frameW, frameH,
            0, 0, displayW, displayH
        );

        requestAnimationFrame(renderSprite);
    }

    // ── State Transitions ──────────────────────────────────────
    function setState(newState, duration = 3000) {
        if (STATE.current === newState && newState !== "idle") return;
        if (!CONFIG.sprite[newState] && !CONFIG.lottie[newState] && newState !== "idle") return;

        STATE.previous = STATE.current;

        if (CONFIG.mode === "lottie") {
            switchLottieState(newState);
        } else if (CONFIG.mode === "rive") {
            const riveCfg = CONFIG.rive;
            const stateMap = {
                idle: riveCfg.idle_state,
                happy: riveCfg.happy_state,
                sad: riveCfg.sad_state,
                celebrate: riveCfg.celebrate_state,
            };
            triggerRiveState(stateMap[newState] || newState);
        }
        
        STATE.current = newState;

        // Auto-return to idle after duration
        if (newState !== "idle" && duration > 0 && CONFIG.mode !== "rive") {
            clearTimeout(STATE._returnTimer);
            STATE._returnTimer = setTimeout(() => setState("idle"), duration);
        }
    }

    // ── Speech Bubble ──────────────────────────────────────────
    function showBubble(text, duration = 2500) {
        // Remove existing bubble
        const existing = container.querySelector(".mascot-bubble");
        if (existing) existing.remove();

        const bubble = document.createElement("div");
        bubble.className = "mascot-bubble";
        bubble.textContent = text;
        container.appendChild(bubble);

        requestAnimationFrame(() => bubble.classList.add("show"));

        clearTimeout(STATE.bubbleTimer);
        STATE.bubbleTimer = setTimeout(() => {
            bubble.classList.remove("show");
            setTimeout(() => bubble.remove(), 300);
        }, duration);
    }

    // ── Interaction Handlers ───────────────────────────────────
    function onContainerClick(e) {
        if (STATE.isDragging) return;
        if (!CONFIG.behavior.click_reaction) return;

        setState("happy", 2000);

        const messages = [
            "Yatta! ✨", "Ganbatte! 💪", "Sugoi! 🌟",
            "Kawaii~ 💕", "Daijoubu! 🍀", "Arigatou! 🙏",
            "You got this! ⭐", "Keep going! 🚀",
        ];
        const msg = messages[Math.floor(Math.random() * messages.length)];
        showBubble(msg);
    }

    function onContainerHover() {
        if (!CONFIG.behavior.hover_reaction) return;
        if (STATE.current !== "idle") return;
        setState("curious", 1000);
    }

    function onContainerLeave() {
        if (STATE.current === "curious") {
            setState("idle", 0);
        }
    }

    // ── Drag to Reposition ─────────────────────────────────────
    function onDragStart(e) {
        if (!CONFIG.behavior.draggable) return;
        if (e.target.closest(".mascot-bubble")) return; // Don't drag bubble

        e.preventDefault();
        STATE.isDragging = true;
        STATE.dragStartX = e.clientX;
        STATE.dragStartY = e.clientY;

        const rect = container.getBoundingClientRect();
        STATE._dragOffsetX = e.clientX - rect.left;
        STATE._dragOffsetY = e.clientY - rect.top;

        container.classList.add("dragging");
        container.removeAttribute("data-position"); // Free from CSS positioning
    }

    function onDragMove(e) {
        if (!STATE.isDragging) return;

        const x = e.clientX - STATE._dragOffsetX;
        const y = e.clientY - STATE._dragOffsetY;

        container.style.left = x + "px";
        container.style.top = y + "px";
        container.style.right = "auto";
        container.style.bottom = "auto";
        container.style.transform = "none";
    }

    function onDragEnd(e) {
        if (!STATE.isDragging) return;
        STATE.isDragging = false;
        container.classList.remove("dragging");
    }

    // ── External API (called from Anki hooks) ──────────────────
    window.OnigiriMascot = {
        /** Hiển thị phản ứng khi trả lời đúng */
        onCorrectAnswer: function () {
            if (!CONFIG.behavior.auto_reactions) return;
            setState("happy", 2000);
            const msgs = ["Perfect! 🎯", "Nice! 👍", "Correct! ⭐", "Amazing! 💎"];
            showBubble(msgs[Math.floor(Math.random() * msgs.length)], 2000);
        },

        /** Hiển thị phản ứng khi trả lời sai */
        onWrongAnswer: function () {
            if (!CONFIG.behavior.auto_reactions) return;
            setState("sad", 2000);
            const msgs = ["Don't give up! 💪", "Try again! 🔄", "You'll get it! 🍀"];
            showBubble(msgs[Math.floor(Math.random() * msgs.length)], 2000);
        },

        /** Hiển thị phản ứng khi level up */
        onLevelUp: function (level) {
            setState("celebrate", 3500);
            showBubble("LEVEL UP! 🎉 LV." + level, 3500);
        },

        /** Thay đổi trạng thái thủ công */
        setState: setState,

        /** Hiển thị bubble chat */
        say: showBubble,

        /** Ẩn mascot */
        hide: function () {
            container.style.display = "none";
        },

        /** Hiện mascot */
        show: function () {
            container.style.display = "";
            if (!STATE.entranceDone) {
                container.classList.add("entrance");
                STATE.entranceDone = true;
                setTimeout(() => container.classList.remove("entrance"), 600);
            }
        },

        /** Di chuyển mascot tới vị trí */
        moveTo: function (x, y) {
            container.style.left = x + "px";
            container.style.top = y + "px";
            container.style.right = "auto";
            container.style.bottom = "auto";
            container.style.transform = "none";
        },
    };

    // ── Public API for Anki Reviewer Hook ──────────────────────
    // These will be called from Python via web.eval()
    window.OnigiriExpToast = window.OnigiriExpToast || {};
    const origExpShow = window.OnigiriExpToast.show;
    window.OnigiriExpToast.show = function (amount, leveledUp, newLevel, cardLabel) {
        if (origExpShow) origExpShow(amount, leveledUp, newLevel, cardLabel);

        // Trigger mascot reaction
        if (leveledUp && window.OnigiriMascot) {
            window.OnigiriMascot.onLevelUp(newLevel);
        } else if (amount > 0 && window.OnigiriMascot) {
            window.OnigiriMascot.onCorrectAnswer();
        }
    };

    // ── Init ────────────────────────────────────────────────────
    function init() {
        if (CONFIG.mode === "lottie") {
            initLottie();
        } else if (CONFIG.mode === "rive") {
            initRive();
        } else {
            // Default: sprite mode
            preloadSpriteImages();
            canvas.style.display = "";
            if (lottieDiv) lottieDiv.style.display = "none";
        }

        // Entrance animation
        setTimeout(() => {
            container.classList.add("entrance");
            STATE.entranceDone = true;
            setTimeout(() => container.classList.remove("entrance"), 600);
        }, 500);

        // Bind events
        container.addEventListener("click", onContainerClick);
        container.addEventListener("mouseenter", onContainerHover);
        container.addEventListener("mouseleave", onContainerLeave);

        // Drag events
        container.addEventListener("mousedown", onDragStart);
        document.addEventListener("mousemove", onDragMove);
        document.addEventListener("mouseup", onDragEnd);

        // Touch events for mobile/tablet
        container.addEventListener("touchstart", (e) => {
            const touch = e.touches[0];
            onDragStart({ clientX: touch.clientX, clientY: touch.clientY, preventDefault: () => {} });
        }, { passive: false });
        document.addEventListener("touchmove", (e) => {
            if (!STATE.isDragging) return;
            const touch = e.touches[0];
            onDragMove({ clientX: touch.clientX, clientY: touch.clientY });
        });
        document.addEventListener("touchend", onDragEnd);

        // Start render loop (sprite mode only; lottie/rive self-animate)
        if (CONFIG.mode === "sprite") {
            requestAnimationFrame(renderSprite);
        }

        console.log("[Onigiri Mascot] 🎌 Nakama engine initialized! Mode:", CONFIG.mode);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
