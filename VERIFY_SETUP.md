# Verify GitHub & VSCode Setup

Use this guide to check if everything is correctly linked and configured.

---

## Quick Check (30 seconds)

### 1. Check Git Configuration
```bash
git config --global user.name
git config --global user.email
```

**Expected Output:**
```
Your Name
connectsid17@gmail.com
```

### 2. Check Git Repository
```bash
git remote -v
```

**Expected Output:**
```
origin  https://github.com/YOUR-USERNAME/warehouse-arch.git (fetch)
origin  https://github.com/YOUR-USERNAME/warehouse-arch.git (push)
```

### 3. Check GitHub CLI
```bash
gh auth status
```

**Expected Output:**
```
✓ Logged in to github.com as YOUR-USERNAME
  Git operations for github.com configured to use https protocol.
  Token: gho_****...
```

### 4. Verify Code on GitHub
Go to: `https://github.com/YOUR-USERNAME/warehouse-arch`

**Expected:**
- Repository visible
- Your files present (streamlit_app.py, Dockerfile, etc.)
- README.md displayed
- Commits showing

### 5. Check GitHub Actions
Go to: `https://github.com/YOUR-USERNAME/warehouse-arch/actions`

**Expected:**
- "Local Deployment Pipeline" workflow visible
- Workflow runs on commits

---

## Detailed Verification Checklist

### ✅ Git Installed & Configured
```bash
# Check version
git --version
# Should show: git version X.X.X

# Check configuration
git config --global --list
# Should show your name and email
```

### ✅ Repository Initialized
```bash
# Check .git folder
ls -la .git
# Should show git configuration

# Check status
git status
# Should show branch info
```

### ✅ Code Pushed to GitHub
```bash
# Check commits
git log --oneline -3
# Should show commits

# Check branch
git branch
# Should show: * main

# Check remote
git remote -v
# Should show origin URL
```

### ✅ VSCode Extensions Installed
In VSCode:
1. Press `Ctrl+Shift+X` (Extensions)
2. Search for: `GitHub Pull Requests and Issues`
3. Should show as "Installed"

Alternative:
```bash
# List installed extensions
code --list-extensions | grep -i github
# Should show:
# github.vscode-pull-request-github
```

### ✅ VSCode Authenticated with GitHub
In VSCode:
1. Click **Source Control** icon (left sidebar)
2. Or press `Ctrl+Shift+G`
3. Should show your GitHub username
4. Or run: `Ctrl+Shift+P` → `GitHub: Show Status`

### ✅ GitHub Actions Workflow Exists
```bash
# Check workflow file
ls -la .github/workflows/
# Should show: deploy.yml

# View workflow content
cat .github/workflows/deploy.yml
# Should show workflow definition
```

---

## Verification by Component

### Git & GitHub CLI

#### ✓ Git Configured
```bash
git config --global --list | grep user
```
Should show your name and email.

#### ✓ GitHub CLI Installed
```bash
which gh
gh --version
```
Should show path and version.

#### ✓ GitHub CLI Authenticated
```bash
gh auth status
```
Should show:
```
✓ Logged in to github.com as YOUR-USERNAME
```

#### ✓ Can Create Issues (GitHub CLI)
```bash
gh issue list --repo YOUR-USERNAME/warehouse-arch
```
Should work without authentication errors.

---

### Git Repository

#### ✓ Repository Initialized
```bash
test -d .git && echo "✓ Repository exists" || echo "✗ Not a repository"
```

#### ✓ Files Committed
```bash
git status
# Should show: nothing to commit, working tree clean
# OR: modified/untracked files (if you made changes)
```

#### ✓ Remote Configured
```bash
git remote -v | grep origin
# Should show GitHub URL
```

#### ✓ Commits Synced
```bash
git log --oneline -1
# Should show recent commits

# Compare with GitHub
git ls-remote origin HEAD
# Should show latest commit hash
```

---

### VSCode & GitHub Integration

#### ✓ VSCode Can Access Git
In VSCode Terminal:
```bash
git status
# Should work without errors
```

#### ✓ Source Control Sidebar
1. Click **Source Control** icon (left)
2. Should show:
   - Current branch (main)
   - Changes/files
   - GitHub user info

#### ✓ GitHub Extension Active
1. `Ctrl+Shift+P` → `GitHub: Show Status`
2. Should display:
   - Authentication status
   - GitHub user
   - Repository info

#### ✓ Can Push from VSCode
1. Click **Source Control**
2. Make a change to any file
3. Should see **commit** and **sync** buttons
4. Clicking sync should push to GitHub

---

### GitHub Repository

#### ✓ Repository Exists
Go to: `https://github.com/YOUR-USERNAME/warehouse-arch`
Should load without 404 error.

#### ✓ Files Visible
Should show:
- streamlit_app.py
- Dockerfile
- docker-compose.yml
- requirements.txt
- README.md
- deploy.sh
- Makefile
- .github/workflows/deploy.yml

