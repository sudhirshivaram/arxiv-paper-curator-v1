# Git Workflow - Keeping Repos in Sync

## 📊 Current Repository Status

✅ **All repos synced at commit: `ba8dfdc`**

You have 2 GitHub repositories:

1. **sushiva/arxiv-paper-curator-v1** (Primary)
   - 🚀 **Railway deploys from this repo**
   - Remote name: `sushiva`
   - URL: git@github.com:sushiva/arxiv-paper-curator-v1.git

2. **sudhirshivaram/arxiv-paper-curator-v1** (Portfolio/Backup)
   - 📁 Portfolio/showcase repository
   - Remote name: `origin`
   - URL: git@github.com-portfolio:sudhirshivaram/arxiv-paper-curator-v1.git

---

## 🔄 Daily Workflow (Keep Repos Synced)

### Making Changes

**Always push to BOTH repos to keep them synced:**

```bash
# 1. Make your changes
git add .
git commit -m "Your commit message"

# 2. Push to BOTH remotes
git push sushiva main    # ← Railway will deploy from this
git push origin main     # ← Keep portfolio repo synced
```

### One-Command Push (Recommended)

Set up a Git alias to push to both at once:

```bash
# Add this alias
git config alias.push-all '!git push sushiva main && git push origin main'

# Now you can use:
git push-all
```

---

## ✅ Quick Sync Check

Verify all repos are in sync:

```bash
# Check sync status
git fetch --all
git log --oneline -1 main origin/main sushiva/main
```

**Expected output** (all same commit):
```
ba8dfdc (HEAD -> main, sushiva/main, origin/main) Merge branch 'main'...
```

---

## 🚨 If Repos Get Out of Sync

### Scenario 1: Pushed to `origin` but forgot `sushiva`

```bash
# Sushiva is behind
git push sushiva main
```

Railway won't deploy until you push to `sushiva`.

### Scenario 2: Pushed to `sushiva` but forgot `origin`

```bash
# Origin is behind
git push origin main
```

Portfolio repo is outdated but Railway is fine.

### Scenario 3: Both repos diverged (different commits)

```bash
# Fetch all changes
git fetch --all

# Check what's different
git log origin/main..sushiva/main    # Commits in sushiva but not origin
git log sushiva/main..origin/main    # Commits in origin but not sushiva

# Pull and merge from the repo with latest changes
git pull sushiva main --no-rebase    # If sushiva is ahead
# OR
git pull origin main --no-rebase     # If origin is ahead

# Push to both
git push sushiva main
git push origin main
```

---

## 📦 Deploying to Production (Railway)

**Railway only watches the `sushiva` repo!**

To deploy changes:

```bash
# 1. Commit your changes
git add .
git commit -m "Your changes"

# 2. Push to sushiva (triggers Railway deployment)
git push sushiva main

# 3. Keep origin synced
git push origin main
```

**Check deployment:**
- Railway dashboard: https://railway.app/dashboard
- Wait ~2-3 minutes for build & deploy
- Test: https://arxiv-paper-curator-v1-production.up.railway.app/api/v1/docs

---

## 🎯 Best Practices

### ✅ DO:
- Always push to BOTH repos
- Use `git push-all` alias for convenience
- Check sync status before starting work
- Pull from both remotes if working on multiple machines

### ❌ DON'T:
- Push to only one repo (they'll diverge)
- Force push unless you know what you're doing
- Forget which repo Railway watches (it's `sushiva`)

---

## 🔧 Useful Git Commands

```bash
# See all remotes
git remote -v

# See all branches and their tracking
git branch -vv

# Check if repos are synced (should all be same hash)
git rev-parse main origin/main sushiva/main

# See divergence between remotes
git log --oneline --graph --all --decorate

# Fetch latest from all remotes without merging
git fetch --all
```

---

## 📋 Quick Reference Card

| Action | Command |
|--------|---------|
| **Push to both** | `git push sushiva main && git push origin main` |
| **Check sync** | `git log --oneline -1 main origin/main sushiva/main` |
| **Deploy to prod** | `git push sushiva main` (Railway auto-deploys) |
| **Sync if diverged** | `git pull sushiva main && git push origin main` |

---

## 🎓 Current Sync Status (2026-01-13)

✅ **All repos synced at:** `ba8dfdc`

**Includes:**
- ✅ Bug fix: authors field validation (commit `0817e88`)
- ✅ Complete benchmarking framework
- ✅ RAGAS evaluation support
- ✅ Production deployment ready

**Railway Status:**
- Deployment triggered: ✅ Yes
- Repo: sushiva/arxiv-paper-curator-v1
- Branch: main
- Expected live in: ~2-3 minutes

---

## 💡 Pro Tip

Set up your shell prompt to show which repos are ahead/behind:

```bash
# Add to ~/.bashrc or ~/.zshrc for git status in prompt
# Shows if you have unpushed commits
```

Or use tools like:
- `git status -sb` (short status with branch info)
- VSCode Git extension (shows sync status in UI)
- `tig` or `gitk` for visual git history

---

**Remember:** `sushiva` = Production (Railway) | `origin` = Portfolio

Keep them synced! 🔄✨
