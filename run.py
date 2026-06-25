"""
TechNova World — Main Runner v3.0
Algorithm-aware content + full quality pipeline

Run:       python run.py
Run tests: python run.py --test
"""

import sys, os, time, schedule, argparse
from datetime import datetime
from pathlib import Path

from utils        import logger, queue_mgr, validate_config
from ai_generator import (
    generate_linkedin_post, generate_twitter_posts,
    generate_twitter_thread, generate_medium_article,
    repurpose_article, get_trending_topics, generate_weekly_batch,
)
from algo_engine import (
    score_linkedin_post, score_twitter_post, score_medium_article,
    check_spam, check_value, print_score_report,
    LINKEDIN_ALGO, TWITTER_ALGO, MEDIUM_ALGO,
)
from linkedin_poster import post_to_linkedin, check_linkedin_connection
from watermark       import add_watermark, batch_watermark
from search_agent    import search_agent
from pdf_carousel    import create_linkedin_carousel, REPORTLAB_OK
from video_script    import create_full_video_package, VIDEO_FORMATS
from brand_voice     import (load_voice, save_voice, check_voice_compliance,
                              build_voice_context, add_banned_phrase,
                              add_signature_phrase, voice_setup_wizard)
from deep_research   import deep_research_generate
import config as cfg

G  = "\033[32m"; Y  = "\033[33m"; R  = "\033[31m"
C  = "\033[36m"; B  = "\033[1m";  RE = "\033[0m"

def setup():
    for d in ["queue","logs","generated","images","images/watermarked","tests","assets"]:
        Path(d).mkdir(parents=True, exist_ok=True)

def hdr(title=""):
    print(f"\n{B}{'='*60}{RE}")
    if title:
        print(f"{B}  {title}{RE}")
        print(f"{B}{'='*60}{RE}")

def ask(prompt, default=""):
    v = input(f"\n  {prompt}: ").strip()
    return v or default

def confirm(prompt):
    return input(f"\n  {prompt} (y/n): ").strip().lower() == "y"

def pause():
    input(f"\n  {G}Press Enter to continue...{RE}")


# ── CONNECTION TEST ──────────────────────────────────────────
def run_connection_test():
    hdr("Connection Tests")
    gem_ok = bool(cfg.GEMINI_API_KEY)
    li_ok  = check_linkedin_connection()
    print(f"\n  {'OK' if gem_ok else 'MISSING'} Gemini API")
    print(f"  {'OK' if li_ok  else 'MISSING'} LinkedIn Company Page")
    print(f"  INFO Twitter -> Buffer.com (free)")
    print(f"  INFO Medium  -> Manually publish")
    if not gem_ok:
        print(f"\n  aistudio.google.com -> free API key lo")
        print(f"  config.py mein GEMINI_API_KEY set karo")
    pause()


