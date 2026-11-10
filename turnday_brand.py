from helpers import L, LM, opt, env_names

Q = [
    {"id": "listings", "type": "choice", "prompt": "How many short-term rental listings do you run?",
     "options": [opt("1", "1 listing", "Just getting systems in place"), opt("2_3", "2–3 listings"), opt("4_10", "4–10 listings"), opt("cohost", "I co-host for someone else")]},
    {"id": "property", "type": "choice", "prompt": "What kind of place is it (your main listing)?",
     "options": [opt("room", "Private room in my home"), opt("apt", "Apartment / condo"), opt("house", "Whole house"), opt("unique", "Cabin / tiny home / unique stay")]},
    {"id": "guests", "type": "choice", "prompt": "Who books you most often?",
     "options": [opt("couples", "Couples & weekenders"), opt("families", "Families"), opt("business", "Work travelers"), opt("groups", "Friend groups"), opt("mixed", "A real mix")]},
    {"id": "cleaning", "type": "choice", "prompt": "Who handles turnovers today?",
     "options": [opt("me", "I clean myself"), opt("one", "One regular cleaner"), opt("team", "A cleaning team / company"), opt("none", "No reliable setup yet")]},
    {"id": "pain", "type": "choice", "prompt": "What went wrong most in the last few months?",
     "options": [opt("late_clean", "Late or rushed cleans"), opt("cleanliness", "Cleanliness comments in reviews"), opt("slow_reply", "Slow guest replies"), opt("restock", "Running out of supplies"), opt("checkin", "Check-in confusion")]},
    {"id": "messaging", "type": "choice", "prompt": "How do you send guest messages now?",
     "options": [opt("manual", "Typed by hand each time"), opt("saved", "Saved replies I paste"), opt("scheduled", "Scheduled messages in the platform"), opt("tool", "A separate messaging tool")]},
    {"id": "tone", "type": "choice", "prompt": "What tone should your guest messages have?",
     "options": [opt("warm", "Warm & personal"), opt("crisp", "Crisp & efficient"), opt("boutique", "Boutique-hotel polished"), opt("playful", "Relaxed & playful")]},
    {"id": "hours", "type": "choice", "prompt": "How many hours a week can you give to host admin?",
     "options": [opt("1", "About 1 hour"), opt("3", "2–4 hours"), opt("6", "5–8 hours"), opt("10", "More than 8 hours")]},
    {"id": "season", "type": "choice", "prompt": "What season are you heading into?",
     "options": [opt("peak", "Peak season"), opt("shoulder", "Shoulder season"), opt("slow", "Slow season"), opt("holiday", "Holiday rush")]},
    {"id": "area", "type": "text", "prompt": "What city or region is your listing in?", "placeholder": "e.g. Lake Tahoe, CA", "help": "Used to remind you to check your local short-term rental rules — we don’t give legal advice."},
]


