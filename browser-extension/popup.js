/**
 * PyCostAudit Browser Extension - Popup Script
 */

const API_URL = "http://localhost:8000";
const HOME_PATH = require('os').homedir();

// Load data from storage
async function loadData() {
    try {
        const result = await chrome.storage.local.get("costData");
        return result.costData || { costs: [] };
    } catch (e) {
        console.error("Error loading data:", e);
        return { costs: [] };
    }
}

// Get today's statistics
function getTodayStats(data) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const todayCosts = data.costs.filter(c => {
        const costDate = new Date(c.timestamp);
        costDate.setHours(0, 0, 0, 0);
        return costDate.getTime() === today.getTime();
    });

    const total = todayCosts.reduce((sum, c) => sum + (c.estimated_cost || 0), 0);
    const tokens = todayCosts.reduce((sum, c) => sum + (c.total_tokens || 0), 0);
    const byProvider = {};
    const byModel = {};

    todayCosts.forEach(c => {
        const prov = c.provider || "unknown";
        const model = c.model || "unknown";
        byProvider[prov] = (byProvider[prov] || 0) + (c.estimated_cost || 0);
        byModel[model] = (byModel[model] || 0) + (c.estimated_cost || 0);
    });

    return {
        total,
        tokens,
        count: todayCosts.length,
        byProvider,
        byModel,
    };
}

// Get forecast
function getForecast(data) {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    weekAgo.setHours(0, 0, 0, 0);

    const weekCosts = data.costs.filter(c => new Date(c.timestamp) >= weekAgo);
    const dailyTotals = {};

    weekCosts.forEach(c => {
        const date = new Date(c.timestamp).toLocaleDateString();
        dailyTotals[date] = (dailyTotals[date] || 0) + (c.estimated_cost || 0);
    });

    if (Object.keys(dailyTotals).length === 0) {
        return { avgDaily: 0, weeklyForecast: 0, monthlyForecast: 0 };
    }

    const values = Object.values(dailyTotals);
    const avgDaily = values.reduce((a, b) => a + b, 0) / values.length;

    return {
        avgDaily,
        weeklyForecast: avgDaily * 7,
        monthlyForecast: avgDaily * 30,
    };
}

// Update UI
async function updateUI() {
    const data = await loadData();
    const stats = getTodayStats(data);
    const forecast = getForecast(data);

    // Update today's costs
    document.getElementById("todayCost").textContent = `$${stats.total.toFixed(4)}`;
    document.getElementById("todayOps").textContent = stats.count.toString();
    document.getElementById("todayTokens").textContent = stats.tokens.toLocaleString();

    // Update provider breakdown
    const providerBreakdown = document.getElementById("providerBreakdown");
    if (Object.keys(stats.byProvider).length === 0) {
        providerBreakdown.innerHTML = '<div class="loading">No costs tracked yet</div>';
    } else {
        const sortedProviders = Object.entries(stats.byProvider)
            .sort((a, b) => b[1] - a[1]);
        providerBreakdown.innerHTML = sortedProviders.map(([prov, cost]) => {
            const pct = stats.total > 0 ? ((cost / stats.total) * 100).toFixed(1) : 0;
            return `
                <div class="breakdown-item">
                    <span class="name">${prov}</span>
                    <span class="cost">$${cost.toFixed(4)}</span>
                    <span class="percent">${pct}%</span>
                </div>
            `;
        }).join("");
    }

    // Update forecast
    document.getElementById("dailyAvg").textContent = `$${forecast.avgDaily.toFixed(2)}`;
    document.getElementById("weeklyEst").textContent = `$${forecast.weeklyForecast.toFixed(2)}`;
    document.getElementById("monthlyEst").textContent = `$${forecast.monthlyForecast.toFixed(2)}`;

    // Update last update time
    document.getElementById("lastUpdate").textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
}

// Refresh button
document.getElementById("refreshBtn").addEventListener("click", async () => {
    document.getElementById("refreshBtn").textContent = "⟳ Refreshing...";
    await updateUI();
    document.getElementById("refreshBtn").textContent = "🔄 Refresh";
});

// Open dashboard button
document.getElementById("openDashboardBtn").addEventListener("click", () => {
    chrome.tabs.create({ url: "http://localhost:3000" });
});

// Initial load
updateUI();

// Auto-refresh every 10 seconds
setInterval(updateUI, 10000);
