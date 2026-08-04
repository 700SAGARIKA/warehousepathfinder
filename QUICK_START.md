# 🚀 Quick Start Guide - Warehouse Path Finder

## Complete Setup in 5 Minutes

### Step 1: Set Up GitHub (2 minutes)
```bash
cd /home/vvdn/Documents/warehouse_arch
chmod +x setup-github.sh
./setup-github.sh
```

The script will guide you through:
- ✅ Configuring Git with your name/email
- ✅ Creating GitHub repository
- ✅ Pushing code to GitHub
- ✅ Authenticating GitHub CLI
- ✅ Setting up VSCode extensions

### Step 2: Deploy Locally (2 minutes)
```bash
# Option A: Using Make (simplest)
make deploy

# Option B: Using Docker Compose
docker-compose up -d

# Option C: Using bash script
./deploy.sh
```

App available at: **http://localhost:8010**

### Step 3: Verify Everything Works (1 minute)
```bash
# Check Git
git status

# Check VSCode extension
# In VSCode: Ctrl+Shift+X → Search "GitHub Pull Requests and Issues"

# Check GitHub
# Open: https://github.com/YOUR-USERNAME/warehouse-arch

# Check deployment
curl http://localhost:8010
```

---

## 📋 What You Now Have

### Local Deployment Pipeline ✅
- `docker-compose.yml` - Container orchestration
- `Makefile` - Simple commands (make deploy, make logs, etc)
- `deploy.sh` - Automated deployment script
- Dockerfile - Container configuration

### GitHub & CI/CD ✅
- `.github/workflows/deploy.yml` - GitHub Actions pipeline
- `setup-github.sh` - Automated GitHub setup
- `GITHUB_SETUP.md` - Detailed authentication guide
- `VERIFY_SETUP.md` - Verification checklist

### Documentation ✅
- `README.md` - Project overview
- `DEPLOYMENT.md` - 300+ line comprehensive guide
- `QUICK_START.md` - This file!

---

## 🔗 How GitHub is Linked with VSCode

### 1. **Git Configuration** (Local)
```bash
git config --global user.name "Your Name"
git config --global user.email "connectsid17@gmail.com"
```
✅ Your identity is set locally

### 2. **Authentication** (GitHub)
- Personal Access Token OR
- GitHub CLI (`gh auth login`) OR
- SSH key
✅ VSCode can access your GitHub account

### 3. **VSCode Extension** (IDE)
- "GitHub Pull Requests and Issues" extension
- VSCode's built-in Source Control
✅ VSCode shows GitHub integration

### 4. **Repository Link** (Git)
```bash
git remote add origin https://github.com/YOUR-USERNAME/warehouse-arch.git
```
✅ Local repo connected to GitHub

### 5. **CI/CD Pipeline** (Automation)
- `.github/workflows/deploy.yml`
- Runs automatically on push
✅ Code changes trigger deployments

---

## ✨ After Setup: Day-to-Day Workflow

### Make Changes
```bash
# Edit files in VSCode
# Files show in Source Control panel
```

### Commit & Push (from VSCode terminal)
```bash
git add .
git commit -m "Feature: Add new functionality"
git push
```

### Watch Pipeline
1. Go to GitHub → Actions tab
2. See workflow running automatically
3. Watch deployment happen

### View Application
```bash
# Local
curl http://localhost:8010

# Or open browser
# http://localhost:8010
```

---

## 🔍 Verify Setup

### Quick Checks
```bash
# Is Git configured?
git config --global user.name

# Is repository linked?
git remote -v

# Is GitHub CLI authenticated?
gh auth status

# Is code on GitHub?
# Visit: https://github.com/YOUR-USERNAME/warehouse-arch

# Is workflow running?
# Visit: https://github.com/YOUR-USERNAME/warehouse-arch/actions
```

Full verification: `cat VERIFY_SETUP.md`

---

## 🛠️ All Available Commands

### Deployment
```bash
make deploy      # Full deployment (build + start)
make build       # Build Docker image only
make run         # Start with Docker Compose
./deploy.sh      # Automated deployment pipeline
```

### Management
```bash
make logs        # View container logs
make status      # Show container status
make stop        # Stop containers
make shell       # Access container shell
make clean       # Remove everything
```

### Git
```bash
git status       # Check changes
git log          # View commits
git push         # Push to GitHub
git pull         # Pull from GitHub
```

### GitHub
```bash
gh auth status   # Check authentication
gh repo view     # View repository info
gh issue list    # List issues
gh pr list       # List pull requests
```

---

## 📁 File Structure

