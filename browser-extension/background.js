/**
 * PyCostAudit Browser Extension - Background Script
 */

const API_URL = "http://localhost:8000";
const STORAGE_KEY = "pycostaudit_data";

// Initialize storage
chrome.runtime.onInstalled.addListener(() => {
    chrome.storage.local.get([STORAGE_KEY], (result) => {
        if (!result[STORAGE_KEY]) {
            chrome.storage.local.set({
                [STORAGE_KEY]: {
                    costs: [],
                    lastSync: new Date().toISOString(),
                },
            });
        }
    });
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "TRACK_OPERATION") {
        trackOperation(request.data, sendResponse);
        return true; // Will respond asynchronously
    }
});

// Track an operation
async function trackOperation(data, sendResponse) {
    try {
        // Estimate cost (Claude Opus pricing)
        const inputCost = (data.inputTokens / 1_000_000) * 15.0;
        const outputCost = (data.outputTokens / 1_000_000) * 75.0;
        const totalCost = inputCost + outputCost;

        const costRecord = {
            timestamp: new Date().toISOString(),
            operation: data.operation || "api_call",
            model: data.model || "claude-opus-4-8",
            input_tokens: data.inputTokens || 0,
            output_tokens: data.outputTokens || 0,
            total_tokens: (data.inputTokens || 0) + (data.outputTokens || 0),
            input_cost: inputCost,
            output_cost: outputCost,
            estimated_cost: totalCost,
        };

        // Save to storage
        chrome.storage.local.get([STORAGE_KEY], (result) => {
            const data = result[STORAGE_KEY] || { costs: [] };
            data.costs.push(costRecord);
            data.lastSync = new Date().toISOString();

            chrome.storage.local.set({ [STORAGE_KEY]: data }, () => {
                console.log("[PyCostAudit] Operation saved:", costRecord);
                sendResponse({
                    success: true,
                    cost: totalCost,
                    record: costRecord,
                });
            });
        });
    } catch (error) {
        console.error("[PyCostAudit] Error tracking operation:", error);
        sendResponse({ success: false, error: error.message });
    }
}

// Sync with backend API (if available)
async function syncWithAPI() {
    try {
        const result = await chrome.storage.local.get([STORAGE_KEY]);
        const data = result[STORAGE_KEY] || { costs: [] };

        // Try to sync with FastAPI backend
        const response = await fetch(`${API_URL}/api/costs`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer browser-extension",
            },
            body: JSON.stringify({
                costs: data.costs,
            }),
        });

        if (response.ok) {
            console.log("[PyCostAudit] Synced with API");
            // Update sync timestamp
            data.lastSync = new Date().toISOString();
            chrome.storage.local.set({ [STORAGE_KEY]: data });
        }
    } catch (error) {
        console.log("[PyCostAudit] API sync unavailable (offline or service not running)");
    }
}

// Auto-sync every 5 minutes
chrome.alarms.create("syncWithAPI", { periodInMinutes: 5 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "syncWithAPI") {
        syncWithAPI();
    }
});

// Initial sync on startup
syncWithAPI();
