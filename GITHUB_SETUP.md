# GitHub & VSCode Setup Guide

## Overview
This guide shows how to:
1. Link GitHub account to VSCode
2. Configure Git locally
3. Initialize repository
4. Push code to GitHub
5. Enable GitHub Actions pipeline

---

## Part 1: GitHub Account Setup

### Step 1.1: Create GitHub Personal Access Token

1. Go to **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Set permissions:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (GitHub Actions)
   - ✅ `read:user` (Read user profile)
4. Set expiration: **90 days** or **No expiration**
5. Click **"Generate token"**
6. **COPY THE TOKEN** (you won't see it again!)

**Save this token safely** - you'll need it for authentication.

### Step 1.2: Create GitHub Repository

1. Go to **https://github.com/new**
2. Repository name: `warehouse-arch` (or your preference)
3. Description: `Warehouse Path Finder - Streamlit Application`
4. Choose **Public** or **Private** (Public recommended for CI/CD)
5. Do NOT initialize with README (we have one)
6. Click **"Create repository"**

**Copy your repository URL** - it will look like:
```
https://github.com/YOUR-USERNAME/warehouse-arch.git
```

---

## Part 2: Git Configuration

### Step 2.1: Install Git
```bash
# Check if Git is installed
git --version

# If not installed (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install git

# If not installed (macOS)
brew install git
```

### Step 2.2: Configure Git Globally
```bash
# Set your name
git config --global user.name "Your Name"

# Set your email (use your GitHub email)
git config --global user.email "connectsid17@gmail.com"

# Verify configuration
git config --global --list
```

### Step 2.3: Store GitHub Credentials

#### Option A: GitHub CLI (Recommended)
```bash
# Install GitHub CLI
# Ubuntu/Debian
sudo apt-get install gh

# macOS
brew install gh

# Authenticate
gh auth login

# Select: HTTPS
# When asked for credentials, paste your Personal Access Token
# When asked to authenticate Git, select: Yes
```

#### Option B: Git Credential Manager (Alternative)
```bash
# Install Git Credential Manager
# Ubuntu/Debian
sudo apt-get install git-credential-manager

# Configure Git to use it
git config --global credential.helper manager
```

#### Option C: SSH Keys (Advanced)
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "connectsid17@gmail.com"
# Press Enter for default location
# Set a passphrase (optional but recommended)

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Display public key (copy this)
cat ~/.ssh/id_ed25519.pub

# Add to GitHub:
# 1. Go to https://github.com/settings/keys
# 2. Click "New SSH key"
# 3. Paste the public key
# 4. Click "Add SSH key"

# Test connection
ssh -T git@github.com
# Should show: "Hi USERNAME! You've successfully authenticated..."

# Configure Git to use SSH
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

---

## Part 3: Initialize Local Git Repository

### Step 3.1: Set Up Repository
```bash
cd /home/vvdn/Documents/warehouse_arch

# Initialize git repository
git init

# Verify
git status
```

### Step 3.2: Add Files to Git
```bash
# Check what's new
git status

# Add all files
git add .

# Verify staging
git status

# Commit initial code
git commit -m "Initial commit: Warehouse Path Finder with deployment pipeline"
```

### Step 3.3: Connect to GitHub Remote
```bash
# Replace YOUR-USERNAME with your GitHub username
git remote add origin https://github.com/YOUR-USERNAME/warehouse-arch.git

# Verify remote
git remote -v
# Should show:
# origin  https://github.com/YOUR-USERNAME/warehouse-arch.git (fetch)
# origin  https://github.com/YOUR-USERNAME/warehouse-arch.git (push)
```

### Step 3.4: Push Code to GitHub
```bash
# Rename branch to main (if needed)
git branch -M main

# Push code to GitHub
git push -u origin main

# Verify on GitHub
# Go to https://github.com/YOUR-USERNAME/warehouse-arch
# You should see your files!
```

---

## Part 4: VSCode GitHub Integration

### Step 4.1: VSCode Extensions

Install these extensions in VSCode:

1. **GitHub Pull Requests and Issues**
   - Open VSCode
   - Go to Extensions (Ctrl+Shift+X)
   - Search: `GitHub Pull Requests and Issues`
   - Click Install
   - Reload VSCode

2. **GitLens** (Optional but recommended)
   - Search: `GitLens`
   - Install

3. **GitHub Copilot** (Optional)
   - Search: `GitHub Copilot`
   - Install (requires paid subscription)

### Step 4.2: Authenticate VSCode with GitHub

**Method 1: Built-in Synchronization**
1. Open Command Palette: `Ctrl+Shift+P`
2. Type: `GitHub: Authorize`
3. Click option to sign in with GitHub
4. Opens browser → authenticate → approve
5. Return to VSCode (should be auto-authorized)

**Method 2: Manual Source Control**
1. Click Source Control icon (left sidebar)
2. Click "Initialize Repository"
3. If prompted for GitHub, click "Sign in with GitHub"
4. Complete authentication in browser

### Step 4.3: Verify Authentication

```bash
# In terminal, verify Git is configured
git config --global user.name
git config --global user.email

# Test with GitHub CLI
gh auth status
# Should show: ✓ Logged in to github.com as YOUR-USERNAME
```

---

## Part 5: Enable GitHub Actions CI/CD

### Step 5.1: Verify Workflow File

The workflow file should already exist at:
```
.github/workflows/deploy.yml
```

### Step 5.2: Check GitHub Actions

1. Go to your GitHub repository
2. Click **"Actions"** tab (top menu)
3. You should see "Local Deployment Pipeline" workflow
4. If not visible, click "I understand my workflows, go ahead and enable them"

### Step 5.3: Configure Secrets (if needed)

For future cloud deployments, add secrets:

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**

Example secrets to add:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
DOCKER_HUB_USERNAME
DOCKER_HUB_TOKEN
```

### Step 5.4: Test the Pipeline

1. Make a small change to the code:
   ```bash
   echo "# Test" >> test.txt
   ```

2. Commit and push:
   ```bash
   git add .
   git commit -m "Test: Trigger CI/CD pipeline"
   git push
   ```

3. Go to GitHub → **Actions** tab
4. You should see the workflow running
5. Wait for it to complete (green checkmark = success)

---

## Part 6: Day-to-Day Git Workflow

### Check Status
```bash
git status
```

### Make Changes & Commit
```bash
# Edit files in VSCode

# Stage changes
git add .

# Or stage specific files
git add streamlit_app.py

# Commit with message
git commit -m "Feature: Add new functionality"

# Push to GitHub
git push
```

### Create Branches
```bash
# Create new branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push branch to GitHub
git push -u origin feature/new-feature

# On GitHub: Create Pull Request
# Go to repository → Pull requests → New
# Select your branch → Create PR
# Wait for CI/CD checks to pass
# Merge PR
```

### Pull Latest Changes
```bash
# Update local repo
git pull

# Or fetch without merging
git fetch
```

---

## Part 7: Verify Everything is Linked

### Checklist
- [ ] GitHub account created
- [ ] Personal Access Token generated
- [ ] Local Git configured (`git config --global --list`)
- [ ] Repository initialized (`git init`)
- [ ] Remote added (`git remote -v`)
- [ ] Code pushed to GitHub
- [ ] VSCode GitHub extension installed
- [ ] VSCode authenticated with GitHub
- [ ] GitHub Actions workflow visible
- [ ] First commit triggered workflow

### Verification Commands
```bash
# Check Git configuration
git config --global user.name
git config --global user.email

# Check remote
git remote -v

# Check GitHub CLI
gh auth status

# Check last commits
git log --oneline -5

# Check branches
git branch -a
```

---

## Part 8: Troubleshooting

### "fatal: Authentication failed"
```bash
# Clear stored credentials
git config --global --unset credential.helper

# Re-authenticate with GitHub CLI
gh auth login

# Or use Personal Access Token instead of password
# When prompted for password, paste your token
```

### "remote: Permission denied"
```bash
# Check if using HTTPS or SSH
git remote -v

# If HTTPS and getting permission denied, use Personal Access Token:
# git push origin main
# Username: YOUR-USERNAME
# Password: YOUR-PERSONAL-ACCESS-TOKEN

# Or switch to SSH:
git remote set-url origin git@github.com:YOUR-USERNAME/warehouse-arch.git
```

### "fatal: could not read Password for 'https://github.com'"
```bash
# Store credentials (HTTPS)
git config --global credential.helper store

# Or use GitHub CLI (recommended)
gh auth login
```

### VSCode Not Showing GitHub Integration
```bash
# Reload VSCode
# Command Palette → Developer: Reload Window

# Or reinstall extension
# Remove: GitHub Pull Requests and Issues
# Reinstall from marketplace
```

### GitHub Actions Workflow Not Running
1. Check if workflow file exists: `.github/workflows/deploy.yml`
2. Go to repository **Settings** → **Actions** → **General**
3. Ensure "Actions permissions" is set to "Allow all actions and reusable workflows"
4. Push a new commit to trigger workflow

---

## Part 9: Quick Reference

### Git Commands
```bash
git init                      # Initialize repo
git add .                     # Stage all files
git commit -m "message"       # Commit with message
git push                      # Push to GitHub
git pull                      # Pull from GitHub
git branch feature/name       # Create branch
git checkout feature/name     # Switch branch
git log                       # View commit history
git status                    # Check status
```

### GitHub CLI
```bash
gh auth login                 # Authenticate
gh auth status                # Check auth status
gh repo create               # Create new repo
gh pr create                 # Create pull request
gh pr list                   # List PRs
gh issue list                # List issues
```

### VSCode Shortcuts
```
Ctrl+Shift+P  → Command Palette
Ctrl+`        → Open Terminal
Ctrl+G        → Go to Line
Ctrl+B        → Toggle Sidebar
```

---

## Part 10: Next Steps

Once everything is linked:

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Monitor GitHub Actions**
   - Go to repository → Actions tab
   - Watch pipeline run automatically

3. **Enable Branch Protection** (Optional)
   - Settings → Branches → Add rule
   - Require PR reviews before merge
   - Require CI/CD checks to pass

4. **Set Up Deployment Triggers**
   - Edit `.github/workflows/deploy.yml`
   - Change branch triggers as needed
   - Deploy on push to `main` branch

5. **Scale to Cloud**
   - Add cloud provider credentials to Secrets
   - Update workflow to deploy to AWS/GCP
   - See DEPLOYMENT.md for cloud instructions

---

## Summary

You now have:
✅ GitHub account linked with VSCode  
✅ Git repository initialized locally  
✅ Code pushed to GitHub  
✅ CI/CD pipeline ready (GitHub Actions)  
✅ All credentials stored safely  

When you push code to GitHub, the pipeline will:
1. Build Docker image
2. Run security scans
3. Push to container registry
4. Deploy to local environment
5. Send status notifications

Happy coding! 🚀