def plan(a):
    n = {"1": 1, "2_3": 3, "4_10": 6, "cohost": 2}.get(a.get("listings"), 1)
    prop = L(Q[1]["options"], a.get("property"))
    guests = L(Q[2]["options"], a.get("guests"))
    pain = L(Q[4]["options"], a.get("pain"))
    tone = L(Q[6]["options"], a.get("tone"))
    area = a.get("area") or "your area"
    clean_line = {
        "me": "Use a 12-step self-clean checklist and time each turnover once to find the slow step.",
        "one": "Send your cleaner the shared checklist and ask for 4 photos after each clean (beds, bath, kitchen, entry).",
        "team": "Agree on one checklist version and a photo-proof standard with the team lead.",
        "none": "Write the checklist first, then use it to brief any cleaner you trial.",
    }.get(a.get("cleaning"), "Write one checklist everyone follows.")
    fix = {
        "late_clean": "Block a buffer on same-day turnovers and confirm the cleaner the evening before.",
        "cleanliness": "Add a ‘guest’s-eye’ final walk: hair check in bath, under-bed sweep, fridge wipe.",
        "slow_reply": "Prepare 8 saved replies for the questions guests ask most (wifi, parking, check-in, late checkout).",
        "restock": "Keep a par-level restock list and a backup bin of 2 turnovers’ worth of supplies.",
        "checkin": "Rewrite check-in steps as 5 numbered lines with one photo per step.",
    }.get(a.get("pain"), "")
    return {
        "title": f"Turnday host ops plan — {prop} in {area}",
        "summary": f"Built for {n} listing(s), mostly {guests.lower()}, with your biggest pain being {pain.lower()}. Messages written in a {tone.lower()} tone. This is an operations checklist — not a promise of occupancy, revenue, ratings, or Superhost status.",
        "preview_sections": [
            {"title": "Fix this first", "bullets": [fix, clean_line, "Do one dry-run turnover with the checklist before your next guest arrives."]},
            {"title": "Guest message calendar (unlocked)", "bullets": [
                f"Booking confirmed: thank-you + what to expect ({tone.lower()}).",
                "3 days before: directions, parking, house-rule highlights.",
                "Check-in day: numbered entry steps + wifi.",
                "Morning after arrival: quick ‘anything missing?’ check.",
                "Checkout eve: short checkout list (no chore lists that feel unfair).",
            ]},
            {"title": "Local rules reminder", "body": f"Short-term rental permits, taxes, and occupancy rules vary by city. Check the official rules for {area} yourself — Turnday doesn’t provide legal or tax advice."},
        ],
        "locked_sections": [
            {"title": "Full turnover checklist by room", "teaser": "Room-by-room steps with photo-proof points for your cleaner."},
            {"title": "Restock par sheet", "teaser": "Quantities per stay length and guest count."},
            {"title": "Seasonal message pack", "teaser": "Weather, holiday, and slow-season templates."},
            {"title": "Weekly 20-minute host review", "teaser": "Process check: replies, cleans, issues — no vanity metrics."},
        ],
    }