# ── ALGO VIEWER ──────────────────────────────────────────────
def run_algo_viewer():
    hdr("Platform Algorithm Rules")
    print("\n  1. LinkedIn  2. Twitter/X  3. Medium")
    choice = ask("Platform (1/2/3)", "1")
    algo_map = {"1":("LinkedIn",LINKEDIN_ALGO),
                "2":("Twitter/X",TWITTER_ALGO),
                "3":("Medium",MEDIUM_ALGO)}
    name, algo = algo_map.get(choice, algo_map["1"])
    print(f"\n  {name} Algorithm Rules")
    print("  " + "-"*50)
    print("\n  Ranking Signals (weight %):")
    for sig, data in algo["ranking_signals"].items():
        bar = "#" * (data["weight"] // 5)
        print(f"  {sig:<22} [{bar:<20}] {data['weight']}%")
        print(f"    -> {data['note']}")
    print("\n  Killing Factors (avoid!):")
    for kf in algo["killing_factors"][:5]:
        print(f"  - {kf}")
    pause()


# ── QUALITY SCORER ───────────────────────────────────────────
def run_quality_scorer():
    hdr("Content Quality Scorer")
    print("\n  Platform: 1=LinkedIn  2=Twitter  3=Medium")
    plat_map = {"1":"linkedin","2":"twitter","3":"medium"}
    plat = plat_map.get(ask("Platform (1/2/3)","1"), "linkedin")
    print("\n  Paste your content (Enter twice to finish):\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if not text:
        print("  Empty content"); pause(); return

    spam = check_spam(text)
    if not spam["safe_to_post"]:
        print(f"\n  SPAM DETECTED: {spam['spam_signals']}")
        pause(); return

    value = check_value(text)
    print(f"\n  Value Score: {value['verdict']}")

    if plat == "linkedin":
        qs = score_linkedin_post(text)
    elif plat == "twitter":
        qs = score_twitter_post(text)
    else:
        title = ask("Article title","")
        sub   = ask("Subtitle","")
        qs    = score_medium_article(title, text, sub)
    print_score_report(qs)
    pause()


# ── TRENDING TOPICS ──────────────────────────────────────────
def run_trending_topics():
    hdr("Trending AI Topics")
    result = get_trending_topics()
    if result:
        print(result)
        from utils import save_text
        save_text(f"generated/trending_{datetime.now().strftime('%Y%m%d')}.txt", result)
        print(f"\n  Saved to generated/")
    else:
        print("  Failed - check Gemini API key")
    pause()


# ── NEWS FEED ────────────────────────────────────────────────
def run_news_fetch():
    hdr("AI News Feed (Real-time RSS)")
    result = search_agent.fetch_and_cache(force=True)
    if not result:
        print(f"  Failed: {result.error}"); pause(); return
    articles = result.data
    print(f"\n  {len(articles)} articles fetched!\n")
    for i, a in enumerate(articles[:6], 1):
        print(f"  {i}. [{a['source']}] {a['title'][:70]}")
    choice = ask("Article se post banao? (1-6, skip=Enter)", "")
    if choice.isdigit() and 1 <= int(choice) <= min(6, len(articles)):
        a = articles[int(choice)-1]
        print("  Platform: 1=LinkedIn  2=Twitter  3=Medium")
        p = {"1":"linkedin","2":"twitter_5","3":"medium_outline"}.get(ask("Platform","1"),"linkedin")
        from search_agent import generate_post_from_news
        r = generate_post_from_news(a, p)
        if r:
            print(f"\n  Generated Post:\n  {'─'*50}")
            print(r.data)
            if confirm("Queue mein add karo?"):
                queue_mgr.add(p.split("_")[0], r.data, a["title"])
                print("  Added to queue!")
    pause()


# ── WEEKLY CONTENT ───────────────────────────────────────────
def run_weekly_content():
    hdr("Weekly Content Generator (5 days)")
    days = ["Monday","Tuesday (+ Medium)","Wednesday","Thursday (+ Medium)","Friday"]
    topics = []
    print()
    for day in days:
        t = ask(f"{day} topic")
        topics.append(t or f"AI productivity tip for {day}")
    print(f"\n  Generating algo-optimised content for {len(topics)} days...")
    result = generate_weekly_batch(topics)
    print(f"\n  Done! Check generated/ folder")
    pause()


# ── SINGLE POST ──────────────────────────────────────────────
def run_single_post():
    hdr("Generate Single Post")
    print("\n  1. LinkedIn Post")
    print("  2. Twitter 5 Posts")
    print("  3. Twitter Thread (8 tweets)")
    print("  4. Medium Article")
    choice = ask("Platform (1-4)","1")
    topic  = ask("Topic")
    if not topic: print("  Topic empty"); pause(); return

    if choice == "1":
        content = generate_linkedin_post(topic, auto_improve=True, show_score=True)
        if content:
            print(f"\n  {'─'*50}\n{content}\n  {'─'*50}")
            spam = check_spam(content)
            print(f"\n  Spam check: {'SAFE' if spam['safe_to_post'] else 'FLAGGED'}")
            if confirm("Post to LinkedIn now?"):
                r = post_to_linkedin(content)
                print(f"  {'Posted! ID: '+r.data['post_id'] if r else 'Failed: '+r.error}")
            elif confirm("Add to queue?"):
                queue_mgr.add("linkedin", content, topic)
                print("  Added to queue!")

    elif choice == "2":
        tweets = generate_twitter_posts(topic, 5)
        for i, t in enumerate(tweets, 1):
            s = score_twitter_post(t)
            print(f"\n  Tweet {i} [{s.total}/100]: {t}")
        from utils import save_text
        save_text(f"generated/twitter_{datetime.now().strftime('%H%M')}.txt", "\n\n".join(tweets))

    elif choice == "3":
        thread = generate_twitter_thread(topic, 8)
        for i, t in enumerate(thread, 1):
            print(f"\n  {i}/8: {t}")
        from utils import save_text
        save_text(f"generated/thread_{datetime.now().strftime('%H%M')}.txt", "\n\n".join(thread))

    elif choice == "4":
        art = generate_medium_article(topic, show_score=True)
        if art:
            print(f"\n  Title: {art.get('title')}")
            print(f"  Subtitle: {art.get('subtitle')}")
            from utils import save_text
            c = (f"TITLE: {art.get('title')}\n"
                 f"SUBTITLE: {art.get('subtitle')}\n\n"
                 f"{art.get('content')}\n\n"
                 f"TAGS: {', '.join(art.get('tags',[]))}")
            p = f"generated/medium_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            save_text(p, c)
            print(f"  Saved: {p}")
    pause()


# ── REPURPOSE ────────────────────────────────────────────────
def run_repurpose():
    hdr("Repurpose Article -> All Platforms")
    print("  Paste your article (Enter twice to finish):\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if len(text) < 100:
        print("  Too short (min 100 chars)"); pause(); return
    result = repurpose_article(text)
    if result:
        from utils import save_text
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out = "\n".join(f"\n{'='*40}\n{k.upper()}\n{'='*40}\n{v}" for k,v in result.items())
        path = f"generated/repurposed_{ts}.txt"
        save_text(path, out)
        print(f"\n  Formats generated: {', '.join(result.keys())}")
        print(f"  Saved: {path}")
    pause()


# ── WATERMARK ────────────────────────────────────────────────
def run_watermark():
    hdr("Image Watermark Tool")
    print("  1. Single image  2. Batch folder")
    choice = ask("Choice","1")
    if choice == "1":
        path = ask("Image path (e.g. images/post.jpg)")
        r = add_watermark(path) if path else None
        print(f"  {'Done: '+r if r else 'Failed or path empty'}")
    else:
        folder = ask("Folder path","images/")
        results = batch_watermark(folder)
        print(f"  {len(results)} images watermarked")
    pause()


# ── PDF CAROUSEL ─────────────────────────────────────────────
def run_pdf_carousel():
    hdr("LinkedIn PDF Carousel Generator")
    if not REPORTLAB_OK:
        print("  Install reportlab: pip install reportlab"); pause(); return
    topic  = ask("Carousel topic")
    if not topic: print("  Topic empty"); pause(); return
    slides = int(ask("Slides count (default 8)","8") or "8")
    slides = max(4, min(12, slides))
    print(f"\n  Generating {slides}-slide carousel...")
    r = create_linkedin_carousel(topic, slide_count=slides)
    if r:
        print(f"\n  PDF:     {r.data['pdf']}")
        print(f"  Outline: {r.data['outline']}")
        print(f"  Upload this PDF as a LinkedIn document post!")
    else:
        print(f"  Failed: {r.error}")
    pause()


# ── VIDEO SCRIPT ─────────────────────────────────────────────
def run_video_script():
    hdr("Video Script Generator")
    for k,v in VIDEO_FORMATS.items():
        print(f"  {k}: {v['name']}")
    fmt   = ask("Format","shorts_60")
    topic = ask("Topic")
    if not topic: print("  Topic empty"); pause(); return
    r = create_full_video_package(topic, fmt)
    if r:
        print(f"\n  Script: {r.data.get('script_file')}")
        raw = r.data["script"].get("raw","")[:500]
        print(f"\n  Preview:\n  {'─'*40}")
        for line in raw.split('\n')[:10]:
            print(f"  {line}")
        print("  ...")
    else:
        print(f"  Failed: {r.error}")
    pause()


# ── QUEUE ────────────────────────────────────────────────────
def run_queue():
    hdr("Post Queue")
    s = queue_mgr.stats()
    print(f"\n  Total: {s['total']}  Pending: {s['pending']}  Posted: {s['posted']}  Failed: {s['failed']}")
    p = queue_mgr.pending()
    if p:
        print(f"\n  Next {min(5,len(p))} pending:")
        for q in p[:5]:
            print(f"  [{q['platform'].upper():10}] {q['topic'][:55]}")
    if p and confirm("Post next LinkedIn item now?"):
        li = queue_mgr.pending("linkedin")
        if li:
            item = li[0]
            r = post_to_linkedin(item["content"])
            if r:
                queue_mgr.mark(item["id"], "posted")
                print(f"  Posted!")
            else:
                queue_mgr.mark(item["id"], "failed", r.error)
                print(f"  Failed: {r.error}")
    pause()


# ── SCHEDULER ────────────────────────────────────────────────
def run_scheduler():
    hdr("Auto Scheduler")
    if not check_linkedin_connection():
        print("  LinkedIn not connected"); pause(); return

    def job():
        logger.info("Scheduled LinkedIn post time!")
        pending = queue_mgr.pending("linkedin")
        if not pending:
            logger.warning("LinkedIn queue empty")
            return
        item = pending[0]
        r = post_to_linkedin(item["content"])
        if r:
            queue_mgr.mark(item["id"], "posted")
        else:
            queue_mgr.mark(item["id"], "failed", r.error)

    for day in [schedule.every().monday, schedule.every().tuesday,
                schedule.every().wednesday, schedule.every().thursday,
                schedule.every().friday]:
        day.at(cfg.LINKEDIN_POST_TIME).do(job)

    print(f"\n  Scheduler running! LinkedIn posts: Mon-Fri {cfg.LINKEDIN_POST_TIME} IST")
    print("  Press Ctrl+C to stop\n")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n  Scheduler stopped.")
        pause()


# ── BRAND VOICE ──────────────────────────────────────────────
def run_brand_voice():
    hdr("Brand Voice Manager")
    v = load_voice()
    print(f"\n  Current Identity: {v['personality']['primary_trait']}")
    print(f"  Banned phrases ({len(v['banned_phrases'])}): {', '.join(v['banned_phrases'][:6])}...")
    print(f"  Signature style examples:")
    for p in v['signature_phrases'][:3]:
        print(f"    - {p}")

    print("\n  1. Run full setup wizard")
    print("  2. Add a banned phrase")
    print("  3. Add a signature phrase")
    print("  4. Check existing text for voice compliance")
    print("  0. Back")

    choice = ask("Choice", "0")
    if choice == "1":
        voice_setup_wizard()
    elif choice == "2":
        p = ask("Phrase to ban")
        if p:
            add_banned_phrase(p)
            print(f"  Added '{p}' to banned phrases")
    elif choice == "3":
        p = ask("New signature phrase")
        if p:
            add_signature_phrase(p)
            print(f"  Added '{p}' to signature phrases")
    elif choice == "4":
        print("  Paste text (Enter twice to finish):\n")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        text = "\n".join(lines).strip()
        if text:
            r = check_voice_compliance(text)
            print(f"\n  Voice Score: {r['voice_score']}/100  {r['verdict']}")
            if r['violations']:
                print(f"  Banned phrases found: {', '.join(r['violations'])}")
            if r['suggestions']:
                print(f"  Suggestions:")
                for s in r['suggestions']:
                    print(f"    - {s}")
    pause()


# ── DEEP RESEARCH MODE ───────────────────────────────────────
def run_deep_research():
    hdr("Deep Research Mode (4-step senior-writer process)")
    print("\n  This takes longer (~30-60s) but produces MUCH higher quality")
    print("  content vs single-prompt generation. Use for important posts.\n")
    print("  Platform: 1=LinkedIn  2=Medium  3=Twitter Thread")
    plat_map = {"1":"linkedin","2":"medium","3":"twitter_thread"}
    plat = plat_map.get(ask("Platform","1"), "linkedin")
    topic = ask("Topic")
    if not topic:
        print("  Topic empty"); pause(); return

    print(f"\n  Step 1/4: Research outline...")
    print(f"  Step 2/4: Gathering specifics...")
    print(f"  Step 3/4: Writing deep draft...")
    print(f"  Step 4/4: Self-critique + polish...")
    print(f"  (Watch logs above for live progress)\n")

    result = deep_research_generate(topic, platform=plat)

    if result:
        print(f"\n  {'─'*55}")
        print(f"  FINAL CONTENT:")
        print(f"  {'─'*55}")
        print(result.data["final"])
        print(f"  {'─'*55}")
        compliance = result.data["compliance"]
        print(f"\n  Brand voice: {compliance['verdict']} ({compliance['voice_score']}/100)")

        if plat == "linkedin":
            score = score_linkedin_post(result.data["final"])
            print(f"  Algo score:  {score.total}/100 (Grade {score.grade})")

        if confirm("Queue mein add karo?"):
            queue_mgr.add(plat.split("_")[0], result.data["final"], topic)
            print("  Added to queue!")
    else:
        print(f"  Failed: {result.error}")
    pause()


# ── TESTS ────────────────────────────────────────────────────
def run_tests():
    hdr("Test Suite v3.0")
    fast = confirm("Fast mode? (skip load tests)")
    cmd = f"{sys.executable} tests/run_tests.py{'  --fast' if fast else ''}"
    print(f"\n  Running: {cmd}\n")
    os.system(cmd)
    pause()


# ════════════════════════════════════════════════════════════
# MAIN MENU
# ════════════════════════════════════════════════════════════

MENU = [
    ("1",  "Connection test",                    run_connection_test),
    ("2",  "Platform algorithm rules viewer",    run_algo_viewer),
    ("3",  "Quality scorer (paste & score)",     run_quality_scorer),
    ("4",  "Brand voice manager",                run_brand_voice),
    ("5",  "Deep Research mode (4-step, best quality)", run_deep_research),
    ("6",  "Trending AI topics",                 run_trending_topics),
    ("7",  "AI News feed (RSS real-time)",       run_news_fetch),
    ("8",  "Weekly content batch (5 days)",      run_weekly_content),
    ("9",  "Single post / article generator",    run_single_post),
    ("10", "Repurpose article -> all platforms", run_repurpose),
    ("11", "Image watermark (single / batch)",   run_watermark),
    ("12", "LinkedIn PDF carousel",              run_pdf_carousel),
    ("13", "Video script (Shorts / Reels)",      run_video_script),
    ("14", "View & manage post queue",           run_queue),
    ("15", "Start auto-scheduler",               run_scheduler),
    ("16", "Run all tests",                      run_tests),
    ("0",  "Exit",                               None),
]


def main():
    setup()

    # CLI flag: python run.py --test
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run tests directly")
    args, _ = parser.parse_known_args()
    if args.test:
        run_tests(); return

    while True:
        hdr("TechNova World — Automation Hub v3.0")
        print(f"\n  {B}Main Menu:{RE}\n")
        for key, label, _ in MENU:
            print(f"  {key:>2}.  {label}")

        choice = ask("Option")
        handler = next((fn for k,_,fn in MENU if k==choice), None)

        if choice == "0":
            print(f"\n  Goodbye! Keep building TechNova World.\n"); break
        elif handler:
            try:
                handler()
            except KeyboardInterrupt:
                print(f"\n  Cancelled.")
            except Exception as e:
                logger.error(f"Error in option {choice}: {e}")
                print(f"  Error: {e}")
                pause()
        else:
            print(f"  Invalid — choose 0-16")
            time.sleep(1)


if __name__ == "__main__":
    main()
