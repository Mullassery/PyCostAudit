# PyCostAudit Browser Extension

Real-time cost tracking for Claude Code in your browser.

## Features

- 📊 Live cost dashboard in Chrome popup
- 🔄 Auto-sync with backend API
- 📈 Weekly and monthly forecasts
- 🤖 Provider breakdown (OpenAI, Bedrock, Gemini)
- ⚠️ Budget alerts
- 📱 Responsive design

## Installation

### Manual (Development)

1. Clone the repository
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked"
5. Select this `browser-extension/` folder

### From Chrome Web Store (Coming Soon)

...

## Usage

### 1. Click the extension icon
Popup shows your real-time costs

### 2. Refresh data
Click the "Refresh" button to sync latest data

### 3. Open dashboard
Click "Open Dashboard" to see full analytics at http://localhost:3000

## How It Works

```
Claude.ai Page
    ↓
Content Script (tracks API calls)
    ↓
Background Script (aggregates costs)
    ↓
Browser Storage (persists data)
    ↓
Popup UI (displays stats)
    ↓
Backend API (optional sync)
```

## Architecture

### `manifest.json`
- Declares extension metadata and permissions

### `popup.html` / `popup.css` / `popup.js`
- User-facing dashboard
- Real-time cost display
- Weekly forecasts

### `content.js`
- Injected into claude.ai
- Listens for operation messages

### `tracker.js`
- Runs on claude.ai pages
- Intercepts fetch/WebSocket
- Extracts token usage

### `background.js`
- Service worker
- Handles message routing
- Syncs with FastAPI backend

## Configuration

### API URL (Optional)
Edit `background.js` to change sync endpoint:
```javascript
const API_URL = "http://localhost:8000";
```

### Refresh Interval
Edit `popup.js` to change auto-refresh:
```javascript
setInterval(updateUI, 10000);  // 10 seconds
```

## Troubleshooting

### Extension not showing costs?
1. Make sure you're on claude.ai
2. Check Chrome DevTools console for errors
3. Try refreshing the page

### Sync failing?
- Backend API might not be running
- Check that `http://localhost:8000` is accessible
- Check browser console for errors

### Token counting inaccurate?
- Browser extension estimates tokens from responses
- For exact counts, use the skill or CLI monitor

## Limitations

- Token counting is estimated (not exact)
- Requires manual page refresh to start tracking
- Local storage limited to 10MB
- WebSocket streaming is not fully tracked

## Next Steps

- [ ] Exact token counting via API
- [ ] Real-time WebSocket integration
- [ ] Budget alerts popup
- [ ] Chrome Web Store publication
- [ ] Safari extension support
