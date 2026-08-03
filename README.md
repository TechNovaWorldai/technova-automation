<div align="center">

<!-- Hero Banner SVG -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 200" width="900" height="200">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f0c29"/>
      <stop offset="50%" style="stop-color:#302b63"/>
      <stop offset="100%" style="stop-color:#24243e"/>
    </linearGradient>
    <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#a78bfa"/>
      <stop offset="50%" style="stop-color:#60a5fa"/>
      <stop offset="100%" style="stop-color:#34d399"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <!-- Background -->
  <rect width="900" height="200" fill="url(#bg)" rx="16"/>
  <!-- Decorative circles -->
  <circle cx="820" cy="40" r="60" fill="#a78bfa" opacity="0.08"/>
  <circle cx="80"  cy="160" r="80" fill="#60a5fa" opacity="0.06"/>
  <circle cx="450" cy="180" r="40" fill="#34d399" opacity="0.05"/>
  <!-- Decorative lines -->
  <line x1="0" y1="190" x2="900" y2="190" stroke="#a78bfa" stroke-width="1" opacity="0.2"/>
  <!-- Icon -->
  <text x="60" y="115" font-family="monospace" font-size="52" fill="url(#textGrad)" filter="url(#glow)">🌐</text>
  <!-- Title -->
  <text x="140" y="95" font-family="'Segoe UI', Arial, sans-serif" font-weight="900" font-size="38"
        fill="url(#textGrad)" filter="url(#glow)">TechNova World</text>
  <!-- Subtitle -->
  <text x="142" y="130" font-family="'Segoe UI', Arial, sans-serif" font-size="17" fill="#94a3b8">
    AI-Powered Social Media Automation • Algorithm-Aware • 100% Free Tier
  </text>
  <!-- Version badge -->
  <rect x="142" y="145" width="72" height="22" rx="11" fill="#a78bfa" opacity="0.25"/>
  <text x="178" y="160" font-family="monospace" font-size="11" fill="#a78bfa" text-anchor="middle">v 4.0</text>
  <!-- Test badge -->
  <rect x="224" y="145" width="110" height="22" rx="11" fill="#34d399" opacity="0.2"/>
  <text x="279" y="160" font-family="monospace" font-size="11" fill="#34d399" text-anchor="middle">104 tests ✓</text>
  <!-- Free badge -->
  <rect x="344" y="145" width="80" height="22" rx="11" fill="#60a5fa" opacity="0.2"/>
  <text x="384" y="160" font-family="monospace" font-size="11" fill="#60a5fa" text-anchor="middle">₹0 / month</text>
</svg>

<br/>

