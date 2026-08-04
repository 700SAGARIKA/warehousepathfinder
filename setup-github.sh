#!/bin/bash

#############################################
# GitHub & VSCode Setup Script
# Automates local Git configuration
#############################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
check_git() {
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        echo "Install with: sudo apt-get install git (Ubuntu/Debian) or brew install git (macOS)"
        exit 1
    fi
    print_success "Git is installed"
}

check_github_cli() {
    if command -v gh &> /dev/null; then
        print_success "GitHub CLI is installed"
        return 0
    else
        print_warning "GitHub CLI is not installed (recommended)"
        return 1
    fi
}

# Configure Git
configure_git() {
    print_header "Step 1: Configure Git"

    read -p "Enter your name: " git_name
    read -p "Enter your email (GitHub email): " git_email

    git config --global user.name "$git_name"
    git config --global user.email "$git_email"

    print_success "Git configured"
    echo "  Name:  $git_name"
    echo "  Email: $git_email"

    # Store credentials
    read -p "Store Git credentials? (y/n): " store_creds
    if [[ "$store_creds" == "y" || "$store_creds" == "Y" ]]; then
        git config --global credential.helper store
        print_success "Credentials will be stored after first push"
    fi
}

# Initialize repository
init_repository() {
    print_header "Step 2: Initialize Git Repository"

    if [ -d ".git" ]; then
        print_warning "Git repository already initialized"
    else
        git init
        print_success "Repository initialized"
    fi

    # Create .gitignore if not exists
    if [ ! -f ".gitignore" ]; then
        cat > .gitignore << 'EOF'
# Virtual environments
venv/
env/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Streamlit
.streamlit/

# Docker
docker-compose.override.yml

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# Uploads
uploads/
EOF
        print_success "Created .gitignore"
    fi

    # Check git status
    echo ""
    git status
}

# Connect to GitHub
connect_github() {
    print_header "Step 3: Connect to GitHub Remote"

    echo "You need to:"
    echo "1. Create a repository on GitHub: https://github.com/new"
    echo "2. Repository name: warehouse-arch"
    echo "3. Do NOT initialize with README/gitignore"
    echo ""

    read -p "Have you created the GitHub repository? (y/n): " repo_created
    if [[ "$repo_created" != "y" && "$repo_created" != "Y" ]]; then
        print_warning "Please create the repository first, then run this script again"
        return 1
    fi

    read -p "Enter your GitHub username: " github_username

    repo_url="https://github.com/${github_username}/warehouse-arch.git"

    # Check if remote already exists
    if git remote | grep -q "origin"; then
        print_warning "Remote 'origin' already exists"
        read -p "Remove and reconfigure? (y/n): " reconfig
        if [[ "$reconfig" == "y" || "$reconfig" == "Y" ]]; then
            git remote remove origin
            git remote add origin "$repo_url"
        fi
    else
        git remote add origin "$repo_url"
    fi

    print_success "Remote configured"
    echo "  URL: $repo_url"

    git remote -v
}

# Initial commit and push
commit_and_push() {
    print_header "Step 4: Commit and Push Code"

    # Check if there are changes
    if [ -z "$(git status -s)" ]; then
        print_warning "No changes to commit"
        return 0
    fi

    echo "Files to commit:"
    git status -s

    read -p "Commit all files? (y/n): " do_commit
    if [[ "$do_commit" != "y" && "$do_commit" != "Y" ]]; then
        print_warning "Skipped commit"
        return 1
    fi

    git add .
    git commit -m "Initial commit: Warehouse Path Finder with deployment pipeline"
    print_success "Code committed"

    # Ensure main branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$current_branch" != "main" ]; then
        git branch -M main
        print_success "Renamed branch to 'main'"
    fi

    echo ""
    echo "Ready to push to GitHub."
    echo "You will be prompted for authentication."
    echo ""

    read -p "Push to GitHub? (y/n): " do_push
    if [[ "$do_push" == "y" || "$do_push" == "Y" ]]; then
        git push -u origin main
        print_success "Code pushed to GitHub!"
        echo "View your repository at: https://github.com/${github_username}/warehouse-arch"
    else
        print_warning "Skipped push (you can do this manually with: git push -u origin main)"
    fi
}

