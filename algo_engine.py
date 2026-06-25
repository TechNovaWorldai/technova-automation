"""
TechNova World — Algorithm Rules Engine v3.0
LinkedIn + Twitter/X + Medium ke algorithm rules
Research-based, 2024-2025 current

Sources: LinkedIn Engineering Blog, Twitter API docs,
         Medium Partner Program data, creator studies
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from enum import Enum


class Platform(Enum):
    LINKEDIN = "linkedin"
    TWITTER  = "twitter"
    MEDIUM   = "medium"


# ════════════════════════════════════════════════════════════
# LINKEDIN ALGORITHM — 2024/2025
# Key signal: DWELL TIME > comments > reactions > shares
# ════════════════════════════════════════════════════════════

LINKEDIN_ALGO = {
    "ranking_signals": {
        "dwell_time":        {"weight": 35, "note": "Highest signal — how long people read your post"},
        "comments":          {"weight": 25, "note": "Deep comments > one-word comments"},
        "reactions":         {"weight": 15, "note": "Any reaction counts, Love > Like"},
        "shares":            {"weight": 10, "note": "Reshares with commentary = bonus"},
        "click_through":     {"weight": 10, "note": "Clicks on 'see more' = strong positive"},
        "saves":             {"weight": 5,  "note": "Saves = high intent signal"},
    },
    "content_rules": {
        "optimal_length":    {"min": 900,  "max": 1300, "unit": "chars",
                              "note": "Long enough for dwell time, short enough to read"},
        "line_breaks":       {"frequency": "every_2_3_lines",
                              "note": "White space = readability = more dwell time"},
        "hook_lines":        {"count": 2, "chars_max": 140,
                              "note": "First 2 lines show before 'see more' — make them IRRESISTIBLE"},
        "question_at_end":   {"required": True,
                              "note": "Genuine question drives comments — algo rewards it"},
        "hashtags":          {"min": 3, "max": 5,
                              "note": "3-5 relevant hashtags. More = spam signal"},
        "external_links":    {"in_post": False,
                              "note": "Links kill reach — put in first comment instead"},
        "post_timing_ist":   ["08:00", "12:00", "17:00", "20:00", "21:00"],
        "best_days":         ["Tuesday", "Wednesday", "Thursday"],
        "avoid_days":        ["Saturday", "Sunday"],
    },
    "hook_rules": {
        "banned_starts":  [
            "I am excited", "I am happy", "We are excited", "We are happy",
            "Proud to announce", "Thrilled to share", "Delighted to",
            "I am pleased", "Excited to share", "Happy to announce",
        ],
        "strong_patterns": [
            "Number + result (e.g. '5 AI tools that...')",
            "Controversial statement ('Most people waste 3 hours...')",
            "Question hook ('What if AI could...')",
            "Shocking stat ('87% of developers don't know...')",
            "Personal failure story ('I failed at X. Here's what I learned:')",
            "Counter-intuitive ('Stop learning Python. Do this instead:')",
        ],
    },
    "comment_triggers": {
        "good_questions": [
            "What tool surprised you the most?",
            "Which one are you trying first?",
            "What's your experience with [topic]?",
            "Am I missing anything from this list?",
            "What would you add?",
        ],
        "note": "Ask ONE specific question. Multiple questions = lower response rate",
    },
    "carousel_rules": {
        "slides":          {"min": 5, "max": 10, "optimal": 8},
        "words_per_slide": {"max": 30},
        "first_slide":     "Bold statement or question — must hook on feed",
        "last_slide":      "Always end with clear CTA + brand",
        "note":            "Carousels get 3x more reach than plain text posts on average",
    },
    "killing_factors": [
        "Posting external links in post body (cuts reach by 60%+)",
        "Using more than 5 hashtags",
        "Tagging people who don't engage (spam signal)",
        "Re-sharing without commentary",
        "Posting more than 2x per day",
        "Ignoring comments in first 60 minutes (golden window)",
    ],
}


# ════════════════════════════════════════════════════════════
# TWITTER/X ALGORITHM — 2024/2025
# Key signal: REPLIES > bookmarks > retweets > likes
# ════════════════════════════════════════════════════════════

TWITTER_ALGO = {
    "ranking_signals": {
        "replies":           {"weight": 30, "note": "Replies = conversation = biggest signal"},
        "bookmarks":         {"weight": 25, "note": "Bookmarks = save for later = high value"},
        "retweets_quote":    {"weight": 20, "note": "Quote tweets with commentary > plain RT"},
        "likes":             {"weight": 15, "note": "Good but least important of the 4"},
        "profile_clicks":    {"weight": 7,  "note": "Clicking profile = strong interest signal"},
        "link_clicks":       {"weight": 3,  "note": "Leaving Twitter = slightly negative"},
    },
    "content_rules": {
        "tweet_length":      {"optimal": "71-100", "max": 280, "unit": "chars",
                              "note": "Shorter tweets often outperform long ones for engagement"},
        "thread_length":     {"min": 5, "max": 12, "optimal": 7,
                              "note": "Threads get 63% more impressions than single tweets"},
        "images":            {"boost": "2x impressions",
                              "note": "Tweets with images get 2x more impressions"},
        "post_timing_ist":   ["08:30", "12:00", "15:00", "18:00", "22:00"],
        "best_days":         ["Monday", "Tuesday", "Wednesday", "Thursday"],
        "frequency":         {"per_day": 5, "max": 7,
                              "note": "5-7 posts/day for growth. More = diminishing returns"},
        "hashtags":          {"max": 2,
                              "note": "1-2 hashtags max. More hashtags HURT reach on X in 2024"},
    },
    "viral_patterns": {
        "hot_takes":         "Confident opinion on trending topic",
        "list_tweets":       "Numbered list (1. 2. 3.) — easy to skim + save",
        "question_tweets":   "Simple yes/no or either/or question",
        "story_tweets":      "Personal story in thread format",
        "news_commentary":   "Break news + add your take",
        "prediction":        "Bold prediction about AI future",
        "before_after":      "Before AI: [x]. After AI: [y].",
        "contrarian":        "'Unpopular opinion: [statement]'",
    },
    "thread_structure": {
        "tweet_1": "Hook — makes them want to read all. End with 🧵",
        "tweet_2_n": "One insight per tweet. Short. Punchy. Numbered.",
        "last_tweet": "Summary + 'Follow @TechNovaWorld for more AI insights'",
        "note": "First tweet is everything — if it doesn't hook, no one reads thread",
    },
    "killing_factors": [
        "More than 2 hashtags per tweet (2024 algo change)",
        "Asking for retweets explicitly ('RT if you agree')",
        "Posting external links without context",
        "Deleting and reposting (penalized)",
        "Long gaps between thread tweets (post all at once)",
        "Replying to your own thread hours later",
    ],
    "reply_strategy": {
        "note": "Reply to big AI accounts within 30 min of their post",
        "why":  "Early thoughtful replies get exposure to their audience",
        "how":  "Add value, not just agree. Ask follow-up question.",
    },
}


# ════════════════════════════════════════════════════════════
# MEDIUM ALGORITHM — 2024/2025
# Key signal: READ RATIO > highlights > follows from article
# ════════════════════════════════════════════════════════════

MEDIUM_ALGO = {
    "ranking_signals": {
        "read_ratio":        {"weight": 40, "note": "% of readers who finish article. Most important."},
        "highlights":        {"weight": 20, "note": "Highlighted text = strong engagement signal"},
        "claps":             {"weight": 15, "note": "Up to 50 claps per reader"},
        "follows":           {"weight": 15, "note": "Reader follows you = highest intent signal"},
        "responses":         {"weight": 10, "note": "Comments on article"},
    },
    "content_rules": {
        "optimal_length":    {"min": 600,  "max": 1000, "unit": "words",
                              "note": "7-min read = sweet spot for Partner Program earnings"},
        "title_length":      {"max": 60, "unit": "chars",
                              "note": "Shorter titles rank better in search"},
        "subtitle":          {"required": True, "max": 100,
                              "note": "Subtitle appears in search results — make it SEO-rich"},
        "first_paragraph":   {"note": "First 150 words = preview. Must hook or they bounce."},
        "subheadings":       {"every_n_words": 200,
                              "note": "Subheadings improve read ratio — people skim first"},
        "images":            {"min": 1, "note": "At least 1 image. Cover image required for distribution."},
        "reading_level":     {"target": "Grade 7-9",
                              "note": "Simple language = higher read ratio"},
        "tags":              {"count": 5, "note": "Use all 5 allowed tags. First = most important."},
        "publish_timing_ist":["06:00", "07:00", "18:00", "19:00"],
        "best_days":         ["Tuesday", "Wednesday", "Thursday"],
    },
    "seo_rules": {
        "keyword_placement": [
            "In title (ideally first 3 words)",
            "In subtitle",
            "In first 100 words",
            "In at least 2 subheadings",
            "In last paragraph",
        ],
        "internal_links":    "Link to your own older relevant articles",
        "external_links":    "Link to authoritative sources (builds trust signal)",
    },
    "read_ratio_boosters": [
        "Start with a story or relatable problem",
        "Use bullet points and numbered lists",
        "Short paragraphs (2-3 sentences max)",
        "Add relevant images every 300 words",
        "Use subheadings as mini-hooks",
        "End each section with a bridge to next",
        "Strong conclusion with key takeaways",
    ],
    "highlight_triggers": [
        "Surprising statistics",
        "Counter-intuitive insights",
        "Actionable tips in one sentence",
        "Quotable lines ('The best tool is the one you actually use')",
    ],
    "killing_factors": [
        "Wall of text (no subheadings, no breaks)",
        "Clickbait title that article doesn't deliver on",
        "Publishing without cover image",
        "Ignoring SEO in title and subtitle",
        "First paragraph is boring/generic",
        "No call-to-action at end",
    ],
}


# ════════════════════════════════════════════════════════════
# QUALITY SCORER
# ════════════════════════════════════════════════════════════

@dataclass
class QualityScore:
    platform:    str
    total:       int                          # 0-100
    breakdown:   Dict[str, int] = field(default_factory=dict)
    passed:      List[str]      = field(default_factory=list)
    failed:      List[str]      = field(default_factory=list)
    warnings:    List[str]      = field(default_factory=list)
    suggestions: List[str]      = field(default_factory=list)
    grade:       str            = "F"

    def __post_init__(self):
        if   self.total >= 90: self.grade = "A+"
        elif self.total >= 80: self.grade = "A"
        elif self.total >= 70: self.grade = "B"
        elif self.total >= 60: self.grade = "C"
        elif self.total >= 40: self.grade = "D"
        else:                  self.grade = "F"


def score_linkedin_post(text: str) -> QualityScore:
    """LinkedIn post ko 0-100 score do."""
    score   = 0
    passed  = []
    failed  = []
    warnings= []
    sugg    = []
    breakdown = {}

    lines      = text.strip().split('\n')
    first_line = lines[0].strip().lower() if lines else ""
    char_count = len(text)
    has_question = '?' in text
    hashtag_count = text.count('#')
    has_external_link = any(x in text for x in ['http://', 'https://'])
    paragraph_count = len([l for l in text.split('\n\n') if l.strip()])
    word_count = len(text.split())

    # 1. HOOK (25 pts)
    hook_score = 0
    banned = [b.lower() for b in LINKEDIN_ALGO["hook_rules"]["banned_starts"]]
    if any(first_line.startswith(b) for b in banned):
        failed.append("❌ Weak hook — starts with banned phrase (I am excited / Happy to share etc.)")
        sugg.append("💡 Hook rewrite: Start with a bold stat, question, or contrarian statement")
    else:
        hook_score += 15
        passed.append("✅ Hook doesn't use banned opener")

    first_two = ' '.join(lines[:2])
    if len(first_two) <= 140:
        hook_score += 10
        passed.append("✅ Hook fits in preview (≤140 chars)")
    else:
        warnings.append("⚠️  Hook too long — may get cut in feed preview")
        hook_score += 5
    breakdown["Hook Quality"] = hook_score

    # 2. LENGTH (20 pts)
    length_score = 0
    r = LINKEDIN_ALGO["content_rules"]["optimal_length"]
    if r["min"] <= char_count <= r["max"]:
        length_score = 20
        passed.append(f"✅ Length optimal ({char_count} chars — sweet spot {r['min']}-{r['max']})")
    elif char_count < r["min"]:
        length_score = max(0, int(20 * char_count / r["min"]))
        warnings.append(f"⚠️  Too short ({char_count} chars) — more dwell time needed")
        sugg.append("💡 Add more value: a story, example, or 2 more bullet points")
    else:
        length_score = 12
        warnings.append(f"⚠️  Too long ({char_count} chars) — consider splitting")
    breakdown["Length"] = length_score

    # 3. READABILITY / WHITE SPACE (15 pts)
    read_score = 0
    empty_lines = text.count('\n\n')
    if empty_lines >= 3:
        read_score = 15
        passed.append("✅ Good use of white space / line breaks")
    elif empty_lines >= 1:
        read_score = 8
        warnings.append("⚠️  Add more line breaks — wall of text kills dwell time")
    else:
        failed.append("❌ No line breaks — very hard to read on mobile")
        sugg.append("💡 Break into 3-5 short paragraphs with blank lines between")
    breakdown["Readability"] = read_score

    # 4. ENGAGEMENT TRIGGER (20 pts)
    eng_score = 0
    if has_question:
        eng_score += 15
        passed.append("✅ Has question to drive comments")
    else:
        failed.append("❌ No question — comments will be low")
        sugg.append("💡 End with: 'What's your take on this?' or 'Which tool are you using?'")

    if paragraph_count >= 3:
        eng_score += 5
        passed.append("✅ Multiple paragraphs = good structure")
    breakdown["Engagement Triggers"] = eng_score

    # 5. HASHTAGS (10 pts)
    hash_score = 0
    h = LINKEDIN_ALGO["content_rules"]["hashtags"]
    if h["min"] <= hashtag_count <= h["max"]:
        hash_score = 10
        passed.append(f"✅ Hashtag count good ({hashtag_count})")
    elif hashtag_count > h["max"]:
        failed.append(f"❌ Too many hashtags ({hashtag_count}) — spam signal!")
        sugg.append(f"💡 Use max {h['max']} hashtags")
    else:
        hash_score = 5
        warnings.append(f"⚠️  Only {hashtag_count} hashtag(s) — add more for discoverability")
    breakdown["Hashtags"] = hash_score

    # 6. NO EXTERNAL LINKS (10 pts)
    link_score = 0
    if not has_external_link:
        link_score = 10
        passed.append("✅ No external link in post body (good for reach)")
    else:
        failed.append("❌ External link in post body cuts reach by 60%+!")
        sugg.append("💡 Move link to first comment — post it there after publishing")
    breakdown["No External Links"] = link_score

    # Total
    total = sum(breakdown.values())
    return QualityScore(
        platform="LinkedIn", total=total,
        breakdown=breakdown, passed=passed,
        failed=failed, warnings=warnings, suggestions=sugg
    )


def score_twitter_post(text: str, is_thread: bool = False) -> QualityScore:
    """Twitter/X post ko 0-100 score do."""
    score    = 0
    passed   = []
    failed   = []
    warnings = []
    sugg     = []
    breakdown = {}

    char_count    = len(text)
    hashtag_count = text.count('#')
    has_question  = '?' in text
    has_number    = any(c.isdigit() for c in text[:20])
    has_link      = 'http' in text
    word_count    = len(text.split())

    # 1. LENGTH (25 pts)
    len_score = 0
    if char_count > 280:
        failed.append(f"❌ Too long! {char_count} chars — Twitter limit is 280")
        sugg.append("💡 Cut to under 270 chars to leave room for link if needed")
    elif 71 <= char_count <= 140:
        len_score = 25
        passed.append(f"✅ Optimal length ({char_count} chars — sweet spot for engagement)")
    elif char_count <= 70:
        len_score = 18
        warnings.append(f"⚠️  Very short ({char_count} chars) — may lack context")
    else:
        len_score = 20
        passed.append(f"✅ Good length ({char_count} chars)")
    breakdown["Length"] = len_score

    # 2. HOOK POWER (25 pts)
    hook_score = 0
    first_words = text[:50].lower()
    strong_patterns = ["?", ":", "—", "%", "stop ", "most people", "unpopular",
                       "hot take", "nobody", "everyone", "secret", "mistake"]
    if any(p in first_words for p in strong_patterns):
        hook_score = 25
        passed.append("✅ Strong hook pattern detected")
    elif has_number:
        hook_score = 20
        passed.append("✅ Number in hook — good for CTR")
    else:
        hook_score = 10
        sugg.append("💡 Stronger hook: use %, contrarian statement, or question")
    breakdown["Hook Power"] = hook_score

    # 3. REPLY/BOOKMARK TRIGGERS (20 pts)
    trigger_score = 0
    if has_question:
        trigger_score += 12
        passed.append("✅ Has question — drives replies (top signal)")
    if any(w in text.lower() for w in ["save this", "bookmark", "what do you think",
                                        "agree?", "disagree?", "your thoughts"]):
        trigger_score += 8
        passed.append("✅ Has save/bookmark trigger")
    elif not has_question:
        sugg.append("💡 Add question or 'Save this for later' to drive replies/bookmarks")
        trigger_score = 5
    breakdown["Reply/Bookmark Triggers"] = trigger_score

    # 4. HASHTAGS (15 pts)
    hash_score = 0
    if hashtag_count == 0:
        hash_score = 8
        warnings.append("⚠️  No hashtags — small discoverability loss")
    elif hashtag_count <= 2:
        hash_score = 15
        passed.append(f"✅ Hashtag count perfect ({hashtag_count}) — 2024 algo prefers ≤2")
    else:
        hash_score = 5
        failed.append(f"❌ Too many hashtags ({hashtag_count}) — hurts reach on X in 2024")
        sugg.append("💡 Max 2 hashtags on Twitter/X")
    breakdown["Hashtags"] = hash_score

    # 5. THREAD INDICATOR (15 pts) - if thread
    thread_score = 0
    if is_thread:
        if '🧵' in text or 'thread' in text.lower():
            thread_score = 15
            passed.append("✅ Thread indicator present (🧵)")
        else:
            thread_score = 8
            sugg.append("💡 Add 🧵 to first tweet so people know it's a thread")
    else:
        thread_score = 15  # Single tweet — full marks
    breakdown["Format"] = thread_score

    total = sum(breakdown.values())
    return QualityScore(
        platform="Twitter/X", total=min(100, total),
        breakdown=breakdown, passed=passed,
        failed=failed, warnings=warnings, suggestions=sugg
    )


def score_medium_article(title: str, content: str, subtitle: str = "") -> QualityScore:
    """Medium article ko 0-100 score do."""
    passed   = []
    failed   = []
    warnings = []
    sugg     = []
    breakdown = {}

    word_count  = len(content.split())
    char_count  = len(content)
    has_subhead = content.count('##') >= 2 or content.count('\n\n') >= 4
    has_bullets = '•' in content or '- ' in content or content.count('\n-') > 1
    title_len   = len(title)
    first_150   = content[:600]
    has_question_in_hook = '?' in first_150
    has_cta     = any(w in content.lower() for w in
                      ["follow", "subscribe", "clap", "share", "newsletter"])

    # 1. TITLE SEO (20 pts)
    title_score = 0
    if title_len <= 60:
        title_score += 12
        passed.append(f"✅ Title length good ({title_len} chars ≤60)")
    else:
        warnings.append(f"⚠️  Title too long ({title_len} chars) — gets cut in search")
        sugg.append("💡 Shorten title to under 60 chars for better SEO")
        title_score += 6

    power_words = ["how", "why", "what", "best", "guide", "secret",
                   "mistake", "truth", "simple", "free", "ai", "tool"]
    if any(w in title.lower() for w in power_words):
        title_score += 8
        passed.append("✅ Power word in title — better CTR in search")
    else:
        sugg.append("💡 Add power word to title: How/Why/Best/Guide/Secret")
        title_score += 3
    breakdown["Title SEO"] = title_score

    # 2. READ RATIO FACTORS (25 pts)
    read_score = 0
    r = MEDIUM_ALGO["content_rules"]

    if r["optimal_length"]["min"] <= word_count <= r["optimal_length"]["max"]:
        read_score += 15
        passed.append(f"✅ Word count optimal ({word_count} words)")
    elif word_count < r["optimal_length"]["min"]:
        read_score += 7
        warnings.append(f"⚠️  Too short ({word_count} words) — min {r['optimal_length']['min']} for Partner Program")
        sugg.append("💡 Expand with more examples, case studies, or step-by-step guide")
    else:
        read_score += 10
        warnings.append(f"⚠️  Long article ({word_count} words) — ensure read ratio stays high")

    if has_subhead:
        read_score += 10
        passed.append("✅ Has subheadings — improves skim-ability + read ratio")
    else:
        failed.append("❌ No subheadings — readers will bounce (hurts read ratio)")
        sugg.append("💡 Add ## subheadings every 150-200 words")
    breakdown["Read Ratio"] = read_score

    # 3. HOOK / FIRST PARAGRAPH (20 pts)
    hook_score = 0
    boring_starts = ["in today's", "in this article", "welcome to", "i want to",
                     "this article", "in recent years", "as we all know"]
    first_para_lower = first_150.lower()

    if any(s in first_para_lower for s in boring_starts):
        failed.append("❌ Boring opening — 'In today's world...' type openers kill read ratio")
        sugg.append("💡 Start with: a surprising stat, a story, or a bold claim")
        hook_score = 5
    else:
        hook_score += 12
        passed.append("✅ Opening doesn't use generic boring starter")

    if has_question_in_hook:
        hook_score += 8
        passed.append("✅ Question in opening — hooks readers in")
    else:
        sugg.append("💡 Consider opening with a question to hook readers")
        hook_score += 4
    breakdown["Hook / Opening"] = hook_score

    # 4. HIGHLIGHT TRIGGERS (15 pts)
    highlight_score = 0
    stat_present = any(c.isdigit() for c in content[:1000])
    quotable = len([s for s in content.split('.') if 8 < len(s.split()) < 15]) >= 3

    if stat_present:
        highlight_score += 8
        passed.append("✅ Statistics/numbers present — good for highlights")
    else:
        sugg.append("💡 Add specific stats or numbers — readers highlight them")
        highlight_score += 3

    if quotable:
        highlight_score += 7
        passed.append("✅ Has short quotable sentences — good for highlights")
    else:
        sugg.append("💡 Add 2-3 short punchy sentences readers would want to highlight")
        highlight_score += 3
    breakdown["Highlight Triggers"] = highlight_score

    # 5. CTA + FOLLOW (10 pts)
    cta_score = 0
    if has_cta:
        cta_score = 10
        passed.append("✅ Has CTA (follow/subscribe/clap)")
    else:
        failed.append("❌ No CTA — missing follow signal")
        sugg.append("💡 End with: 'Follow TechNova World for daily AI insights'")
    breakdown["CTA"] = cta_score

    # 6. SUBTITLE (10 pts)
    sub_score = 0
    if subtitle and len(subtitle) >= 20:
        sub_score = 10
        passed.append(f"✅ Subtitle present ({len(subtitle)} chars)")
    else:
        failed.append("❌ Missing subtitle — appears in search results!")
        sugg.append("💡 Write a subtitle that includes your target keyword")
    breakdown["Subtitle SEO"] = sub_score

    total = sum(breakdown.values())
    return QualityScore(
        platform="Medium", total=min(100, total),
        breakdown=breakdown, passed=passed,
        failed=failed, warnings=warnings, suggestions=sugg
    )


# ════════════════════════════════════════════════════════════
# ANTI-SPAM VALIDATOR
# ════════════════════════════════════════════════════════════

SPAM_PATTERNS = [
    "follow for follow", "f4f", "like for like", "l4l",
    "dm me", "check bio", "link in bio", "100% free",
    "make money fast", "passive income guaranteed",
    "click here now", "limited time", "act now",
    "buy now", "discount code", "promo code",
    "repost this", "tag 5 friends", "share to win",
    "giveaway", "contest", "winner",
]

FAKE_ENGAGEMENT_PHRASES = [
    "agree?", "smash that like", "hit the like button",
    "share if you agree", "rt if you agree", "retweet if",
    "tag someone who", "comment yes if",
    "drop a 🔥 if", "type yes if",
]


def check_spam(text: str) -> Dict:
    """
    Spam aur fake engagement patterns detect karo.

    Returns:
        Dict with is_spam, spam_signals, fake_engagement_signals, safe_to_post
    """
    text_lower = text.lower()

    spam_found = [p for p in SPAM_PATTERNS if p in text_lower]
    fake_found = [p for p in FAKE_ENGAGEMENT_PHRASES if p in text_lower]

    # Repetition check
    words      = text_lower.split()
    word_freq  = {}
    for w in words:
        if len(w) > 4:
            word_freq[w] = word_freq.get(w, 0) + 1
    repeated = {w: c for w, c in word_freq.items() if c >= 4}

    # Excessive caps
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    excessive_caps = caps_ratio > 0.3

    # Too many emojis
    import unicodedata
    emoji_count = sum(1 for c in text
                      if unicodedata.category(c) in ("So", "Sm") or ord(c) > 127000)
    too_many_emojis = emoji_count > 8

    is_spam        = bool(spam_found or repeated)
    has_fake_eng   = bool(fake_found)
    safe_to_post   = not is_spam and not excessive_caps

    return {
        "safe_to_post":           safe_to_post,
        "is_spam":                is_spam,
        "has_fake_engagement":    has_fake_eng,
        "spam_signals":           spam_found,
        "fake_engagement_signals":fake_found,
        "repeated_words":         repeated,
        "excessive_caps":         excessive_caps,
        "emoji_count":            emoji_count,
        "too_many_emojis":        too_many_emojis,
    }


# ════════════════════════════════════════════════════════════
# VALUE CHECKER — Does content give real value?
# ════════════════════════════════════════════════════════════

VALUE_INDICATORS = {
    "high_value": [
        "actionable tip", "step by step", "how to", "example",
        "case study", "data shows", "research", "study found",
        "practical", "you can", "try this", "here's how",
        "save time", "increase", "improve", "learn",
    ],
    "low_value": [
        "follow my journey", "excited to share", "blessed",
        "grateful", "honoured", "proud of myself",
        "just wanted to say", "thoughts?", "what do you think",
    ],
}

def check_value(text: str) -> Dict:
    """Content mein real value hai ya nahi check karo."""
    text_lower = text.lower()

    high = [v for v in VALUE_INDICATORS["high_value"] if v in text_lower]
    low  = [v for v in VALUE_INDICATORS["low_value"]  if v in text_lower]

    value_score = min(100, len(high) * 20 - len(low) * 10)
    value_score = max(0, value_score)

    has_specific_number = any(c.isdigit() for c in text)
    has_example         = any(w in text_lower for w in ["for example", "e.g.", "like ", "such as", "e.g"])
    has_takeaway        = any(w in text_lower for w in ["takeaway", "key point", "remember", "summary"])

    return {
        "value_score":     value_score,
        "high_value_hits": high,
        "low_value_hits":  low,
        "has_numbers":     has_specific_number,
        "has_examples":    has_example,
        "has_takeaway":    has_takeaway,
        "verdict": (
            "🟢 High Value"   if value_score >= 60 else
            "🟡 Medium Value" if value_score >= 30 else
            "🔴 Low Value — rewrite!"
        ),
    }


# ════════════════════════════════════════════════════════════
# PROMPT BUILDER — algo-aware prompts
# ════════════════════════════════════════════════════════════

def build_linkedin_prompt(topic: str, brand: str, audience: str) -> str:
    rules = LINKEDIN_ALGO
    hooks = "\n".join(f"  - {p}" for p in rules["hook_rules"]["strong_patterns"])
    banned = ", ".join(rules["hook_rules"]["banned_starts"][:4])
    questions = "\n".join(f"  - {q}" for q in rules["comment_triggers"]["good_questions"][:3])

    return f"""Write a LinkedIn post for {brand} about: "{topic}"
