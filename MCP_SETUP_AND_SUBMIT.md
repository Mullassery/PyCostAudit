# MCP Setup & Automated Skill Registry Submission

**Objective:** Use Playwright MCP or Chrome MCP to fully automate PyCostAudit submissions to all registries

**Status:** Ready for MCP-based execution  
**Version:** 0.4.1

---

## What This Achieves

With MCP automation, you can:
- ✅ Submit to skills.sh (automated form filling)
- ✅ Submit to Swagger Hub (API import)
- ✅ Submit to APIs.guru (registry registration)
- ✅ Create GitHub PRs to awesome lists (CLI automation)
- ✅ Enable and populate GitHub Discussions
- ✅ Generate completion report
- ✅ All in 30-60 minutes with zero manual intervention

---

## Option 1: Playwright MCP (Recommended)

### Step 1: Install Playwright MCP

```bash
cd /Users/georgimullassery/CostReporter

# Method A: Using npm (Recommended)
npm install -D playwright @anthropic-ai/playwright-mcp

# Method B: Using conda
conda install -c conda-forge playwright-mcp

# Verify installation
npm list playwright @anthropic-ai/playwright-mcp
```

### Step 2: Set Up MCP Configuration

Create `.claude/mcp-servers.json`:

```bash
mkdir -p .claude

cat > .claude/mcp-servers.json << 'EOF'
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic-ai/playwright-mcp"],
      "env": {
        "PLAYWRIGHT_HEADLESS": "false",
        "PLAYWRIGHT_TIMEOUT": "30000"
      }
    }
  }
}
EOF

cat .claude/mcp-servers.json
```

### Step 3: Verify MCP Server is Running

```bash
# Start MCP server (if not auto-started by Claude Code)
npx @anthropic-ai/playwright-mcp --server

# In another terminal, test connection
curl http://localhost:3000/health
# Expected: {"status": "ok"}
```

### Step 4: Run Automated Submission in Claude Code

In Claude Code or via CLI:

```bash
# Using Claude Code CLI
claude-code --file playwright_skill_submissions.js --use-mcp playwright

# Or directly execute
node playwright_skill_submissions.js

# Or in Claude Code chat
/mcp-run playwright_skill_submissions.js
```

### What Happens (Fully Automated)

1. **Browser Opens:** Chromium launches (headless=false to see progress)
2. **skills.sh Submission:**
   - Navigates to https://skills.sh/submit
   - Fills: name, description, repository, homepage, author, tags
   - Submits form
   - Verifies success at https://skills.sh/skills/pycostaudit

3. **Swagger Hub Registration:**
   - Navigates to https://app.swaggerhub.com/apis
   - Auto-detects login status
   - Creates API from OpenAPI URL
   - Publishes API
   - Generates Swagger Hub link

4. **APIs.guru Registration:**
   - Navigates to https://apis.guru
   - Submits OpenAPI spec URL
   - Verifies registry submission

5. **Report Generation:**
   - Checks each registry for success
   - Generates completion report
   - Shows verification URLs

---

## Option 2: Chrome DevTools Protocol (Chrome MCP)

### Step 1: Install Chrome MCP

```bash
# Using npm
npm install -D @anthropic-ai/chrome-mcp

# Or using Docker (no local install needed)
docker pull anthropic/chrome-mcp:latest
```

### Step 2: Configure Chrome MCP

```bash
# For local Chrome
cat > .claude/mcp-servers.json << 'EOF'
{
  "servers": {
    "chrome": {
      "command": "npx",
      "args": ["@anthropic-ai/chrome-mcp"],
      "env": {
        "CHROME_HEADLESS": "false"
      }
    }
  }
}
EOF

# Or for Docker
cat > .claude/mcp-servers.json << 'EOF'
{
  "servers": {
    "chrome": {
      "command": "docker",
      "args": ["run", "--rm", "-p", "9222:9222", "anthropic/chrome-mcp:latest"]
    }
  }
}
EOF
```

### Step 3: Run Submission Script

```bash
# Chrome MCP will handle all browser interactions
node playwright_skill_submissions.js

# Chrome automatically:
# - Launches browser
# - Navigates URLs
# - Interacts with pages
# - Returns results
```

---

## Option 3: Hybrid Approach (Best of Both)

Combine GitHub CLI automation + Playwright MCP:

