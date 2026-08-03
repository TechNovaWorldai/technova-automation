# TechNova World — Complete Deployment Guide v4.0

This guide walks you through every step required to push TechNova World Automation to GitHub, secure your secrets, and activate fully-automated 24/7 LinkedIn posting — all for free.

---

## ⚡ What "24/7 Automation" Actually Means

There is **no always-on server** running (that's not available on a free tier). Instead, GitHub Actions cron jobs wake up at the exact scheduled time, run the relevant script, and shut down — whether your laptop is on or off.

- **LinkedIn post (Mon–Fri, 9 PM IST)** → `post-linkedin.yml` wakes up, posts, exits
- **Weekly content batch (Sunday, 8 PM IST)** → `weekly-batch.yml` generates 5 days of content, exits
- **GitHub Actions runs on GitHub's infrastructure** — 2,000 free minutes/month, well above the ~15 min/week this app uses

---

## Part 1 — Push to GitHub

### Step 1 — Create a New Repository

1. Go to [github.com](https://github.com) → **"New repository"**
2. Name it `technova-automation` (or any name you prefer)
3. Set visibility to **Private** (recommended — keeps your business logic private)
4. Click **"Create repository"**

### Step 2 — Push Your Local Code

```bash
cd path/to/technova-world-automation
git init
git add .
git commit -m "Initial commit — TechNova World Automation v4.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/technova-automation.git
git push -u origin main
```

> 💡 Prefer a GUI? Use **GitHub Desktop** — "Add Local Repository" → select the folder → "Publish Repository"

### Step 3 — Verify No Secrets Were Committed

```bash
git log --all --full-history -- .env
```

This should return **nothing**. If it returns any output, delete the `.env` file, commit again, and **immediately regenerate every API key you have** — the old ones are compromised.

---

## Part 2 — Setting Up GitHub Secrets (Critical)

API keys must **never** appear in source code. GitHub provides an encrypted Secrets vault that only your Actions workflows can access.

1. Go to your repository → **Settings** tab
2. Left sidebar: **Secrets and variables** → **Actions**
3. Click **"New repository secret"** and create each of the following:

| Secret Name | Where to get the value |
|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → Get API Key |
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) → Sign up free → Keys *(optional but recommended)* |
| `LINKEDIN_ACCESS_TOKEN` | [developer.linkedin.com/tools/oauth](https://developer.linkedin.com/tools/oauth) |
| `LINKEDIN_ORGANIZATION_ID` | Your LinkedIn Company Page URL — the numeric ID in the URL |

For each: enter the **exact name** from the table above (case-sensitive) → paste the value → click **"Add secret"**.

> 🔒 These values are encrypted at rest and only ever visible to your Actions workflows. They never appear in logs.

---

## Part 3 — Activating GitHub Actions Workflows

Your repository already contains three workflow files in `.github/workflows/`:

| Workflow File | What it does | When it runs |
|---|---|---|
| `run-tests.yml` | Runs all 104 automated tests | On every `git push` |
| `weekly-batch.yml` | Generates 5 days of content, queues LinkedIn posts | Every Sunday, 8 PM IST |
| `post-linkedin.yml` | Posts the next item from the queue to LinkedIn | Mon–Fri, 9 PM IST |

**No action required to activate these** — GitHub detects the workflow files automatically when you push.

### Verify They're Running

1. Go to your repository → **Actions** tab
2. You'll see all three workflows listed
3. To test a workflow manually before the scheduled time: click the workflow → **"Run workflow"** → **"Run workflow"** (confirm)
4. Results appear within 1–2 minutes (green ✅ = success, red ❌ = failure)

### Diagnosing a Failed Run (❌)

1. Click the failed run → click the failed step to expand the logs
2. Common causes:

| Symptom in logs | Cause | Fix |
|---|---|---|
| `LINKEDIN_ACCESS_TOKEN not set` | Secret name misspelled (case-sensitive) | Check exact spelling in Settings → Secrets |
| `401 Unauthorized` | LinkedIn token expired | [Regenerate the token](https://developer.linkedin.com/tools/oauth) → update the Secret |
| `429 rate limit` | Gemini free tier hit | App automatically retries with OpenRouter — usually resolves itself |
| `No items in queue` | `weekly-batch.yml` hasn't run yet | Manually trigger `weekly-batch.yml` first, then retry `post-linkedin.yml` |

---

## Part 4 — Web Dashboard on Render.com (Optional)

GitHub Actions handles all scheduled tasks — a web dashboard is only needed if you want a browser UI for manual generation, queue management, and real-time monitoring.

### Setup (~10 minutes)

1. Create a free account at [render.com](https://render.com) (sign in with GitHub)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository (grant Render permission to read it)
4. Render automatically detects `render.yaml` and creates three services:

| Service | Type | Purpose |
|---|---|---|
| `technova-dashboard` | Web Service | Browser dashboard — live URL |
| `technova-linkedin-poster` | Cron Job | Mon–Fri 9:30 PM IST auto-post |
| `technova-weekly-batch` | Cron Job | Sunday 8:30 PM IST content batch |

5. For each service, go to the **Environment** tab and add your secrets:
   - `GEMINI_API_KEY`
   - `OPENROUTER_API_KEY` *(optional)*
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_ORGANIZATION_ID`
   - `FLASK_SECRET_KEY` — Render auto-generates this (`generateValue: true` is already set in `render.yaml`)
6. Click **"Apply"** — the build takes 2–3 minutes
7. Click the `technova-dashboard` service → copy the **live URL** at the top (e.g. `https://technova-dashboard.onrender.com`)

### Free Tier Behaviour — Cold Start

Render's free web service **sleeps after 15 minutes of inactivity**. The first request after it sleeps takes 30–50 seconds to respond (server wake-up). Subsequent requests are fast.

> ✅ **This does not affect scheduled posting.** The cron jobs (`technova-linkedin-poster`, `technova-weekly-batch`) are separate services — Render wakes them independently at their scheduled times.

### GitHub Actions vs Render Cron — Choose One

Both platforms can handle scheduled posting. Running both simultaneously will cause **duplicate posts**. Pick one:

- **GitHub Actions** — simpler to manage, no extra platform
- **Render Cron** — useful if you also want the dashboard on the same platform

---

## Part 5 — Running Tests Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your GEMINI_API_KEY at minimum
python tests/run_tests.py
```

Expected result: **104/104 tests passed (100%)**

On Windows, if you see Unicode/emoji encoding errors in the console output, run:
```bash
$env:PYTHONIOENCODING="utf-8"; python tests/run_tests.py
```

### Automatic Testing on GitHub

Every `git push` triggers `run-tests.yml` automatically. Results appear in the **Actions** tab. GitHub sends an email if any test fails.

---

## Part 6 — LinkedIn Token Renewal (Every 60 Days)

LinkedIn access tokens expire after 60 days. When this happens, all automated posts will fail with a `401 Unauthorized` error.

### How to Renew

1. Go to [developer.linkedin.com/tools/oauth](https://developer.linkedin.com/tools/oauth)
2. Select your app → select the same scopes as before → **"Request access token"**
3. Complete the OAuth consent flow
4. Copy the new Access Token
5. Go to your GitHub repo → **Settings → Secrets → Actions → `LINKEDIN_ACCESS_TOKEN`** → **"Update"** → paste the new token → **"Save"**

> 💡 **Set a recurring calendar reminder every 55 days** to renew the token before it expires and automation is interrupted.

---

## Pre-Deployment Checklist

Before going live, verify each of these:

- [ ] `.env` is listed in `.gitignore` *(already configured)*
- [ ] `git log --all -- .env` returns nothing
- [ ] GitHub repository is set to **Private**
- [ ] All 4 secrets added to GitHub (Gemini + OpenRouter + LinkedIn token + Org ID)
- [ ] `run-tests.yml` shows a green ✅ in the Actions tab
- [ ] Manually triggered `weekly-batch.yml` completed successfully
- [ ] Manually triggered `post-linkedin.yml` posted to LinkedIn
- [ ] LinkedIn token expiry date noted (60 days from generation)
- [ ] Render `technova-dashboard` deployed and the live URL loads *(if using dashboard)*
- [ ] Render Environment tab secrets added *(if using Render)*

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---|---|
| "Secret not found" in logs | Check secret name spelling — names are **case-sensitive** |
| LinkedIn `401 Unauthorized` | Token expired — [regenerate it](https://developer.linkedin.com/tools/oauth) |
| LinkedIn `403 Permission denied` | Missing OAuth scope — ensure `w_member_social` and `r_liteprofile` are enabled on your LinkedIn App |
| LinkedIn `No posting target` | Set `LINKEDIN_ORGANIZATION_ID` **or** `LINKEDIN_PERSON_URN` in Secrets |
| Gemini `429 rate limit` | App retries with OpenRouter automatically — wait and it will resolve |
| Workflow not triggering on schedule | Repo Settings → Actions → General → verify "Allow all actions and reusable workflows" is enabled |
| Queue empty, nothing posted | Trigger `weekly-batch.yml` first to populate the queue |
| Dashboard slow on first load | Expected — free tier cold start takes 30–50 seconds. Subsequent requests are fast. |
| Dashboard "Application Error" | Check Render → Logs tab — usually a missing environment variable or build failure |

---

## Diagnostic Commands

Run these locally to verify your setup before deploying:

```bash
# Check all environment variables
python -c "from utils import validate_config; import json; print(json.dumps(validate_config(), indent=2))"

# LinkedIn full diagnostic
python -c "from linkedin_poster import diagnose_linkedin; diagnose_linkedin()"

# Test AI connection (requires GEMINI_API_KEY)
python -c "from ai_client import which_model_answered; print(which_model_answered('Say OK'))"

# Run only deployment-related tests
python tests/run_tests.py --suite deploy
```

---

## Cost Summary

| Service | Free Tier Limit | This App's Usage |
|---|---|---|
| Gemini 2.5 API | ~1,500 requests/day | ~40 requests/week ✅ |
| OpenRouter (fallback) | Rate-limited free models | Used only if Gemini fails ✅ |
| GitHub Actions | 2,000 min/month | ~15 min/week ✅ |
| GitHub Private Repo | Unlimited | ✅ |
| Render Web Service | Free (sleeps when idle) | Dashboard only ✅ |
| Render Cron Jobs | Free tier | Scheduled posting ✅ |

**Monthly cost: ₹0**

---

*TechNova World Automation v4.0 — Deployment Guide*