Audience: {audience}

ALGORITHM RULES (follow strictly for maximum reach):

1. HOOK (first 2 lines — shown before 'see more'):
   - MAX 140 chars combined
   - NEVER start with: {banned}
   - Use one of these proven patterns:
{hooks}

2. BODY (dwell time = #1 signal):
   - Total 900-1300 characters
   - Line break every 2-3 lines (mobile readability)
   - One clear insight or story
   - NO external links (kills reach by 60%+)

3. ENGAGEMENT TRIGGER:
   - End with ONE specific question:
{questions}

4. HASHTAGS (last line only):
   - Exactly 4-5 hashtags
   - Must include: #AI #ArtificialIntelligence
   - No hashtags in body text

Return ONLY the post. No explanations."""


def build_twitter_prompt(topic: str, brand: str, audience: str,
                          post_type: str = "single") -> str:
    patterns = "\n".join(f"  - {k}: {v}"
                         for k, v in list(TWITTER_ALGO["viral_patterns"].items())[:5])

    if post_type == "thread":
        return f"""Write a Twitter/X thread for {brand} about: "{topic}"
Audience: {audience}

ALGORITHM RULES for viral threads:
- Tweet 1: Hook with 🧵 — makes people want to read all. Under 200 chars.
- Tweets 2-7: One insight each. Short. Punchy. Numbered X/8.
- Tweet 8: Summary + "Follow @TechNovaWorld for more"
- Max 270 chars per tweet
- MAX 2 hashtags total (only in tweet 1)
- NO "RT if you agree" or "Like if" phrases (penalized)
- Add question in tweet 5 or 6 to drive replies

Return tweets numbered: 1/8 text, 2/8 text, etc."""

    else:
        return f"""Write 5 standalone Twitter/X posts for {brand} about: "{topic}"
Audience: {audience}

ALGORITHM RULES for maximum replies + bookmarks:
{patterns}

Rules:
- Each post MAX 270 characters
- MAX 2 hashtags per post
- Post 1: Breaking news / hook angle
- Post 2: Surprising insight ("Most people don't know...")
- Post 3: Question (drives replies = top algo signal)
- Post 4: Practical tip (drives bookmarks = 2nd signal)
- Post 5: CTA (follow @TechNovaWorld)

Number them: 1. 2. 3. etc.
NO "RT if you agree" phrases."""


def build_medium_prompt(topic: str, brand: str, audience: str) -> str:
    seo_rules = "\n".join(f"  - {r}" for r in MEDIUM_ALGO["seo_rules"]["keyword_placement"])
    boosters  = "\n".join(f"  - {b}" for b in MEDIUM_ALGO["read_ratio_boosters"][:4])

    return f"""Write a complete Medium article for {brand} about: "{topic}"
Audience: {audience}

ALGORITHM RULES for maximum read ratio + distribution:

TITLE (60 chars max):
  - Include power word: How/Why/Best/Guide/Secret/Simple
  - Include primary keyword near start

SUBTITLE (under 100 chars):
  - Include secondary keyword
  - Expand on title promise

ARTICLE BODY (600-1000 words):
Read Ratio Boosters:
{boosters}

SEO Keyword Placement:
{seo_rules}

Structure:
  - Opening: story, stat, or bold claim (NO "In today's world...")
  - Subheadings every 150-200 words (##)
  - Short paragraphs: 2-3 sentences max
  - Bullet points where appropriate
  - End: key takeaways + "Follow TechNova World for daily AI insights"

Highlight Triggers (readers highlight these):
  - Surprising statistics
  - Short punchy sentences under 12 words
  - Counter-intuitive insights

Return in format:
TITLE: [title]
SUBTITLE: [subtitle]
---
[article body]
---
TAGS: tag1, tag2, tag3, tag4, tag5"""


# ════════════════════════════════════════════════════════════
# CONVENIENCE EXPORTS
# ════════════════════════════════════════════════════════════

def get_algo_rules(platform: str) -> Dict:
    """Platform ke algo rules return karo."""
    return {
        "linkedin": LINKEDIN_ALGO,
        "twitter":  TWITTER_ALGO,
        "medium":   MEDIUM_ALGO,
    }.get(platform.lower(), {})


def score_content(text: str, platform: str, **kwargs) -> QualityScore:
    """Universal scorer — platform detect karke score karo."""
    p = platform.lower()
    if p == "linkedin":
        return score_linkedin_post(text)
    elif p in ("twitter", "twitter_single", "tweet"):
        return score_twitter_post(text, is_thread=kwargs.get("is_thread", False))
    elif p == "medium":
        return score_medium_article(
            kwargs.get("title", ""), text,
            subtitle=kwargs.get("subtitle", "")
        )
    else:
        raise ValueError(f"Unknown platform: {platform}")


def print_score_report(qs: QualityScore):
    """Quality score report print karo."""
    grade_colors = {"A+": "🟢", "A": "🟢", "B": "🟡", "C": "🟡", "D": "🔴", "F": "🔴"}
    icon = grade_colors.get(qs.grade, "⚪")

    print(f"\n{'='*55}")
    print(f"  📊 QUALITY REPORT — {qs.platform}")
    print(f"{'='*55}")
    print(f"  {icon} Score: {qs.total}/100  Grade: {qs.grade}")
    print(f"\n  Breakdown:")
    for k, v in qs.breakdown.items():
        bar = "█" * (v // 5) + "░" * ((20 - v // 5))
        print(f"  {k:<22} {bar} {v:3d}")

    if qs.passed:
        print(f"\n  ✅ PASSED ({len(qs.passed)}):")
        for p in qs.passed:
            print(f"     {p}")

    if qs.failed:
        print(f"\n  ❌ FAILED ({len(qs.failed)}):")
        for f in qs.failed:
            print(f"     {f}")

    if qs.warnings:
        print(f"\n  ⚠️  WARNINGS ({len(qs.warnings)}):")
        for w in qs.warnings:
            print(f"     {w}")

    if qs.suggestions:
        print(f"\n  💡 SUGGESTIONS:")
        for s in qs.suggestions:
            print(f"     {s}")
    print(f"{'='*55}")