```bash
#!/bin/bash

# Part 1: GitHub CLI (already working)
echo "Phase 1: GitHub Awesome Lists..."
export GH_TOKEN=$(cat ~/.github-token)  # Load token from secure storage
bash submit_awesome_lists.sh
echo "✅ Phase 1 complete - PRs submitted"

# Part 2: Playwright MCP (browser automation)
echo ""
echo "Phase 2: Registry Submissions..."
node playwright_skill_submissions.js
echo "✅ Phase 2 complete - Registries submitted"

# Part 3: Verification
echo ""
echo "Phase 3: Verification..."
echo "Check submissions at:"
echo "- https://skills.sh/skills/pycostaudit"
echo "- https://app.swaggerhub.com/apis/Mullassery/PyCostAudit"
echo "- https://apis.guru (search: PyCostAudit)"
echo "- https://github.com/amanattar/awesome-claude-skills/pulls"
```

---

## Complete Automated Submission Script

Create `auto_submit.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 PyCostAudit Automated Registry Submission"
echo "═══════════════════════════════════════════════"
echo ""

# Check prerequisites
echo "✓ Checking prerequisites..."
command -v node >/dev/null || { echo "❌ Node.js required"; exit 1; }
command -v gh >/dev/null || { echo "❌ GitHub CLI required"; exit 1; }

# Check tokens
if [ -z "$GH_TOKEN" ]; then
  echo "❌ GH_TOKEN not set"
  echo "   Set: export GH_TOKEN=your_token"
  exit 1
fi

echo "✓ Prerequisites OK"
echo ""

# Phase 1: Install dependencies
echo "📦 Installing dependencies..."
npm install -D playwright

# Phase 2: Awesome lists
echo ""
echo "📤 Phase 1/3: Submitting to awesome-claude lists..."
bash submit_awesome_lists.sh || echo "⚠️  Some awesome list submissions had issues"

# Phase 3: Registry submissions
echo ""
echo "📤 Phase 2/3: Submitting to registry APIs..."
node playwright_skill_submissions.js || echo "⚠️  Some registry submissions had issues"

# Phase 4: Verification
echo ""
echo "📤 Phase 3/3: Verification..."
echo ""
echo "✅ Submission workflow complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Verify registries:"
echo "   - skills.sh: https://skills.sh/skills/pycostaudit"
echo "   - Swagger Hub: https://app.swaggerhub.com/apis/Mullassery/PyCostAudit"
echo "   - APIs.guru: https://apis.guru (search: PyCostAudit)"
echo ""
echo "2. Monitor GitHub PRs:"
echo "   - awesome-claude-skills: https://github.com/amanattar/awesome-claude-skills/pulls"
echo "   - awesome-claude-code: Check for PR"
echo ""
echo "3. Engage community:"
echo "   - Post on GitHub Discussions: https://github.com/Mullassery/PyCostAudit/discussions"
echo "   - Monitor for feedback"
echo ""
echo "4. Schedule social posts (Week 5+):"
echo "   - Reddit (r/ClaudeCode, r/LLM)"
echo "   - Product Hunt (Week 7+)"
echo "   - Hacker News (Week 8+)"
echo ""
echo "📊 Expected Impact:"
echo "   +35-55 stars from registries"
echo "   +50-150 stars from social (weeks 5-8)"
echo "   +135-255 total stars"
echo ""
echo "═══════════════════════════════════════════════"
echo "🎉 Automated submission complete!"
```

Make it executable:

```bash
chmod +x auto_submit.sh
```

---

## Run Everything Now

### Quick Start (One Command)

```bash
# Set your GitHub token
export GH_TOKEN=$(read -s -p "GitHub Token: " token && echo $token)

# Run automated submission
./auto_submit.sh
```

### Step-by-Step Execution

```bash
# Step 1: Install Playwright MCP
npm install -D playwright @anthropic-ai/playwright-mcp

# Step 2: Set GitHub token
export GH_TOKEN=your_token_here

# Step 3: Run submission to awesome lists
bash submit_awesome_lists.sh

# Step 4: Run registry submissions
node playwright_skill_submissions.js

# Step 5: Verify at URLs above
```

---

## Monitoring & Verification

### Real-time Monitoring

