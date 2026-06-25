# 🌐 TechNova World — Automation v4.0

AI-powered content automation for TechNova World — algorithm-aware,
brand-voiced, fully tested, free-tier deployable.

---

## 🧠 "Posting Intelligence" — Kaise Kaam Karta Hai

Yeh sabse important sawal hai, isliye seedha explain karte hain — **3
alag layers** hain jo milkar "intelligence" banate hain:

### Layer 1 — WHEN to post (Timing Intelligence)
File: `config.py` + GitHub Actions cron schedule

```
LinkedIn  → Monday-Friday, 9:00 PM IST
Medium    → Tuesday + Thursday, 6:00 PM IST
Twitter   → 5 slots/day (9AM, 12PM, 3PM, 6PM, 11PM IST)
```

Yeh timing **algorithm research se aayi hai** (`algo_engine.py` mein
`LINKEDIN_ALGO["content_rules"]["post_timing_ist"]`) — LinkedIn pe
professionals subah aur office-end pe zyada active hote hain, isliye
9 PM IST (jab log dinner ke baad phone check karte hain) best window hai.

**Yeh fixed hai, AI nahi decide karta** — kyunki timing patterns
slow-changing hote hain, audience behavior se aate hain, har post ke
saath change nahi hote.

### Layer 2 — WHAT to post (Content Intelligence)
Files: `ai_generator.py` + `algo_engine.py` + `brand_voice.py`

Yeh teen-step process hai:

1. **Topic selection** — `get_trending_topics()` Gemini se current AI
   trends fetch karta hai, ya tum khud topic do
2. **Algorithm-aware generation** — `build_linkedin_prompt()` jaise
   functions Gemini ko exact rules dete hain (hook length, hashtag count,
   line breaks, no external links — yeh sab LinkedIn/Twitter/Medium ke
   real 2024-2025 algorithm research se hai)
3. **Quality scoring + auto-improve** — har generated post `score_linkedin_post()`
   se 0-100 score paata hai. Agar score 65 se kam hai, system khud
   `_improve_post()` call karke better version banata hai

### Layer 3 — IS it good enough (Safety Intelligence)
Files: `algo_engine.py` (`check_spam`, `check_value`) + `brand_voice.py`

Post hone se **pehle** 3 checks hote hain:
- **Spam check** — 30+ known spam patterns ("follow for follow",
  "DM me" etc.) detect karta hai
- **Value check** — content mein real value hai ya sirf filler
- **Brand voice check** — banned generic phrases ("game-changer",
  "revolutionize") catch karta hai

Agar koi check fail ho, post **queue mein "failed" mark hota hai aur
publish NAHI hota** — koi spam ya low-quality content automatically
nahi jaata.

---

## 🏗️ Deployment Architecture — Best Free Way

```
┌─────────────────────────────────────────────────────┐
│  GitHub Repo (free, private)                         │
│  ├─ Code + Secrets (encrypted)                        │
│  └─ 3 Scheduled Workflows:                            │
│                                                        │
│  ┌──────────────────┐   ┌──────────────────┐         │
│  │ Sunday 8PM IST    │   │ Mon-Fri 9PM IST  │         │
│  │ weekly-batch.yml  │──▶│ post-linkedin.yml│         │
│  │ Generates 5 days  │   │ Posts from queue  │         │
│  │ of content        │   │ to LinkedIn        │         │
│  └──────────────────┘   └──────────────────┘         │
│                                                        │
│  ┌──────────────────┐                                │
│  │ Every push        │                                │
│  │ run-tests.yml     │  ◀── 69 automated tests        │
│  └──────────────────┘                                │
└─────────────────────────────────────────────────────┘
```

**Why this is the best free way:**
- GitHub Actions = 2000 free minutes/month (tumhara usage: ~15 min/week)
- No server to maintain, no sleep/wake issues (unlike free-tier web hosts)
- Secrets encrypted, never exposed in code or logs
- Render.yaml included as backup option if you want a second platform

Full step-by-step: see **`DEPLOYMENT.md`**

---

## 📁 Project Structure

```
technova-deploy/
├── .github/workflows/       # 3 GitHub Actions (test, weekly batch, daily post)
├── automation/               # Non-interactive scripts for cron jobs
│   ├── post_scheduled.py     # Posts 1 queued item to LinkedIn
│   └── weekly_batch.py       # Generates 5 days of content
├── tests/run_tests.py        # 69 tests across 8 suites
├── algo_engine.py             # LinkedIn/Twitter/Medium algorithm rules + scorer
├── ai_generator.py            # Gemini-powered content generation
├── brand_voice.py             # TechNova World's unique voice rules
├── deep_research.py           # 4-step senior-writer-style generation
├── linkedin_poster.py         # LinkedIn API posting
├── search_agent.py            # Real-time AI news via RSS
├── watermark.py               # Image watermarking (Pillow)
├── pdf_carousel.py             # LinkedIn carousel PDF generator
├── video_script.py             # Shorts/Reels script generator
├── utils.py                    # Logging, retry, queue manager
├── config.py                   # Reads secrets from environment (safe for git)
├── run.py                      # Interactive local menu (17 options)
├── render.yaml                 # Render.com deployment config (alternative)
├── requirements.txt
├── .env.example                 # Template for local secrets
├── .gitignore                   # Protects .env and secrets
├── DEPLOYMENT.md                # Full deployment walkthrough
└── README.md                    # This file
```

---

## 🚀 Quick Start (Local)

```bash
pip install -r requirements.txt
cp .env.example .env
# .env mein apni Gemini + LinkedIn keys daalo
python run.py
```

## 🧪 Run Tests

```bash
python tests/run_tests.py          # All 69 tests
python tests/run_tests.py --fast    # Skip load tests (faster)
python tests/run_tests.py --suite algo   # Single suite
```

## ☁️ Deploy for 24/7 Automation

See **`DEPLOYMENT.md`** for the complete walkthrough — GitHub push,
secrets setup, and activating scheduled workflows.

---

## 🎯 What This App Does NOT Do (Honest Limits)

- Twitter/X auto-posting — Twitter's API is paid ($100/month). Use
  Buffer.com free tier with the generated content instead.
- Medium auto-publishing — Medium's API doesn't support full auto-publish
  reliably. Copy generated articles from `generated/` and paste manually
  (2 min/article).
- "Anthropic/Google-level" content — free AI models give good drafts,
  not polished brand copy. `deep_research.py` + `brand_voice.py` close
  the gap significantly, but human review before posting is still
  recommended for important content.

---

*TechNova World — 100% free-tier automation, algorithm-aware, tested.*
