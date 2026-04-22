#!/bin/bash
# GitHub Repository Setup Script for Telecom RAG

set -e

echo "🚀 Setting up GitHub Repository for Telecom RAG"
echo "================================================"
echo ""

# Check if Git is configured
echo "📋 Step 1: Checking Git Configuration"
if ! git config --global user.name &>/dev/null; then
    echo "⚠️  Git user.name not configured"
    read -p "Enter your name: " git_name
    git config --global user.name "$git_name"
    echo "✅ Set user.name to: $git_name"
else
    echo "✅ Git user.name: $(git config --global user.name)"
fi

if ! git config --global user.email &>/dev/null; then
    echo "⚠️  Git user.email not configured"
    read -p "Enter your email: " git_email
    git config --global user.email "$git_email"
    echo "✅ Set user.email to: $git_email"
else
    echo "✅ Git user.email: $(git config --global user.email)"
fi

echo ""
echo "📋 Step 2: Initializing Git Repository"
if [ -d .git ]; then
    echo "✅ Git repository already initialized"
else
    git init
    echo "✅ Initialized Git repository"
fi

echo ""
echo "📋 Step 3: Verifying .gitignore"
if [ -f .gitignore ]; then
    echo "✅ .gitignore exists"
    echo "   Checking for .env..."
    if grep -q "^\.env$" .gitignore; then
        echo "   ✅ .env is ignored (secrets safe)"
    else
        echo "   ⚠️  Adding .env to .gitignore"
        echo ".env" >> .gitignore
    fi
else
    echo "⚠️  Creating .gitignore"
    cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
.env
venv/
env/
.DS_Store
google-cloud-sdk/
Docker.dmg
*.egg-info
dist/
build/
EOF
    echo "✅ Created .gitignore"
fi

echo ""
echo "📋 Step 4: Adding Files to Git"
git add .
echo "✅ Added all files (respecting .gitignore)"

echo ""
echo "📋 Step 5: Creating Initial Commit"
if git rev-parse HEAD &>/dev/null; then
    echo "✅ Repository already has commits"
    echo "   Creating new commit with recent changes..."
    git commit -m "feat: Update Telecom RAG with Cloud Run deployment

- Fixed .env configuration (removed quotes)
- Added OrbStack optimization
- Deployed to Cloud Run successfully
- Added comprehensive documentation
- 32,802 documents loaded
- Hybrid search enabled" || echo "   ℹ️  No changes to commit"
else
    git commit -m "feat: Initial commit - Telecom RAG System

- Hybrid search (BM25 + Dense + RRF)
- 32,802 telecom documents
- RAGAS evaluation metrics
- Cloud Run deployment ready
- OrbStack optimized
- Comprehensive documentation"
    echo "✅ Created initial commit"
fi

echo ""
echo "📋 Step 6: GitHub Repository Setup"
echo ""
echo "Now you need to create a private repository on GitHub:"
echo ""
echo "1. Go to: https://github.com/new"
echo "2. Repository name: telecom-rag"
echo "3. Description: AI-powered Telecom Operations Assistant with RAG"
echo "4. Visibility: ✅ Private"
echo "5. Do NOT initialize with README, .gitignore, or license"
echo "6. Click 'Create repository'"
echo ""
read -p "Press Enter after creating the repository on GitHub..."

echo ""
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/telecom-rag.git): " repo_url

echo ""
echo "📋 Step 7: Adding Remote and Pushing"
git remote add origin "$repo_url" 2>/dev/null || git remote set-url origin "$repo_url"
echo "✅ Added remote: $repo_url"

echo ""
echo "🚀 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Successfully pushed to GitHub!"
echo ""
echo "📊 Repository Summary:"
echo "   URL: $repo_url"
echo "   Branch: main"
echo "   Visibility: Private"
echo ""
echo "🎉 Done! Your code is now on GitHub."
echo ""
echo "💡 Next Steps:"
echo "   1. Visit your repository: ${repo_url%.git}"
echo "   2. Add a README if needed"
echo "   3. Set up branch protection rules (optional)"
echo "   4. Add collaborators (optional)"