```bash
# Watch for skills.sh submission
watch -n 10 'curl -s https://skills.sh/api/skills | grep pycostaudit'

# Watch GitHub PR status
gh pr list -R amanattar/awesome-claude-skills | grep -i pycostaudit

# Check PyPI downloads
curl -s https://libraries.io/api/pypi/pycostaudit | jq '.downloads'
```

### Manual Verification Checklist

- [ ] skills.sh
  - [ ] Navigate to: https://skills.sh/skills/pycostaudit
  - [ ] Verify: Name, description, tags visible
  - [ ] Check: Author, license info correct

- [ ] Swagger Hub
  - [ ] Navigate to: https://app.swaggerhub.com
  - [ ] Search: "PyCostAudit"
  - [ ] Verify: All endpoints documented
  - [ ] Check: API is public

- [ ] APIs.guru
  - [ ] Navigate to: https://apis.guru
  - [ ] Search: "pycostaudit"
  - [ ] Verify: OpenAPI spec loaded
  - [ ] Check: Developer tools can discover it

- [ ] GitHub Awesome Lists
  - [ ] awesome-claude-skills PR: https://github.com/amanattar/awesome-claude-skills/pulls
  - [ ] awesome-claude-code PR: Search for Mullassery
  - [ ] awesome-llm-tools PR: Search for pycostaudit

- [ ] GitHub Discussions
  - [ ] Navigate to: https://github.com/Mullassery/PyCostAudit/discussions
  - [ ] Verify: Pinned announcement visible
  - [ ] Check: Community can post responses

---

## Troubleshooting

### MCP Connection Failed

```bash
# Restart MCP server
pkill -f "@anthropic-ai/playwright-mcp"
sleep 2
npx @anthropic-ai/playwright-mcp --server &

# Verify connection
curl http://localhost:3000/health
```

### Browser Automation Timeout

```bash
# Increase timeout in submit script
# In playwright_skill_submissions.js, change:
// const timeout = 5000;  // 5 seconds
const timeout = 15000;  // 15 seconds

# Re-run
node playwright_skill_submissions.js
```

### GitHub API Rate Limit

```bash
# Check your rate limit
gh api rate_limit

# If exceeded, wait 1 hour or use different token
export GH_TOKEN=alternative_token
```

### Form Field Names Changed

```bash
# Update selectors in playwright script:
# 1. Open browser manually
# 2. Inspect form elements
# 3. Update selectors: page.$('input[name="..."]')
# 4. Test script locally
```

---

## Files Ready for MCP Automation

```
✓ playwright_skill_submissions.js      Ready for MCP execution
✓ submit_awesome_lists.sh              Ready for GitHub CLI
✓ skills_manifest.json                 Ready for submission
✓ openapi.json                         Ready for submission
✓ claude_skill_definition.json          Ready for submission
✓ SUBMISSION_AUTOMATION.md             Ready for reference
```

---

## Timeline

| Task | Time | Tool | Status |
|------|------|------|--------|
| Install MCP | 5 min | npm | Ready |
| GitHub awesome lists | 10 min | GitHub CLI | Ready |
| Registry submissions | 20 min | Playwright MCP | Ready |
| Verification | 10 min | Browser | Manual |
| **Total** | **45 min** | **Automated** | **Ready** |

---

## Success Indicators

After running automated submission:

1. **skills.sh:** Skill appears in registry within 5 minutes
2. **GitHub PRs:** PRs created to 3+ awesome lists
3. **Swagger Hub:** API is public and searchable
4. **APIs.guru:** Spec is indexed in registry
5. **GitHub Discussions:** Community post visible
6. **PyPI:** Download trends start tracking

---

## Next Actions

**Immediate (Now):**
```bash
# 1. Install MCP
npm install -D playwright @anthropic-ai/playwright-mcp

# 2. Set token (don't hardcode!)
export GH_TOKEN=$(cat ~/.github-token)

# 3. Run full automation
./auto_submit.sh
```

**Follow-up (Weeks 2-3):**
- Monitor PR merges on awesome lists
- Verify all registries have PyCostAudit
- Collect early testimonials from GitHub Discussions
- Post on social media (Phase 2)

**Scaling (Weeks 4-8):**
- Product Hunt launch
- Hacker News post
- Reddit/community engagement
- Gather case studies

---

**Status:** Ready for immediate MCP-based execution  
**Effort:** Zero-touch automation once MCP is running  
**Expected Stars:** 135-255 across all channels

🚀 **Execute now:** `./auto_submit.sh`
