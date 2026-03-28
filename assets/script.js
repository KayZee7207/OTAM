function openSelectPath() {
    const path = prompt("GOTO path");
    if (!path) return;
    window.location = "/view/" + path.replace(/^[\/\\]+|[\/\\]+$/g, "");
}

function runReplay(filename) {
    fetch('/runReplay', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status == "error") {
                alert(data.message);
            } else {
                console.log(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
}

function analyzeReplay(filename) {
    const btn = document.querySelector('button[onclick^="analyzeReplay"]');
    const originalText = btn ? btn.innerHTML : '';

    // 1. Show Loading State Immediately
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<svg class="animate-spin h-4 w-4 text-white inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Analyzing...';
    }

    // 2. Prepare Results Container
    let resultContainer = document.getElementById('analysisResults');
    if (!resultContainer) {
        // Create fallback (reuse logic from displayAnalysisResults or just rely on existing DOM if template is correct)
        // For now, let's assume the template has it or displayAnalysisResults will handle creation.
        // But we want to show "Loading..." in it if it exists.
    } else {
        resultContainer.style.display = 'block';
        resultContainer.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <div class="text-center">
                    <svg class="animate-spin h-8 w-8 text-indigo-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="text-slate-400">Analyzing chat logs with AI...</p>
                </div>
            </div>
         `;
    }

    fetch('/analyzeReplay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: filename }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status == "error") {
                alert(data.message);
                console.error(data);
                if (resultContainer) resultContainer.innerHTML = `<div class="text-red-500 p-4">Error: ${data.message}</div>`;
            }

            // Always try to display data if present, even on error if partial
            if (data.data) {
                displayAnalysisResults(data.data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (resultContainer) resultContainer.innerHTML = `<div class="text-red-500 p-4">Network Error: ${error}</div>`;
            alert("An error occurred during analysis.");
        })
        .finally(() => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        });
}

function displayAnalysisResults(result) {
    // 1. Get Container
    let resultContainer = document.getElementById('analysisResults');

    // Fallback if not found (e.g. on older pages or if template didn't render it)
    if (!resultContainer) {
        console.warn("Analysis container not found in DOM, creating fallback.");
        resultContainer = document.createElement('div');
        resultContainer.id = 'analysisResults';
        resultContainer.className = 'mb-6 bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg animate-fade-in z-10 relative';

        // Injection Logic
        const chatContainer = document.getElementById('chat-container');
        const mainContent = document.getElementById('mainContent');
        const pathEl = document.getElementById('path');

        if (chatContainer) {
            const innerCard = chatContainer.querySelector('div.bg-slate-900');
            if (innerCard) innerCard.insertBefore(resultContainer, innerCard.firstChild);
            else chatContainer.insertBefore(resultContainer, chatContainer.firstChild);
        } else if (mainContent) {
            mainContent.insertBefore(resultContainer, mainContent.firstChild);
        } else if (pathEl) {
            pathEl.insertAdjacentElement('afterend', resultContainer);
        } else {
            document.body.prepend(resultContainer);
        }
    }

    // 2. Build HTML
    let badgeColor = "bg-green-500";
    if (result.toxicity_score > 7) badgeColor = "bg-red-600";
    else if (result.toxicity_score > 4) badgeColor = "bg-yellow-500";

    let html = `
    <div class="flex justify-between items-start mb-4">
        <h2 class="text-xl font-bold text-white flex items-center">
            <span class="mr-2">🤖</span> AI Analysis Report
        </h2>
        <span class="${badgeColor} text-white text-sm font-bold px-3 py-1 rounded-full">Score: ${result.toxicity_score}/10</span>
    </div>
    <div class="bg-slate-900/50 rounded-lg p-4 mb-4 border border-white/5">
        <h3 class="text-sm font-bold text-slate-400 uppercase mb-2">Summary</h3>
        <p class="text-slate-200 leading-relaxed">${result.summary}</p>
    </div>
    `;

    if (result.flagged_messages && result.flagged_messages.length > 0) {
        html += `<h3 class="text-sm font-bold text-slate-400 uppercase mb-3">Flagged Violations</h3><div class="space-y-3">`;
        result.flagged_messages.forEach(m => {
            html += `
                <div class="bg-red-900/10 border border-red-500/20 rounded-lg p-3">
                    <div class="flex justify-between items-start mb-1">
                        <span class="font-bold text-red-400">${m.player}</span>
                        <span class="text-xs text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-700">${m.coc_violation || 'Violation'}</span>
                    </div>
                    <p class="text-white mb-2">"${m.message}"</p>
                    <p class="text-sm text-slate-400 italic">Note: ${m.comment || 'No comment'}</p>
                </div>`;
        });
        html += `</div>`;
    } else {
        html += `<div class="text-green-400 flex items-center"><span class="mr-2">✓</span> No severe violations found.</div>`;
    }

    resultContainer.innerHTML = html;
    resultContainer.style.display = 'block';
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

/* UI Utilities */
function toggleAnalyzed() {
    const btn = document.getElementById('toggleAnalyzedBtn');
    const cards = document.querySelectorAll('.replay-card');
    const isHiding = btn.innerText.includes('Hide');

    if (isHiding) {
        btn.innerHTML = '<span class="mr-2">🙈</span> Show Analyzed';
        btn.classList.add('bg-indigo-900', 'border-indigo-700', 'text-indigo-200');
    } else {
        btn.innerHTML = '<span class="mr-2">👁️</span> Hide Analyzed';
        btn.classList.remove('bg-indigo-900', 'border-indigo-700', 'text-indigo-200');
    }

    cards.forEach(card => {
        if (card.dataset.analyzed === 'true') {
            card.style.display = isHiding ? 'none' : 'block';
        }
    });
}

function updateContextMenu(playerId, playerName) {
    const contextMenu = document.getElementById('contextFilterMenu');
    contextMenu.innerHTML = '';

    if (!playerId) return;

    const links = [
        { text: 'Profile', url: "https://server4.beyondallreason.info/profile/" + playerId },
        { text: 'Actions', url: "https://server4.beyondallreason.info/moderation/report/user/" + playerId + "#actions_tab" },
        { text: 'Details', url: "https://server4.beyondallreason.info/moderation/report/user/" + playerId + "#user_details_tab" },
        { text: 'Reports', url: "https://server4.beyondallreason.info/moderation/report?target_id=" + playerId + "&limit=50&state=Open&kind=Any&order=Oldest+first" },
        { text: 'Gex', url: "https://gex.honu.pw/user/" + playerId },
        { text: 'BarStats', url: "https://www.bar-stats.pro/playerstats?playerName=" + playerName }
    ];

    links.forEach(link => {
        const div = document.createElement('div');
        div.textContent = link.text;
        div.onclick = () => window.open(link.url, '_blank');
        contextMenu.appendChild(div);
    });
}

// Collapser Logic
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('collapser')) {
        const content = e.target.nextElementSibling;
        if (content && content.classList.contains('collapsable')) {
            e.target.parentElement.classList.toggle('collapsed');
            const isCollapsed = e.target.parentElement.classList.contains('collapsed');
            const text = e.target.innerText;
            if (isCollapsed) e.target.innerText = text.replace('[-]', '[+]');
            else e.target.innerText = text.replace('[+]', '[-]');
        }
    }

    // Context Menu Close
    const menu = document.getElementById('contextFilterMenu');
    if (menu && menu.style.display === 'block') {
        menu.style.display = 'none';
    }
});

// Context Menu Open
document.addEventListener('contextmenu', function (e) {
    const target = e.target.closest('label');
    if (target && Array.from(target.classList).some(c => c.startsWith('player-'))) {
        e.preventDefault();
        const id = target.dataset.id;
        const name = target.dataset.name;
        updateContextMenu(id, name);
        const menu = document.getElementById('contextFilterMenu');
        menu.style.display = 'block';
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
    }
});

// Width Logic ->
document.addEventListener("DOMContentLoaded", () => {
    const widthSelector = document.getElementById("widthSelector");
    const customWidthGroup = document.getElementById("customWidthGroup");
    const customWidthInput = document.getElementById("customWidthInput");
    const applyCustomBtn = document.getElementById("applyCustomWidth");
    const mainContent = document.getElementById("mainContent");

    const savedWidth = localStorage.getItem("maxWidth") || "1800px";

    function applyWidth(width) {
        if (!mainContent) return;
        mainContent.style.maxWidth = width;
    }

    // Initialize
    if (widthSelector) {
        // Check if saved width is one of the options
        const options = Array.from(widthSelector.options).map(o => o.value);
        if (options.includes(savedWidth)) {
            widthSelector.value = savedWidth;
            if (customWidthGroup) customWidthGroup.classList.add("hidden");
        } else {
            // It's a custom value
            widthSelector.value = "custom";
            if (customWidthGroup) customWidthGroup.classList.remove("hidden");
            if (customWidthInput) customWidthInput.value = savedWidth;
        }

        // Apply immediately
        applyWidth(savedWidth);

        // Change Handler
        widthSelector.addEventListener("change", (e) => {
            const val = e.target.value;
            if (val === "custom") {
                if (customWidthGroup) customWidthGroup.classList.remove("hidden");
                if (customWidthInput) customWidthInput.focus();
            } else {
                if (customWidthGroup) customWidthGroup.classList.add("hidden");
                applyWidth(val);
                localStorage.setItem("maxWidth", val);
            }
        });
    }

    // Custom Apply Handler
    if (applyCustomBtn && customWidthInput) {
        applyCustomBtn.addEventListener("click", () => {
            const val = customWidthInput.value.trim();
            if (val) {
                applyWidth(val);
                localStorage.setItem("maxWidth", val);
                // Visual feedback could go here
            }
        });

        // Also apply on Enter key
        customWidthInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                applyCustomBtn.click();
            }
        });
    }

    // Font Size Logic
    const fontSizeSelector = document.getElementById("fontSizeSelector");
    const customFontSizeInputContainer = document.getElementById("customFontSizeInputContainer");
    const customFontSizeInput = document.getElementById("customFontSizeInput");

    // Default to 16px across the full tool
    let currentFontSize = localStorage.getItem("chatFontSize") || "16";
    let customFontSizeValue = localStorage.getItem("customChatFontSizeVal") || "16";

    function applyFontSize(val) {
        const root = document.documentElement;
        if (!root) return;
        if (val === "custom") {
            const px = customFontSizeInput.value || customFontSizeValue;
            root.style.fontSize = px + "px";
        } else {
            root.style.fontSize = val + "px";
        }
    }

    // Init
    if (fontSizeSelector) {
        // Restore state
        fontSizeSelector.value = currentFontSize;
        if (currentFontSize === "custom") {
            if (customFontSizeInputContainer) customFontSizeInputContainer.classList.remove("hidden");
            if (customFontSizeInput) customFontSizeInput.value = customFontSizeValue;
        }

        // Apply immediately
        applyFontSize(currentFontSize);

        // Listener
        fontSizeSelector.addEventListener("change", (e) => {
            const val = e.target.value;
            currentFontSize = val;

            if (val === "custom") {
                if (customFontSizeInputContainer) customFontSizeInputContainer.classList.remove("hidden");
                // Focus input
                if (customFontSizeInput) {
                    customFontSizeInput.value = customFontSizeValue;
                    customFontSizeInput.focus();
                }
                applyFontSize("custom");
            } else {
                if (customFontSizeInputContainer) customFontSizeInputContainer.classList.add("hidden");
                applyFontSize(val);
            }

            localStorage.setItem("chatFontSize", val);
        });
    }

    if (customFontSizeInput) {
        customFontSizeInput.addEventListener("input", (e) => {
            customFontSizeValue = e.target.value;
            localStorage.setItem("customChatFontSizeVal", customFontSizeValue);
            if (fontSizeSelector.value === "custom") {
                applyFontSize("custom");
            }
        });
    }

    // Ensure it runs once DOM is definitely ready or content injected
    // (chat-container might be rendered by replay view logic)
    // We already call it on Init, but redundant check doesn't hurt.

    // Settings Modal
    const btn = document.getElementById("settingsButton");
    const modal = document.getElementById("settingsModal");
    const close = document.getElementById("settingsClose");

    if (btn && modal) {
        btn.onclick = () => modal.style.display = "flex";
        close.onclick = () => modal.style.display = "none";
    }
});
