#!/bin/bash
# Install PyCostAudit Skill for Claude Code

set -e

SKILL_DIR="/Users/georgimullassery/PyCostAudit"
BIN_DIR="$HOME/.local/bin"
SKILL_LINK="$BIN_DIR/cost-audit"

# Create bin directory if needed
mkdir -p "$BIN_DIR"

# Create symlink to skill
ln -sf "$SKILL_DIR/pycostaudit_skill.py" "$SKILL_LINK"
chmod +x "$SKILL_LINK"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.zshrc
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.bashrc
fi

echo "✅ PyCostAudit Skill installed!"
echo ""
echo "Usage:"
echo "  cost-audit report              # Show today's costs"
echo "  cost-audit track <op> <in> <out>  # Track operation"
echo "  cost-audit forecast            # Weekly forecast"
echo "  cost-audit alerts              # Check alerts"
echo ""
echo "Reload shell to use: source ~/.zshrc"
