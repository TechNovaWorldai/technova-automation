# 🌐 TechNova World — Complete Deployment Guide v4.0

Yeh guide tumhe step-by-step batayega: GitHub pe push kaise karo, secrets
kaise safe rakho, aur 24/7 automation kaise activate karo (free).

---

## ⚠️ Pehle yeh samjho — bahut zaroori

**24/7 ka matlab "ek server hamesha chal raha hai" nahi hai (free mein yeh
nahi milta). Iska matlab hai: "scheduled jobs jo automatically, bina tumhare
laptop ke, sahi time pe chalte hain."**

- LinkedIn pe Mon-Fri 9PM IST post → GitHub Actions cron job chalega
- Sunday content batch generate → GitHub Actions cron job chalega
- Tumhara laptop band ho, sleep mode mein ho — koi farak nahi padega
- Yeh GitHub ke servers pe chalta hai, bilkul free (2000 min/month tak)

---

## 📋 Part 1 — GitHub Pe Push Karna

### Step 1: Naya repository banao

1. github.com pe jaao → "New repository"
2. Name: `technova-automation` (ya jo chaho)
3. **Private** select karo (recommended — apna business logic public mat rakho)
4. "Create repository" click karo

### Step 2: Apne computer pe yeh folder push karo

```bash
cd path/to/technova-deploy
git init
git add .
git commit -m "Initial commit - TechNova World automation v4.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/technova-automation.git
git push -u origin main
```

> 💡 Agar git command line se comfortable nahi ho, **GitHub Desktop** use
> karo — "Add Local Repository" → folder select karo → "Publish repository"

### Step 3: Verify karo ki secrets push NAHI hue

```bash
git log --all --full-history -- .env
```

Yeh **kuch return nahi karna chahiye**. Agar kuch dikhe, turant `.env` file
delete karke dobara commit karo, aur apni saari keys **regenerate** karo
(purani keys ab compromised maan lo).

---

## 🔐 Part 2 — GitHub Secrets Setup (Sabse Important Step)

API keys **kabhi code mein nahi jaati** — GitHub ke encrypted "Secrets"
vault mein jaati hain.

1. Apne repo pe jaao → **Settings** tab
2. Left sidebar: **Secrets and variables** → **Actions**
3. **"New repository secret"** click karo — yeh 4 secrets banao:

| Secret Name | Value kahan se milegi |
|---|---|
| `GEMINI_API_KEY` | aistudio.google.com → Get API Key |
| `OPENROUTER_API_KEY` | openrouter.ai → Sign up free → Keys (optional but recommended) |
| `LINKEDIN_ACCESS_TOKEN` | developer.linkedin.com → OAuth Playground |
| `LINKEDIN_ORGANIZATION_ID` | LinkedIn Company Page URL se number |

Each ke liye: Name daalo (exact wahi naam upar table mein hai) → Value
paste karo → "Add secret"

> 🔒 Yeh secrets sirf GitHub Actions workflows access kar sakte hain.
> Koi insaan, koi log, koi public jagah — yeh values kabhi nahi dikhengi.

---

## ⚙️ Part 3 — GitHub Actions Activate Karna

Repo mein already 3 workflow files hain (`.github/workflows/`):

| File | Kya karta hai | Kab chalta hai |
|---|---|---|
| `run-tests.yml` | Saare 69 tests chalata hai | Har push pe automatically |
| `weekly-batch.yml` | Poori week ka content generate | Sunday 8 PM IST |
| `post-linkedin.yml` | Queue se LinkedIn pe post karta hai | Mon-Fri 9 PM IST |

**Activate karne ke liye kuch karna nahi hai** — jaise hi tum push karoge,
GitHub automatically yeh dekh lega aur schedule pe chalne lagega.

### Verify karo ki kaam kar raha hai:

1. Repo pe jaao → **Actions** tab
2. Tumhe teen workflows dikhenge
3. Pehli baar manually test karne ke liye: kisi workflow pe click karo →
   **"Run workflow"** button → "Run workflow" confirm karo
4. 1-2 minute mein result dikhega (green ✅ ya red ❌)

### Agar red ❌ dikhe:

1. Failed run pe click karo → log dekho
2. Common issues:
   - Secret naam galat type hua (case-sensitive hai)
   - LinkedIn token expire ho gaya (60 din mein expire hota hai — naya lo)
   - Gemini free tier limit hit hui (1500/day — agle din retry hoga)

---

## 🌍 Part 4 — Render.com (Web Dashboard — Required for Browser UI)

GitHub Actions sirf **scheduled jobs** chala sakta hai — koi live website
nahi de sakta. Dashboard (browser se input/output/queue/research) dekhne
ke liye **Render.com pe ek live URL** chahiye. Yeh free hai.

### Setup (10 minutes):

1. **render.com** pe free account banao (GitHub se sign in kar sakte ho)
2. **"New +"** → **"Blueprint"**
3. Apna GitHub repo connect karo (permission allow karo)
4. Render automatically `render.yaml` detect karega — yeh **3 services**
   banayega:

   | Service | Type | Kya karta hai |
   |---|---|---|
   | `technova-dashboard` | Web | Browser dashboard — live URL milega |
   | `technova-linkedin-poster` | Cron | Mon-Fri 9:30 PM IST auto-post |
   | `technova-weekly-batch` | Cron | Sunday 8:30 PM IST content batch |