BRAND = {
    "name": "Turnday", "slug": "turnday", "port": 5105,
    "tagline": "A turnover-and-messaging playbook for independent short-term rental hosts.",
    "eyebrow": "For 1–10 listing hosts",
    "hero_title": "Calmer turnovers. Faster replies. One host playbook.",
    "hero_lede": "Answer 10 quick questions about your listing, cleaner setup, and guests. Turnday builds a turnover checklist and a guest-message calendar that fits the hours you actually have.",
    "cta_primary": "Build my host playbook", "cta_short": "Start quiz",
    "cta_band_title": "Your next checkout is a chance to reset.",
    "cta_band_text": "Get a checklist your cleaner can follow and messages guests actually read.",
    "honesty_line": "Operations checklists only. No occupancy, revenue, rating, or Superhost guarantees.",
    "audience_line": "Independent hosts and co-hosts running 1–10 listings without a full property-management system.",
    "personas": [
        {"title": "Side-gig host", "text": "One listing, a day job, and turnovers that eat Sunday."},
        {"title": "Growing host", "text": "2–5 listings where every process now lives in your head."},
        {"title": "Co-host", "text": "You run someone else’s place and need repeatable standards."},
    ],
    "journey": [
        {"stage": "Booking", "pain": "Guests ask the same five questions.", "fix": "Saved replies and a confirmation message in your tone."},
        {"stage": "Pre-arrival", "pain": "Check-in confusion and late-night calls.", "fix": "Numbered entry steps with one photo each."},
        {"stage": "Stay", "pain": "Small problems become bad reviews.", "fix": "A morning-after check-in message."},
        {"stage": "Turnover", "pain": "Rushed cleans and missing supplies.", "fix": "Room-by-room checklist and restock pars."},
    ],
    "how_steps": [
        {"title": "Quiz your listing", "text": "Property, guests, cleaner setup, and your hours."},
        {"title": "See your playbook preview", "text": "Top fix plus the guest message calendar."},
        {"title": "Start your plan", "text": "Enter your email, then complete checkout on Gumroad."},
    ],
    "features": [
        {"title": "Turnover checklist", "text": "Room-by-room, with photo-proof points."},
        {"title": "Message calendar", "text": "Booking → check-in → checkout in your tone."},
        {"title": "Restock pars", "text": "Never run out of coffee or toilet paper again."},
        {"title": "Seasonal packs", "text": "Subscription: new templates as seasons change."},
    ],
    "sample_peek": ["Same-day turnover buffer rule", "5-step numbered check-in", "Cleaner photo-proof standard", "Weekly 20-minute host review"],
    "trust_points": [
        {"title": "Not affiliated with Airbnb or Vrbo", "text": "Use each platform’s own tools and follow their rules."},
        {"title": "No ranking promises", "text": "We help you run cleaner operations — results vary."},
        {"title": "Local rules are yours to check", "text": "We remind you; we don’t give legal advice."},
    ],
    "faq": [
        {"q": "Does Turnday connect to my Airbnb account?", "a": "No. Turnday is a plan and template library. You paste messages into your platform yourself."},
        {"q": "Will this get me Superhost?", "a": "We don’t promise ratings or status. The plan focuses on the operations guests notice."},
        {"q": "Is pricing advice included?", "a": "Only general seasonal reminders — not dynamic pricing or financial advice."},
        {"q": "How does billing work?", "a": "Choose Monthly or Quarterly, save your email, then complete payment on Gumroad. Renews automatically. Cancel anytime from your Gumroad library."},
    ],
    "pricing": [
        {"id": "monthly", "name": "Monthly", "price": "$24", "period": "/ month",
             "intro": "$24", "renewal": "$24 / month", "renewal_note": "Renews automatically. Cancel anytime from your Gumroad library.",
             "includes": ['Turnover checklist', 'Guest message calendar', 'Restock par sheet']},
        {"id": "quarterly", "name": "Quarterly", "price": "$59", "period": "every 3 months",
             "intro": "$59", "renewal": "$59 every 3 months", "renewal_note": "Renews automatically. Cancel anytime from your Gumroad library.", "featured": True,
             "includes": ['Everything in Monthly', 'Seasonal message packs', 'Multi-listing module']},
    ],
    "checkout_url": "https://solvfix.gumroad.com/l/gbzwxh",
    "disclaimer_short": "Operations education only. Not affiliated with Airbnb/Vrbo. No occupancy, revenue, or rating guarantees. Not legal or tax advice.",
    "disclaimer_long": "Turnday provides general hosting operations checklists and message templates. It is not affiliated with Airbnb, Vrbo, or any booking platform. It does not guarantee bookings, revenue, reviews, or platform status, and it is not legal, tax, or insurance advice. Short-term rental rules vary by location; check official local requirements. Payments are processed by Gumroad, not on this site.",
    "font_url": "https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700&family=Inter:wght@400;500;600&display=swap",
    "fonts": ("Outfit", "Inter"),
    "questions": Q, "generate_plan": plan,
    "voice": "Calm, practical, hospitable. Like an experienced co-host leaving you a tidy note.",
    "palette": {"Background": "#F5F8FB", "Alt": "#E9EFF5", "Card": "#FFFFFF", "Ink": "#13263A", "Muted": "#5B6B7C", "Accent (coastal blue)": "#2563A8", "Accent hover": "#1C4C82", "Highlight (sunrise)": "#F4A259"},
    "logo_svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none"><rect width="64" height="64" rx="14" fill="#2563A8"/><path d="M14 34 32 18l18 16" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 31v15h24V31" stroke="#FFFFFF" stroke-width="4" stroke-linejoin="round"/><path d="M27 39.5l3.5 3.5 7-7" stroke="#F4A259" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "css_vars": """
  --bg:#F5F8FB;--bg-alt:#E9EFF5;--card:#FFFFFF;--ink:#13263A;--muted:#5B6B7C;--line:#D6E0EA;
  --accent:#2563A8;--accent-2:#1C4C82;--on-accent:#FFFFFF;--hi:#F4A259;--radius:16px;
  --font-display:'Outfit', system-ui, sans-serif;--font-body:'Inter', system-ui, sans-serif;
  --shadow-card:0 18px 40px rgba(19,38,58,.08);--shadow-btn:0 8px 20px rgba(37,99,168,.25);
  --cta-band-bg:#13263A;--cta-band-ink:#F5F8FB;--cta-band-btn:#F4A259;--cta-band-btn-ink:#13263A;--tracking:-0.02em;
""",
    "personality": "background:radial-gradient(900px 420px at 85% -10%, #FDE3C8 0%, transparent 55%), linear-gradient(180deg,#E6F0FA 0%, var(--bg) 60%);",
    "extra_css": ".journey-card{border-top:4px solid var(--hi)}",
    "dos": ["Write like a host who has done 500 turnovers.", "Mention the platform’s own tools when relevant."],
    "donts": ["Imply affiliation with Airbnb or Vrbo.", "Promise bookings, nightly-rate gains, or Superhost."],
}
BRAND.update(env_names("turnday"))