# Setup GitHub CLI authentication
setup_github_cli() {
    if ! check_github_cli; then
        print_header "GitHub CLI Setup"
        echo "Install GitHub CLI for easier authentication:"
        echo "  Ubuntu/Debian: sudo apt-get install gh"
        echo "  macOS: brew install gh"
        echo "  Then run: gh auth login"
        return 0
    fi

    print_header "Step 5: GitHub CLI Authentication"

    if gh auth status > /dev/null 2>&1; then
        print_success "Already authenticated with GitHub"
        gh auth status
    else
        echo "Authenticating with GitHub..."
        gh auth login
    fi
}

# Setup VSCode extensions
setup_vscode() {
    print_header "Step 6: VSCode Setup (Manual)"

    echo "Install these extensions in VSCode:"
    echo ""
    echo "1. GitHub Pull Requests and Issues"
    echo "   - Open VSCode"
    echo "   - Go to Extensions (Ctrl+Shift+X)"
    echo "   - Search: 'GitHub Pull Requests and Issues'"
    echo "   - Click Install"
    echo ""
    echo "2. GitLens (Optional)"
    echo "   - Search: 'GitLens'"
    echo "   - Click Install"
    echo ""
    echo "Then restart VSCode and authenticate:"
    echo "   - Command Palette (Ctrl+Shift+P)"
    echo "   - Type: 'GitHub: Authorize'"
    echo "   - Follow the prompts"
    echo ""

    if command -v code &> /dev/null; then
        read -p "Open VSCode now? (y/n): " open_vscode
        if [[ "$open_vscode" == "y" || "$open_vscode" == "Y" ]]; then
            code .
        fi
    fi
}

# Show verification checklist
show_verification() {
    print_header "Verification Checklist"

    echo "Check these items to verify everything is set up:"
    echo ""

    # Git config
    if git config --global user.name > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Git name configured: $(git config --global user.name)"
    else
        echo -e "${RED}✗${NC} Git name not configured"
    fi

    if git config --global user.email > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Git email configured: $(git config --global user.email)"
    else
        echo -e "${RED}✗${NC} Git email not configured"
    fi

    # Repository
    if [ -d ".git" ]; then
        echo -e "${GREEN}✓${NC} Repository initialized"
    else
        echo -e "${RED}✗${NC} Repository not initialized"
    fi

    # Remote
    if git remote | grep -q "origin"; then
        echo -e "${GREEN}✓${NC} Remote configured: $(git remote get-url origin)"
    else
        echo -e "${RED}✗${NC} Remote not configured"
    fi

    # Commits
    commit_count=$(git rev-list --count HEAD 2>/dev/null || echo "0")
    if [ "$commit_count" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Commits created: $commit_count"
    else
        echo -e "${YELLOW}⚠${NC} No commits yet"
    fi

    # GitHub CLI
    if command -v gh &> /dev/null && gh auth status > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} GitHub CLI authenticated"
    else
        echo -e "${YELLOW}⚠${NC} GitHub CLI not authenticated (optional)"
    fi

    echo ""
}

# Show summary
show_summary() {
    print_header "Setup Complete!"

    echo "You're all set! Here's what's next:"
    echo ""
    echo "1. View your repository on GitHub:"
    github_username=$(git config user.name 2>/dev/null || echo "USERNAME")
    echo "   https://github.com/$(git config user.name 2>/dev/null || echo 'YOUR-USERNAME')/warehouse-arch"
    echo ""
    echo "2. Check GitHub Actions (CI/CD Pipeline):"
    echo "   Go to repository → Actions tab"
    echo "   Your workflow should run automatically on next push"
    echo ""
    echo "3. Install VSCode extensions:"
    echo "   Ctrl+Shift+X → Search 'GitHub Pull Requests and Issues'"
    echo ""
    echo "4. VSCode GitHub authentication:"
    echo "   Ctrl+Shift+P → 'GitHub: Authorize'"
    echo ""
    echo "5. Make changes and push:"
    echo "   git add ."
    echo "   git commit -m 'Your message'"
    echo "   git push"
    echo ""
    echo "For more details, see GITHUB_SETUP.md"
    echo ""
}

# Main execution
main() {
    clear
    print_header "Warehouse Path Finder - GitHub Setup"

    check_git
    configure_git
    init_repository

    if connect_github; then
        commit_and_push
    else
        return 1
    fi

    if check_github_cli; then
        setup_github_cli
    fi

    setup_vscode
    show_verification
    show_summary
}

# Run main
main

exit 0
