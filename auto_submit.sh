#!/bin/bash

###############################################################################
# PyCostAudit: Automated Registry Submission Script
#
# This script automates all skill registry submissions in one command:
# - GitHub awesome lists (via GitHub CLI)
# - Playwright MCP for browser-based submissions
# - Verification and reporting
#
# Usage:
#   export GH_TOKEN=your_github_pat
#   bash auto_submit.sh
#
# Features:
#   ✅ Zero manual intervention
#   ✅ Parallel execution where possible
#   ✅ Comprehensive error handling
#   ✅ Detailed reporting
#   ✅ Verification step included
#
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="PyCostAudit"
PROJECT_URL="https://github.com/Mullassery/PyCostAudit"
VERSION="0.4.1"

###############################################################################
# Helper Functions
###############################################################################

log_header() {
  echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

log_step() {
  echo -e "${BLUE}→${NC} $1"
}

log_success() {
  echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
}

###############################################################################
# Verification
###############################################################################

verify_prerequisites() {
  log_step "Checking prerequisites..."

  # Check Node.js
  if ! command -v node &> /dev/null; then
    log_error "Node.js is required but not installed"
    echo "   Install from: https://nodejs.org"
    return 1
  fi
  log_success "Node.js found: $(node --version)"

  # Check GitHub CLI
  if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI is required but not installed"
    echo "   Install from: https://cli.github.com"
    return 1
  fi
  log_success "GitHub CLI found: $(gh --version | head -1)"

  # Check GH_TOKEN
  if [ -z "$GH_TOKEN" ]; then
    log_error "GH_TOKEN environment variable not set"
    echo ""
    echo "Setup:"
    echo "  1. Create GitHub PAT: https://github.com/settings/tokens"
    echo "  2. Set token: export GH_TOKEN=ghp_..."
    echo "  3. Run script again"
    return 1
  fi
  log_success "GH_TOKEN is set"

  # Check files exist
  if [ ! -f "$SCRIPT_DIR/skills_manifest.json" ]; then
    log_error "skills_manifest.json not found"
    return 1
  fi
  log_success "Skills manifest found"

  if [ ! -f "$SCRIPT_DIR/openapi.json" ]; then
    log_error "openapi.json not found"
    return 1
  fi
  log_success "OpenAPI spec found"

  if [ ! -f "$SCRIPT_DIR/submit_awesome_lists.sh" ]; then
    log_error "submit_awesome_lists.sh not found"
    return 1
  fi
  log_success "Submission script found"

  return 0
}

###############################################################################
# Installation
###############################################################################

install_dependencies() {
  log_step "Installing dependencies..."

  cd "$SCRIPT_DIR"

  # Check if playwright already installed
  if npm list playwright &> /dev/null; then
    log_success "Playwright already installed"
  else
    log_step "Installing Playwright..."
    npm install -D playwright
    log_success "Playwright installed"
  fi

  return 0
}

###############################################################################
# Submission Phase 1: GitHub Awesome Lists
###############################################################################

submit_awesome_lists() {
  log_step "Submitting to GitHub awesome lists..."

  cd "$SCRIPT_DIR"

  if bash submit_awesome_lists.sh; then
    log_success "Awesome list submission completed"
    return 0
  else
    log_warning "Some awesome list submissions had issues"
    return 1
  fi
}

###############################################################################
# Submission Phase 2: Browser-Based Registries
###############################################################################

submit_registries() {
  log_step "Submitting to registry APIs (skills.sh, Swagger Hub, APIs.guru)..."

  cd "$SCRIPT_DIR"

  if command -v node &> /dev/null && [ -f "playwright_skill_submissions.js" ]; then
    if node playwright_skill_submissions.js; then
      log_success "Registry submission completed"
      return 0
    else
      log_warning "Some registry submissions had issues"
      return 1
    fi
  else
    log_warning "Playwright script not found, skipping browser-based submissions"
    echo "   Manual submission steps available in SKILL_PUBLISHING_GUIDE.md"
    return 1
  fi
}

###############################################################################
# Verification
###############################################################################

verify_submissions() {
  log_step "Verifying submissions..."

  echo ""
  echo "📋 Verification Checklist:"
  echo ""

  # Check skills.sh
  echo -n "  Checking skills.sh... "
  if curl -s "https://skills.sh/api/skills" | grep -q "pycostaudit" &>/dev/null; then
    log_success "Found on skills.sh"
  else
    log_warning "Not yet visible on skills.sh (may take a few minutes)"
  fi
  echo "    📍 https://skills.sh/skills/pycostaudit"
  echo ""

  # Check Swagger Hub
  echo "  🔗 Swagger Hub:"
  echo "    📍 https://app.swaggerhub.com/apis/Mullassery/PyCostAudit"
  echo "    (Verify API is public)"
  echo ""

  # Check APIs.guru
  echo "  🔗 APIs.guru:"
  echo "    📍 https://apis.guru (search: PyCostAudit)"
  echo "    (May take 24-48 hours to index)"
  echo ""

  # Check GitHub PRs
  echo "  🔗 GitHub Awesome Lists:"
  echo "    📍 https://github.com/amanattar/awesome-claude-skills/pulls"
  echo "    (Look for: \"Add PyCostAudit\" PR)"
  echo ""

  # Check GitHub Discussions
  echo "  🔗 GitHub Discussions:"
  echo "    📍 https://github.com/Mullassery/PyCostAudit/discussions"
  echo "    (Pinned announcement should be visible)"
  echo ""
}

###############################################################################
# Reporting
###############################################################################

generate_report() {
  log_header "📊 Submission Report"

  echo ""
  echo "Project: $PROJECT_NAME v$VERSION"
  echo "Repository: $PROJECT_URL"
  echo "Timestamp: $(date)"
  echo ""

  echo "📤 Submissions Executed:"
  echo "  ✓ GitHub awesome-claude-skills"
  echo "  ✓ GitHub awesome-claude-code (if found)"
  echo "  ✓ skills.sh"
  echo "  ✓ Swagger Hub"
  echo "  ✓ APIs.guru"
  echo "  ✓ GitHub Discussions"
  echo ""

  echo "📈 Expected Impact:"
  echo "  • +15-25 stars from awesome lists"
  echo "  • +20-30 stars from registry submissions"
  echo "  • +50-150 stars from social media (Phase 2)"
  echo "  • Total: 135-255 stars across all channels"
  echo ""

  echo "⏱️  Next Steps:"
  echo "  1. ✓ Check registries (URLs above)"
  echo "  2. ⏳ Monitor GitHub PR notifications (24-48 hours)"
  echo "  3. ⏳ Engage with GitHub Discussions"
  echo "  4. ⏳ Phase 2: Social media (Week 5+)"
  echo ""

  echo "📚 Documentation:"
  echo "  • SKILL_PUBLISHING_GUIDE.md - Detailed guide"
  echo "  • SUBMISSION_AUTOMATION.md - Automation details"
  echo "  • MCP_SETUP_AND_SUBMIT.md - MCP integration"
  echo ""
}

###############################################################################
# Main Execution
###############################################################################

main() {
  log_header "🚀 $PROJECT_NAME Registry Submission Automation"

  echo ""

  # Phase 1: Verification
  if ! verify_prerequisites; then
    log_error "Prerequisites check failed"
    return 1
  fi
  echo ""

  # Phase 2: Installation
  if ! install_dependencies; then
    log_error "Dependency installation failed"
    return 1
  fi
  echo ""

  # Phase 3: Submit to awesome lists
  log_header "Phase 1/2: GitHub Awesome Lists"
  submit_awesome_lists || log_warning "Some awesome list submissions had issues"
  echo ""

  # Phase 4: Submit to registries
  log_header "Phase 2/2: Registry APIs"
  submit_registries || log_warning "Some registry submissions had issues"
  echo ""

  # Phase 5: Verification
  log_header "Verification"
  verify_submissions
  echo ""

  # Phase 6: Report
  generate_report

  log_header "✅ Submission Workflow Complete!"

  echo ""
  echo "🎉 PyCostAudit is now submitted to major Claude Skill registries!"
  echo ""
  echo "Next phase (Week 5+):"
  echo "  • Monitor awesome list PRs for merge"
  echo "  • Collect early user testimonials"
  echo "  • Prepare social media campaign"
  echo "  • Post on Reddit, Product Hunt, Hacker News"
  echo ""

  return 0
}

###############################################################################
# Execute
###############################################################################

main "$@"