5. Har service pe click karo → **Environment** tab → secrets daalo:
   - `GEMINI_API_KEY`
   - `OPENROUTER_API_KEY` (optional but recommended — fallback)
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_ORGANIZATION_ID`
   - `FLASK_SECRET_KEY` — Render apne aap generate kar dega (`generateValue: true`)
6. **"Apply"** / **"Deploy"** click karo
7. 2-3 minute mein build complete hoga
8. `technova-dashboard` service pe click karo → top pe **live URL** milega
   (kuch aisa: `https://technova-dashboard.onrender.com`)

### ⚠️ Important — Free Web Service "Sleep" Behavior

Render ka **free web service** 15 minute inactivity ke baad sleep ho jaata
hai. Jab tum dashboard open karoge, **first request 30-50 seconds** lag
sakta hai (server wake-up time) — uske baad normal speed.

**Yeh scheduled posting ko AFFECT NAHI karta** — `technova-linkedin-poster`
aur `technova-weekly-batch` **cron jobs** hain, web service se alag. Render
unhe khud wake karke chalata hai, sahi time pe, dashboard sleep ho ya na ho.

> 💡 **GitHub Actions vs Render Cron — dono free hain.**
> Render web service zaroori hai (dashboard ke liye) — lekin scheduled
> posting GitHub Actions YA Render cron, **sirf ek** rakho (dono active
> rakhoge toh ek hi post 2 baar ho sakta hai).

---

## 🧪 Part 5 — Tests Run Karna (Local + Automatic)

### Local pe (apne computer pe):

```bash
pip install -r requirements.txt
cp .env.example .env
# .env mein apni keys daalo
python tests/run_tests.py
```

Expected output: **69/69 tests passed (100%)**

### GitHub pe (automatic):

Har baar jab tum `git push` karoge, `run-tests.yml` workflow automatically
chalega. Repo ke **Actions** tab mein result dikhega. Agar koi test fail
ho, GitHub tumhe email karega.

---

## 🔄 Part 6 — Token Renewal (Har 60 Din Zaroori)

LinkedIn ka access token **60 din** mein expire ho jaata hai. Jab expire
ho jaaye:

1. linkedin.com/developers/tools/oauth → naya token generate karo
2. GitHub repo → Settings → Secrets → `LINKEDIN_ACCESS_TOKEN` → **Update**
3. Naya value paste karo → Save

> 💡 Calendar reminder set kar lo — har 55 din pe ek reminder, taaki
> automation kabhi rukke nahi.

---

## ✅ Quick Checklist — Deployment Se Pehle

- [ ] `.env` file `.gitignore` mein hai (already configured)
- [ ] `git log --all -- .env` kuch return nahi karta
- [ ] GitHub repo **Private** hai
- [ ] 4 Secrets GitHub mein add ho gaye (Gemini + OpenRouter + LinkedIn token + Org ID)
- [ ] `run-tests.yml` workflow green ✅ dikh raha hai Actions tab mein
- [ ] LinkedIn token expiry date kahin note kar li (60 din se)
- [ ] Pehla manual "Run workflow" test successful raha
- [ ] Render `technova-dashboard` service deploy ho gaya — live URL khulta hai
- [ ] Render Environment tab mein bhi same 4 secrets daal diye

---

## 🆘 Troubleshooting

| Problem | Solution |
|---|---|
| "Secret not found" error | Secret naam exact match check karo (case-sensitive) |
| LinkedIn post fail ho raha | Token expired — naya generate karo |
| Gemini "429 rate limit" | App automatically Gemini Pro ya OpenRouter try karega — wait karo |
| Workflow nahi chal raha automatically | Repo **Settings → Actions → General** mein "Allow all actions" enabled hai check karo |
| Queue khali hai, kuch post nahi hua | `weekly-batch.yml` pehle chalna chahiye Sunday ko — manually "Run workflow" try karo |
| Dashboard 30-50 sec lag raha pehli baar | Normal — free tier sleep se wake ho raha hai. Doosri request fast hogi. |
| Dashboard "Application Error" dikhe | Render → Logs tab dekho — usually missing secret ya build fail |

---

## 📊 Cost Summary

| Service | Free Tier Limit | Tumhara Usage |
|---|---|---|
| Gemini 2.5 API | Daily free quota | ~30-40 requests/week — well within limit |
| OpenRouter (fallback) | Rate-limited but free | Only used if Gemini fails |
| GitHub Actions | 2000 min/month | ~15 min/week — well within limit |
| GitHub (private repo) | Unlimited free | ✅ |
| Render Web Service | Free tier (sleeps when idle) | ✅ Dashboard |
| Render Cron Jobs | Free tier available | ✅ Scheduled posting

**Total monthly cost: ₹0**

---

*TechNova World Automation v4.0 — Deployment Guide*