```
warehouse_arch/
│
├── 📱 Application
│   ├── streamlit_app.py       # Main app
│   └── requirements.txt       # Dependencies
│
├── 🐳 Docker & Deployment
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── Makefile
│   └── deploy.sh
│
├── 🔗 GitHub & Git
│   ├── .github/
│   │   └── workflows/
│   │       └── deploy.yml    # CI/CD pipeline
│   ├── .git/                 # Local repository
│   ├── .gitignore
│   └── setup-github.sh       # GitHub setup automation
│
└── 📚 Documentation
    ├── README.md             # Overview
    ├── DEPLOYMENT.md         # Detailed guide (300+ lines)
    ├── GITHUB_SETUP.md       # GitHub & VSCode guide
    ├── VERIFY_SETUP.md       # Verification checklist
    └── QUICK_START.md        # This file!
```

---

## 🎯 Connection Diagram

```
┌─────────────────┐
│   Your Machine  │
│                 │
│  ┌───────────┐  │
│  │ VSCode    │  │  ← Edit files here
│  │ (IDE)     │  │  ← See GitHub integration
│  └───────────┘  │
│        ↓        │
│  ┌───────────┐  │
│  │ Git       │  │  ← git add/commit/push
│  │ (Local)   │  │  ← Linked to GitHub
│  └───────────┘  │
│        ↓        │
│  ┌───────────┐  │
│  │ Docker    │  │  ← docker-compose up
│  │ (Containers)  │  ← App runs here
│  └───────────┘  │
│                 │
└─────────────────┘
         ↓
    (Internet)
         ↓
    ┌─────────────┐
    │   GitHub    │
    │             │
    │ Remote Repo │  ← Your code lives here
    │ + Actions   │  ← CI/CD pipeline runs
    └─────────────┘
```

---

## ⚡ One-Command Setup

### Complete Setup (All at once)
```bash
\
./setup-github.sh && \
make deploy && \
echo "✓ Setup complete! Visit http://localhost:8010"
```

---

## 🆘 Troubleshooting

### "Permission denied: setup-github.sh"
```bash
chmod +x setup-github.sh
./setup-github.sh
```

### "docker-compose: command not found"
```bash
sudo apt-get install docker-compose
# Or use: docker compose up -d
```

### "fatal: not a git repository"
```bash
git init
git add .
git commit -m "Initial commit"
```

### "Authentication failed"
```bash
gh auth login
# Paste your Personal Access Token when prompted
```

### "Port 8010 already in use"
```bash
lsof -i :8010  # Find process
kill -9 <PID>  # Kill process
make deploy    # Try again
```

More help: See `GITHUB_SETUP.md` Part 8 or `DEPLOYMENT.md` Section 7

---

## ✅ Success Checklist

- [ ] Run `./setup-github.sh` (GitHub setup)
- [ ] Run `make deploy` (Local deployment)
- [ ] Visit `http://localhost:8010` (App working)
- [ ] Check GitHub repo exists
- [ ] Check GitHub Actions tab
- [ ] Install VSCode extensions
- [ ] Verify git status: `git status`
- [ ] Make a test commit and push

When ALL boxes are checked ✅ → **You're ready to go!** 🚀

---

## 📖 Documentation Map

Need help? Choose your topic:

| Topic | File |
|-------|------|
| Overview | README.md |
| Deployment methods | DEPLOYMENT.md |
| GitHub & VSCode setup | GITHUB_SETUP.md |
| Verify everything works | VERIFY_SETUP.md |
| Quick start | QUICK_START.md (you are here!) |

---

## 🎓 Next Steps

After setup:

1. **Make code changes** in VSCode
2. **Commit & push** using Git
3. **Watch workflow run** on GitHub Actions
4. **Monitor deployment** in logs
5. **Access application** at http://localhost:8010
6. **Scale to cloud** when ready (see DEPLOYMENT.md Section 8)

---

## 🤝 Getting Help

```bash
# Re-run GitHub setup
./setup-github.sh

# View comprehensive deployment guide
cat DEPLOYMENT.md

# Verify everything is linked
cat VERIFY_SETUP.md

# Check current status
git status
git remote -v
gh auth status
docker-compose ps
```

---

## Summary

You now have:
✅ **GitHub account linked** with authentication  
✅ **VSCode IDE integration** ready to use  
✅ **Local deployment pipeline** automated  
✅ **CI/CD workflow** configured  
✅ **Docker containerization** set up  
✅ **Comprehensive documentation** available  

**Everything is connected and ready!** 🎉

Start with: `./setup-github.sh && make deploy`

Questions? Check the relevant documentation file above.

Happy coding! 🚀
