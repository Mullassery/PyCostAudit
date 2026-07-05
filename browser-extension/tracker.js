/**
 * PyCostAudit Tracker - Runs on Claude.ai
 * Monitors for API calls and reports costs
 */

console.log("[PyCostAudit] Tracker initialized on", window.location.hostname);

// Intercept fetch calls
const originalFetch = window.fetch;
window.fetch = function (...args) {
    const request = args[0];
    const options = args[1] || {};

    // Call original fetch
    const fetchPromise = originalFetch.apply(this, args);

    // Monitor the response
    fetchPromise
        .then((response) => {
            // Check if this is an API call to Claude
            if (
                typeof request === "string" &&
                (request.includes("claude") || request.includes("api"))
            ) {
                // Clone response to read body
                const clonedResponse = response.clone();

                clonedResponse.json().then((data) => {
                    // Extract tokens from response
                    const usage = data.usage || {};
                    const inputTokens = usage.input_tokens || 0;
                    const outputTokens = usage.output_tokens || 0;

                    if (inputTokens > 0 || outputTokens > 0) {
                        // Send to content script
                        window.postMessage(
                            {
                                type: "CLAUDE_OPERATION",
                                payload: {
                                    operation: "api_call",
                                    model: data.model || "claude-opus-4-8",
                                    inputTokens,
                                    outputTokens,
                                    url: request,
                                    timestamp: new Date().toISOString(),
                                },
                            },
                            "*"
                        );

                        console.log("[PyCostAudit] Tracked operation:", {
                            inputTokens,
                            outputTokens,
                        });
                    }
                }).catch(() => {
                    // Response is not JSON (e.g., streaming)
                    console.log("[PyCostAudit] Streaming response detected");
                });
            }

            return response;
        })
        .catch((error) => {
            console.error("[PyCostAudit] Fetch error:", error);
        });

    return fetchPromise;
};

// Monitor WebSocket (for streaming)
const OriginalWebSocket = window.WebSocket;
window.WebSocket = function (url, ...args) {
    console.log("[PyCostAudit] WebSocket opened:", url);

    const ws = new OriginalWebSocket(url, ...args);
    let messageCount = 0;

    ws.addEventListener("message", (event) => {
        messageCount++;
        // Crude token estimation: 1 message ≈ 100 tokens
        if (messageCount % 10 === 0) {
            console.log(
                `[PyCostAudit] WebSocket activity: ${messageCount} messages`
            );
        }
    });

    return ws;
};

// Report to extension every 30 seconds
setInterval(() => {
    window.postMessage(
        {
            type: "CLAUDE_OPERATION",
            payload: {
                operation: "heartbeat",
                timestamp: new Date().toISOString(),
            },
        },
        "*"
    );
}, 30000);

console.log("[PyCostAudit] Tracking initialized");