#### ✓ Commits Visible
Click **"N commits"** link
Should show:
- Initial commit
- Your commits
- Proper messages

#### ✓ GitHub Actions Enabled
1. Click **Actions** tab
2. Should show "Local Deployment Pipeline"
3. Click workflow name
4. Should show recent runs

#### ✓ Workflow Runs on Push
1. Make a small change locally
2. Commit: `git commit -am "Test commit"`
3. Push: `git push`
4. Go to Actions tab
5. Should see workflow running (yellow/green indicator)

---

## Troubleshooting Failed Checks

### ❌ "Not a git repository"
```bash
cd /home/vvdn/Documents/warehouse_arch
git init
git add .
git commit -m "Initial commit"
```

### ❌ "No remote origin"
```bash
git remote add origin https://github.com/YOUR-USERNAME/warehouse-arch.git
git push -u origin main
```

### ❌ "GitHub CLI not authenticated"
```bash
gh auth login
# Select HTTPS
# Use Personal Access Token for password
# Or use SSH key
```

### ❌ "VSCode can't find git"
In VSCode:
1. `Ctrl+Shift+P` → `Terminal: Select Default Profile`
2. Choose `bash` or `zsh`
3. Reload window: `Ctrl+Shift+P` → `Developer: Reload Window`

### ❌ "Authentication failed on push"
```bash
# Clear cached credentials
git config --global --unset credential.helper

# Re-authenticate with GitHub CLI
gh auth login

# Or use Personal Access Token:
# When prompted for password, paste your token instead
```

### ❌ "GitHub Actions not showing"
1. Repository → Settings → Actions → General
2. Ensure "Actions permissions" = "Allow all actions"
3. Push a new commit to trigger workflow

---

## Full Verification Script

Run this script to check everything at once:

```bash
#!/bin/bash

echo "=========================================="
echo "GitHub & VSCode Setup Verification"
echo "=========================================="
echo ""

# Git
echo "1. Git Configuration:"
git config --global user.name && echo "   ✓ Name configured" || echo "   ✗ Name missing"
git config --global user.email && echo "   ✓ Email configured" || echo "   ✗ Email missing"
echo ""

# Repository
echo "2. Git Repository:"
test -d .git && echo "   ✓ Repository initialized" || echo "   ✗ Not initialized"
git remote -v | grep origin > /dev/null && echo "   ✓ Remote configured" || echo "   ✗ No remote"
git log --oneline -1 > /dev/null && echo "   ✓ Commits exist" || echo "   ✗ No commits"
echo ""

# GitHub CLI
echo "3. GitHub CLI:"
command -v gh &> /dev/null && echo "   ✓ GitHub CLI installed" || echo "   ✗ Not installed"
gh auth status > /dev/null 2>&1 && echo "   ✓ Authenticated" || echo "   ⚠ Not authenticated"
echo ""

# GitHub Repository
echo "4. GitHub Repository:"
echo "   Go to: https://github.com/YOUR-USERNAME/warehouse-arch"
echo "   Verify files are visible"
echo ""

# VSCode Extensions
echo "5. VSCode Extensions:"
code --list-extensions | grep -i "github" && echo "   ✓ GitHub extension installed" || echo "   ✗ Not installed"
echo ""

# GitHub Actions
echo "6. GitHub Actions Workflow:"
test -f .github/workflows/deploy.yml && echo "   ✓ Workflow file exists" || echo "   ✗ Workflow missing"
echo "   Check: https://github.com/YOUR-USERNAME/warehouse-arch/actions"
echo ""

echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
```

Save as `verify.sh` and run:
```bash
chmod +x verify.sh
./verify.sh
```

---

## Success Indicators

### All Green ✅
- [x] Git configured locally
- [x] Repository initialized and committed
- [x] Code pushed to GitHub
- [x] GitHub CLI authenticated
- [x] VSCode extensions installed
- [x] VSCode authenticated with GitHub
- [x] GitHub Actions workflow visible
- [x] Workflow runs on commits

### Next Steps
1. Make a change locally
2. Commit and push
3. Watch workflow run on GitHub
4. Deploy using CI/CD pipeline

---

## Quick Reference

| Check | Command |
|-------|---------|
| Git version | `git --version` |
| Git config | `git config --global --list` |
| Repository status | `git status` |
| Remote URL | `git remote -v` |
| Commits | `git log --oneline -5` |
| GitHub CLI status | `gh auth status` |
| VSCode extensions | `code --list-extensions` |
| Workflow file | `ls -la .github/workflows/` |

---

## Help & Support

If something's not working:

1. **Read GITHUB_SETUP.md** for detailed instructions
2. **Run setup-github.sh** to reconfigure
3. **Check git status** for current state
4. **Review GitHub Actions logs** for deployment errors
5. **Test manually** with: `make deploy`

You're all set! 🎉
