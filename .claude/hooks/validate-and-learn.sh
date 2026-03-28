#!/bin/bash
# Hook: validate-and-learn.sh
# Runs when Claude finishes a response (Stop event).
# Checks if there are signs of issues and reminds Claude to update learnings.
#
# Exit codes:
#   0 = success, pass context back to Claude
#   1 = error in hook itself
#   2 = block (not used here)

LEARNINGS_FILE="$CLAUDE_PROJECT_DIR/.claude/learnings.md"

# Ensure learnings file exists
if [ ! -f "$LEARNINGS_FILE" ]; then
  cat > "$LEARNINGS_FILE" << 'INIT'
# Learnings

Erfarenheter och misstag från tidigare sessioner. Läs denna fil vid start av nya sessioner för att undvika att upprepa samma fel.
INIT
fi

# Count current learnings
LEARNING_COUNT=$(grep -c "^## " "$LEARNINGS_FILE" 2>/dev/null || echo "0")

# Pass context back to Claude as a gentle reminder
cat << EOF
Reminder: If any mistakes, unexpected issues, or useful insights came up during this response, append them to .claude/learnings.md (currently has $LEARNING_COUNT entries). Check the existing entries first to avoid duplicates.
EOF

exit 0