<!-- Badges -->
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-104%2F104%20Passing-22c55e?style=for-the-badge&logo=pytest&logoColor=white)](tests/run_tests.py)
[![LinkedIn API](https://img.shields.io/badge/LinkedIn-Auto--Post-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://developer.linkedin.com)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.5%20Flash%2FPro-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-24%2F7-181717?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Free Tier](https://img.shields.io/badge/Cost-₹0%2FMonth-f59e0b?style=for-the-badge&logo=cashapp&logoColor=white)](#-cost-breakdown)

</div>

---

## 📖 What Is This?

**TechNova World Automation** is a production-ready, fully-tested social media automation system that generates, scores, and publishes algorithm-optimised content to **LinkedIn** — automatically, every weekday, at the optimal posting time, for free.

It is **not** a generic scheduler. Every piece of content is:

- 🧠 **Algorithm-aware** — generation prompts embed the real 2024–2025 LinkedIn/Twitter/Medium ranking rules
- 📊 **Auto-scored** — each post scores 0–100 against 25+ quality checks before being queued
- 🎙️ **Brand-voiced** — a configurable brand voice engine strips generic AI phrasing
- 🔄 **Self-improving** — posts that score below 65 are automatically rewritten, up to 3 times
- 🛡️ **Spam-guarded** — 30+ spam patterns caught before any post goes live

---

## ✨ Features

| Category | What it does |
|---|---|
| 🤖 **AI Generation** | LinkedIn posts, Twitter threads, Medium articles via Gemini 2.5 Flash/Pro |
| 🔁 **Fallback Chain** | Gemini Flash → Gemini Pro → OpenRouter (Llama/DeepSeek) — one provider outage can't break the pipeline |
| 📐 **Algorithm Engine** | 25+ scoring rules per platform based on LinkedIn/Twitter/Medium engineering research |
| 🎙️ **Brand Voice** | Configurable tone, banned phrases, signature style — stored in `assets/brand_voice.json` |
| 🔬 **Deep Research Mode** | 4-step pipeline: research outline → gather specifics → draft → self-critique |
| 📰 **News-Aware Content** | RSS-fed real-time AI news injected into posts for relevance |
| 🖼️ **Image Watermarking** | Automated image branding via Pillow |
| 📄 **PDF Carousel** | LinkedIn carousel slides generated as PDFs via ReportLab |
| 🎬 **Video Scripts** | YouTube Shorts / Instagram Reels script generator |
| 📋 **Post Queue** | JSON-backed queue — generate once on Sunday, auto-post Mon–Fri |
| 🖥️ **Web Dashboard** | Flask dashboard with queue management, live generation, CSV export |
| 📦 **Buffer CSV Export** | Export queued posts as CSV for Buffer / Hootsuite |
| 🧪 **104 Automated Tests** | 11 test suites covering unit, integration, load, quality, and deployment |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB REPOSITORY                            │
│                                                                 │
│  ┌─────────────────────┐    ┌───────────────────────────────┐   │
│  │   Sunday 8 PM IST   │    │    Mon–Fri 9 PM IST           │   │
│  │  weekly-batch.yml   │───▶│   post-linkedin.yml           │   │
│  │                     │    │                               │   │
│  │  5 topics ──────────│    │  Queue → Score → Post         │   │
│  │    └─ LinkedIn post │    │    └─ LinkedIn API v2         │   │
│  │    └─ Twitter posts │    │    └─ Company / Personal URN  │   │
│  │    └─ Medium draft  │    └───────────────────────────────┘   │
│  └─────────────────────┘                                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  On every `git push` → run-tests.yml (104 tests)         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
 ┌─────────────────┐               ┌──────────────────────┐
 │  Gemini 2.5     │  ──fails──▶  │  OpenRouter          │
 │  Flash / Pro    │               │  Llama / DeepSeek    │
 │  (primary AI)   │               │  (free fallback)     │
 └─────────────────┘               └──────────────────────┘
```

### The 3 Intelligence Layers

<details>
<summary><strong>Layer 1 — WHEN to post (Timing Intelligence)</strong></summary>

Posting times are research-based, not random:

```
LinkedIn  → Mon–Fri, 9:00 PM IST   (professionals check phones after dinner)
Medium    → Tue + Thu, 6:00 PM IST (Medium distribution peaks early evening)
Twitter   → 9 AM, 12 PM, 3 PM, 6 PM, 11 PM IST (5 slots, replies-maximising)
```

These are **fixed by research** in `algo_engine.py` → `LINKEDIN_ALGO["content_rules"]["post_timing_ist"]`. Timing patterns evolve over months, not days.

</details>

<details>
<summary><strong>Layer 2 — WHAT to post (Content Intelligence)</strong></summary>

Three-step pipeline per post:

1. **Topic selection** — `get_trending_topics()` fetches current AI trends from RSS feeds, or you supply topics directly
2. **Algorithm-aware generation** — `build_linkedin_prompt()` injects exact 2024/2025 platform rules into every prompt: hook length, hashtag count, line spacing, link placement, optimal word count
3. **Quality scoring + auto-improve** — every post gets a 0–100 score via `score_linkedin_post()`. Below 65 → automatic rewrite (up to 3 attempts)

</details>

<details>
<summary><strong>Layer 3 — IS IT GOOD ENOUGH (Safety Intelligence)</strong></summary>

Three gates before any post is published:

| Check | Tool | What it catches |
|---|---|---|
| Spam guard | `check_spam()` | 30+ spam phrases, fake engagement, excessive caps, emoji spam |
| Value check | `check_value()` | Filler content, vague claims without supporting data |
| Brand voice | `check_voice_compliance()` | Banned phrases ("game-changer", "revolutionize"), missing specifics |

A post that fails any check is marked `"failed"` in the queue and **never published**.

</details>

---

## 📁 Project Structure

```
technova-world-automation/
│
├── .github/workflows/
│   ├── run-tests.yml          # Auto-runs 104 tests on every push
│   ├── weekly-batch.yml       # Sunday: generates 5 days of content
│   └── post-linkedin.yml      # Mon–Fri: posts from queue to LinkedIn
│
├── automation/
│   ├── post_scheduled.py      # Non-interactive single-post runner (for cron)
│   └── weekly_batch.py        # Non-interactive batch generator (for cron)
│
├── tests/
│   └── run_tests.py           # 104 tests across 11 suites
│
├── ai_client.py               # Unified AI entry point: Gemini → OpenRouter fallback
├── ai_generator.py            # Algorithm-aware content generation for all platforms
├── algo_engine.py             # Platform algorithm rules + 0–100 quality scorer
├── brand_voice.py             # Brand voice config, compliance checker, rewriter
├── deep_research.py           # 4-step senior-writer-style pipeline
├── linkedin_poster.py         # LinkedIn API v2 posting (company + personal fallback)
├── search_agent.py            # Real-time AI news via RSS feeds
├── watermark.py               # Image watermarking (Pillow)
├── pdf_carousel.py            # LinkedIn carousel PDF generator (ReportLab)
├── video_script.py            # YouTube Shorts / Reels script generator
├── utils.py                   # Logging, retry decorator, Result wrapper, QueueManager
├── config.py                  # Reads ALL secrets from environment variables (git-safe)
├── run.py                     # Interactive local menu (17 options)
├── webapp.py                  # Flask web dashboard
│
├── assets/
│   └── brand_voice.json       # Your brand voice config (auto-created on first run)
├── queue/
│   └── posts_queue.json       # Post queue (auto-created)
├── generated/                 # Generated content files (gitignored)
│
├── render.yaml                # Render.com deployment blueprint
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Protects .env and secrets
├── DEPLOYMENT.md              # Full step-by-step deployment guide
└── README.md                  # This file
```

---

## ⚡ Quick Start (Local Development)

### Prerequisites

- Python 3.10 or higher
- A free [Google AI Studio](https://aistudio.google.com) account (for Gemini API key)
- A [LinkedIn Developer App](https://developer.linkedin.com) (for posting)

### Step 1 — Clone & Install

```bash
git clone https://github.com/TechNovaWorldai/technova-automation.git
cd technova-automation
pip install -r requirements.txt
```

### Step 2 — Configure Environment

```bash
cp .env.example .env
```

Open `.env` and fill in your keys (see **Getting API Keys** below):

```env
GEMINI_API_KEY=your_key_here
LINKEDIN_ACCESS_TOKEN=your_token_here
LINKEDIN_ORGANIZATION_ID=your_org_id   # optional — personal profile works too
```

### Step 3 — Verify Everything Works

```bash
# Run all 104 tests
python tests/run_tests.py

# Expected: 104/104 passed (100%)
```

### Step 4 — Launch the Interactive Menu

```bash
python run.py
```

You'll see a 17-option menu covering generation, posting, queue management, dashboard launch, and more.

### Step 5 — Or Use the Web Dashboard

```bash
python webapp.py
# Open: http://localhost:5000
```

---

## 🔑 Getting API Keys

### Gemini API Key (Required — Free)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with any Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy the key → paste into `GEMINI_API_KEY` in your `.env`

> **Free quota:** ~1,500 requests/day (well above weekly automation needs of ~40 requests)

---

### OpenRouter API Key (Optional — Free Fallback)

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up for a free account
3. Go to **Keys** → **Create Key**
4. Copy the key → paste into `OPENROUTER_API_KEY` in your `.env`

> Used automatically if Gemini is rate-limited or down. Provides access to Llama 3.3 70B, DeepSeek, and other free models.

---

### LinkedIn Access Token (Required for Posting)

This is the most involved step. Follow carefully:

**Step 1 — Create a LinkedIn App**
1. Go to [developer.linkedin.com/apps](https://developer.linkedin.com/apps)
2. Click **"Create App"**
3. Fill in: App Name, LinkedIn Page (your company page URL), Logo, Business email
4. Accept the Legal Agreement → **"Create App"**

**Step 2 — Configure OAuth Scopes**
1. Go to your app → **"Auth"** tab → **"OAuth 2.0 scopes"**
2. Request access to these scopes:
   - ✅ `r_liteprofile` — read your profile (needed for URN auto-fetch)
   - ✅ `w_member_social` — post as yourself (personal posts)
   - ✅ `rw_organization_social` — post as company page *(requires LinkedIn review)*

**Step 3 — Generate an Access Token**
1. Go to [developer.linkedin.com/tools/oauth](https://developer.linkedin.com/tools/oauth)
2. Select your app → select the scopes above → click **"Request access token"**
3. Complete the OAuth flow
4. Copy the **Access Token** → paste into `LINKEDIN_ACCESS_TOKEN` in your `.env`

> ⚠️ **Tokens expire every 60 days.** Set a calendar reminder to refresh it.

**Step 4 — Get Your Organization ID (for company page posting)**
1. Go to your LinkedIn Company Page
2. The URL looks like: `linkedin.com/company/12345678/`
3. The number (`12345678`) is your `LINKEDIN_ORGANIZATION_ID`

**Step 5 — Diagnose Your Setup**

```bash
python -c "from linkedin_poster import diagnose_linkedin; diagnose_linkedin()"
```

This prints a full diagnostic report showing what's set, what's missing, and exactly how to fix any issues.

---

## 🧪 Running Tests

```bash
# Run all 104 tests
python tests/run_tests.py

# Run a specific suite only
python tests/run_tests.py --suite unit
python tests/run_tests.py --suite algo
python tests/run_tests.py --suite ai_client
python tests/run_tests.py --suite webapp

# Skip slow load tests
python tests/run_tests.py --fast
```

### Test Suites

| Suite | Tests | What it covers |
|---|---|---|
| `unit` | 8 | Core utils, Result, QueueManager, retry |
| `algo` | 17 | LinkedIn/Twitter/Medium scoring rules |
| `api` | 11 | API mocking for Gemini and LinkedIn |
| `watermark` | 6 | Image watermarking (Pillow) |
| `load` | 7 | Scorer throughput, queue capacity |
| `quality` | 6 | End-to-end content quality pipeline |
| `voice` | 7 | Brand voice compliance + rewriter |
| `deploy` | 7 | Env var safety, gitignore, automation scripts |
| `ai_client` | 8 | Model fallback chain (Flash → Pro → OpenRouter) |
| `research` | 8 | Source citation accuracy, RSS integration |
| `webapp` | 19 | Flask routes, batch lifecycle, CSV export |

---

## ☁️ Deployment (24/7 Automation)

See **[`DEPLOYMENT.md`](DEPLOYMENT.md)** for the complete step-by-step walkthrough covering:
- Pushing to GitHub and securing secrets
- Activating the 3 GitHub Actions workflows
- Setting up a Render.com web dashboard
- LinkedIn token renewal process
- Troubleshooting checklist

### Quick Summary

| Platform | Purpose | Cost |
|---|---|---|
| **GitHub** (private repo) | Code hosting + secret storage | Free |
| **GitHub Actions** | Scheduled batch + auto-post + CI tests | Free (2,000 min/month) |
| **Render.com** | Web dashboard (optional) | Free tier |

**Total: ₹0/month**

---

## 🔧 LinkedIn Troubleshooting

This is the most common point of failure. Run the built-in diagnostic first:

```bash
python -c "from linkedin_poster import diagnose_linkedin; diagnose_linkedin()"
```

| Error | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | Token expired | [Regenerate token](https://developer.linkedin.com/tools/oauth) → update Secret |
| `403 Permission denied` | Missing OAuth scope | Add `w_member_social` / `r_liteprofile` to your LinkedIn App scopes |
| `No posting target` | Both Org ID and Person URN missing | Set `LINKEDIN_ORGANIZATION_ID` **or** `LINKEDIN_PERSON_URN` in Secrets |
| `Could not auto-fetch URN` | `r_liteprofile` scope missing | Add `r_liteprofile` scope and regenerate token |
| Company page 403 | `rw_organization_social` not approved | Post falls back to personal profile automatically |
| Timeout | LinkedIn API slow | Retry decorator handles this automatically (3 attempts, exponential backoff) |

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Setting Up a Development Environment

```bash
git clone https://github.com/TechNovaWorldai/technova-automation.git
cd technova-automation
pip install -r requirements.txt
cp .env.example .env
# Fill in your GEMINI_API_KEY at minimum
python tests/run_tests.py   # Must show 104/104 before you start
```

### Branch & Commit Conventions

```bash
# Create a feature branch
git checkout -b feat/your-feature-name

# Commit message format:
git commit -m "feat: add Instagram Reels script generator"
git commit -m "fix: linkedin 403 fallback not triggering"
git commit -m "docs: update contribution guide"
git commit -m "test: add watermark edge case tests"
```

**Prefixes:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

### Adding a New Content Platform

1. Add platform rules to [`algo_engine.py`](algo_engine.py) — follow the `LINKEDIN_ALGO` dict pattern
2. Add a `score_<platform>_post()` function in `algo_engine.py`
3. Add a `build_<platform>_prompt()` function in `algo_engine.py`
4. Add a `generate_<platform>_post()` function in [`ai_generator.py`](ai_generator.py)
5. Add tests in [`tests/run_tests.py`](tests/run_tests.py) — at minimum: scoring, spam check, prompt build
6. Update the file structure table in this README

### Adding a New AI Provider

1. Add the API call function in [`ai_client.py`](ai_client.py) — follow the `_call_openrouter_model()` pattern
2. Add it to the fallback chain in `generate()`
3. Add a test in the `ai_client` suite in [`tests/run_tests.py`](tests/run_tests.py)

### Code Standards

- All functions and classes must have English docstrings (Args + Returns for public API)
- No hardcoded API keys, URLs, or secrets — everything via `config.py`
- New features need at least 3 tests
- Run `python tests/run_tests.py` — 104/104 must pass before opening a PR

### Opening a Pull Request

1. Fork the repository
2. Create your feature branch
3. Make your changes + add tests
4. Verify all 104 tests still pass
5. Open a PR with a clear description of what you changed and why

---

## 🗺️ Roadmap & Improvement Suggestions

These are known improvements worth contributing:

| Priority | Feature | Complexity |
|---|---|---|
| 🔴 High | **LinkedIn token auto-refresh** — OAuth refresh token flow so token never expires manually | Medium |
| 🔴 High | **Twitter/X posting** — Basic tweet/thread posting via API v2 (when free tier is available) | Medium |
| 🟡 Medium | **Instagram caption generator** — Adapt LinkedIn algo rules for Instagram | Low |
| 🟡 Medium | **Analytics ingestion** — Pull LinkedIn post impressions/engagement back into the system | High |
| 🟡 Medium | **Content calendar UI** — Visual week-view in the web dashboard | Medium |
| 🟢 Low | **Notion integration** — Save generated drafts directly to a Notion database | Low |
| 🟢 Low | **Slack notifications** — Post a summary of what was generated/posted to a Slack channel | Low |
| 🟢 Low | **Token expiry reminder** — Email/Slack alert 7 days before LinkedIn token expires | Low |

---

## ⚠️ Honest Limitations

| Limitation | Reason | Workaround |
|---|---|---|
| **Twitter/X auto-posting** | Twitter's API free tier doesn't include posting | Export queue as Buffer CSV → schedule via Buffer free tier |
| **Medium auto-publishing** | Medium API doesn't support full programmatic publishing | Copy from `generated/medium_*.txt` → paste in Medium editor (2 min each) |
| **Company page posting** | LinkedIn requires `rw_organization_social` Community Management API approval | Posts fall back to personal profile automatically until approval |
| **Real-time web search** | Gemini uses training data, not live search | `search_agent.py` RSS integration partially bridges this for AI news |
| **Perfect content quality** | Free AI models give strong drafts, not polished brand copy | `deep_research.py` + `brand_voice.py` significantly close the gap; human review recommended for key posts |

---

## 📊 Cost Breakdown

| Service | Free Tier | Our Usage |
|---|---|---|
| Gemini 2.5 API | ~1,500 requests/day | ~40 requests/week ✅ |
| OpenRouter (fallback) | Rate-limited free models | Only when Gemini fails ✅ |
| GitHub Actions | 2,000 min/month | ~15 min/week ✅ |
| GitHub Repo (private) | Unlimited | ✅ |
| Render Web Service | Free (sleeps when idle) | Dashboard only ✅ |
| Render Cron Jobs | Free tier | Scheduled posting ✅ |

**Monthly cost: ₹0** (Zero)

---

## 📄 License

MIT License — see [`LICENSE`](LICENSE) for details.

---

<div align="center">

**Built with ❤️ by the TechNova World team**

[![GitHub](https://img.shields.io/badge/GitHub-TechNovaWorldai-181717?style=flat-square&logo=github)](https://github.com/TechNovaWorldai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-TechNova_World-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/company/technova-world)

*If this saved you time, give it a ⭐ — it helps others find the project.*

</div>
