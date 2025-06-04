#!/bin/bash

echo "🔍 Quick Security Check for GitHub"
echo "================================="

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Secrets and credentials
secrets.py
config_local.py
wifi_credentials.py
.env
*.secret

# Logs and runtime files
*.log
logs/
device_id.txt
local_config.json

# Python cache
__pycache__/
*.pyc

# IDE files
.vscode/
.idea/
*.swp

# OS files
.DS_Store
Thumbs.db
EOF
    echo "✅ .gitignore created"
else
    echo "✅ .gitignore already exists"
fi

# Check for potential secrets
echo ""
echo "🔍 Scanning for potential secrets..."

FOUND_SECRETS=false

# Look for hardcoded secrets (actual string values, not config references)
PATTERNS=(
    "password.*=.*['\"][^'\"]{3,}['\"]"
    "ssid.*=.*['\"][^'\"]{3,}['\"]" 
    "api_key.*=.*['\"][^'\"]{10,}['\"]"
    "token.*=.*['\"][^'\"]{10,}['\"]"
    "secret.*=.*['\"][^'\"]{5,}['\"]"
)

for pattern in "${PATTERNS[@]}"; do
    results=$(grep -r -i -E "$pattern" --include="*.py" --exclude="*template*" --exclude="secrets.py" --exclude="*backup*" . 2>/dev/null)
    if [ ! -z "$results" ]; then
        # Filter out obvious config references
        filtered_results=$(echo "$results" | grep -v "self\.config\." | grep -v "config\[" | grep -v "\.get(")
        if [ ! -z "$filtered_results" ]; then
            FOUND_SECRETS=true
            echo "❌ Found hardcoded secrets:"
            echo "$filtered_results"
            echo ""
        fi
    fi
done

# Check for common WiFi/network strings
wifi_check=$(grep -r -i "wifi\|ssid" --include="*.py" . | grep -E "=.*['\"][^'\"]{3,}['\"]" 2>/dev/null)
if [ ! -z "$wifi_check" ]; then
    echo "⚠️  Found WiFi-related strings (check if these are secrets):"
    echo "$wifi_check"
    echo ""
fi

# Summary
echo "📋 SUMMARY"
echo "=========="

if [ "$FOUND_SECRETS" = true ]; then
    echo "❌ POTENTIAL SECRETS FOUND - DO NOT PUSH YET"
    echo ""
    echo "📝 Next steps:"
    echo "1. Move secrets to a secrets.py file"
    echo "2. Update your code to import from secrets.py"
    echo "3. Test that everything still works"
    echo "4. Run this script again to verify"
else
    echo "✅ No obvious secrets found"
    echo "✅ .gitignore is set up"
    echo "🚀 You should be safe to push to GitHub"
fi

echo ""
echo "💡 To double-check manually:"
echo "   grep -r \"password\\|api\" --include=\"*.py\" ."