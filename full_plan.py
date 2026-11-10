"""Full (paid) plan sections for every quiz-plan site.

`full_sections(slug, answers, plan)` returns the sections that replace the
locked teasers once a buyer unlocks with their Gumroad license key. Content is
rule-based, educational, and makes no promises of results.
The same file ships in every repo; each app only calls its own slug.
"""
from __future__ import annotations

from typing import Any, Callable


def _titles(plan: dict, defaults: list[str]) -> list[str]:
    locked = plan.get("locked_sections") or []
    return [(locked[i].get("title") if i < len(locked) else None) or d for i, d in enumerate(defaults)]


def _sec(title: str, bullets: list[str], body: str = "") -> dict:
    d: dict[str, Any] = {"title": title, "bullets": bullets}
    if body:
        d["body"] = body
    return d


def _list(v) -> list:
    if not v:
        return []
    return v if isinstance(v, list) else [v]


def _days(start: int, end: int, cycle: list[str], prefix: str = "Day") -> list[str]:
    return [f"{prefix} {d}: {cycle[(d - start) % len(cycle)]}" for d in range(start, end + 1)]


# ---------------------------------------------------------------- ShelfSpeak
def shelfspeak(a, plan):
    t = _titles(plan, ["Weeks 2–4 full calendar", "Photo & reel shot list", "Weekly reflection prompts", "Next-month refresh pack"])
    offer = a.get("offer") or "your main offer"
    city = a.get("city") or "your area"
    per_week = {"1": 1, "2": 3, "4": 4, "daily": 6}.get(a.get("capacity"), 3)
    angles = [
        f"Behind the scenes: show one step of how {offer} gets done",
        "Customer question answered in plain words (no names without permission)",
        f"Local nod: something you love about {city}",
        f"Offer explainer: who {offer} is for and what to expect",
        "Team or owner intro: one photo, three sentences",
        "Myth vs. fact about your trade",
        "Simple how-to tip people can use today",
        "Soft call to action: how to book, visit, or ask a question",
    ]
    cal = []
    day = 8
    i = 0
    for week in (2, 3, 4):
        for _ in range(per_week):
            cal.append(f"Week {week} · post {(_ + 1)}: {angles[i % len(angles)]}")
            i += 1
        day += 7
    assets = a.get("assets")
    shots = {
        "phone": ["Hands at work, close-up, by a window", "Wide shot of the space when it’s tidy", "Product or result on a plain background", "Owner portrait in natural light"],
        "phone_video": ["7-second process clip (start → finish)", "Talking-head tip, one take, under 30 seconds", "Slow pan of the space at opening", "Before/after split (only with customer permission)"],
        "pro": ["Pick 12 pro photos and give each one a caption idea", "Re-crop pro shots to 4:5 and 9:16", "Add one phone ‘real moment’ per week so the feed feels current", "Refresh your profile photo and cover"],
        "none": ["Start with three phone photos this week: space, hands at work, the sign out front", "Shoot in daylight, no flash, phone wiped clean", "Take each shot vertical and horizontal", "Make a ‘photo day’ every other week"],
    }.get(assets, ["Hands at work", "Space at opening", "Result on a plain background", "Owner portrait"])
    return [
        _sec(t[0], cal + ["Batch captions on one day; schedule or paste the rest of the week.", "If a week gets busy, post the two strongest ideas and skip the rest — consistency beats volume."]),
        _sec(t[1], shots + ["Keep a ‘shots I need’ note on your phone and tick items off weekly.", "Always ask before posting a customer’s face or work."]),
        _sec(t[2], [
            "How many posts did I publish vs. plan? What got in the way?",
            "Which post got real replies or questions (not just likes)? Why might that be?",
            "Did anyone mention a post in person or when booking?",
            "What is one idea I want to repeat next week, and one I’ll drop?",
            "Time check: how long did batching take? Can I trim it?",
            "These are process notes — reach and bookings vary and aren’t promised.",
        ]),
        _sec(t[3], [
            "Seasonal swap: replace one weekly angle with a seasonal or holiday tie-in for your area.",
            f"New-angle month: pick a theme around {offer} (for example ‘care tips month’) and give each week a sub-topic.",
            "Re-share your three best posts from this month with a fresh caption.",
            "Update your bio, link, and hours before the new month starts.",
            "Retake the quiz any time your capacity or goal changes; your plan rebuilds to match.",
        ]),
    ]


# ---------------------------------------------------------------- SignMatch
def signmatch(a, plan):
    t = _titles(plan, ["Days 8–30 checklist", "Review-request scripts", "Monthly re-check ritual", "SolvFix re-scan prompts"])
    dirs = _list(a.get("dirs")) or ["google"]
    names = {"google": "Google Business Profile", "yelp": "Yelp", "apple": "Apple Business Connect", "facebook": "Facebook page", "bing": "Bing Places", "industry": "your industry directory"}
    steps = []
    d = 8
    for key in dirs:
        n = names.get(key, key)
        steps.append(f"Day {d}: {n} — match name, address, phone, and hours exactly to your master record")
        steps.append(f"Day {d + 1}: {n} — update categories, website link, and add 3 current photos")
        d += 2
    steps += [
        f"Day {d}: Search your business name + city; list every page that shows old details",
        f"Day {d + 1}: Request fixes or removal for duplicates through each site’s own process",
        f"Day {d + 2}: Check your website footer and contact page match the master record",
        f"Day {d + 3}: Update any social bios and booking tools with the same details",
        "Days after that: one 20-minute block a week to follow up on pending edits",
        "Day 30: Re-check every listing above and note what changed",
    ]
    return [
        _sec(t[0], steps),
        _sec(t[1], [
            "In person: “If you were happy with today, a short review on Google really helps a small shop like ours.”",
            "Text/email: “Thanks for visiting! If you have a minute, here’s the link to leave a review: [link]. Honest feedback helps us improve.”",
            "Reply to every review — thank positive ones, and answer critical ones calmly with an offer to talk offline.",
            "Ask everyone the same way; don’t only ask happy customers (no review gating).",
            "Never offer discounts or gifts for reviews, and never write or buy reviews.",
        ]),
        _sec(t[2], [
            "First Monday of each month, 30 minutes: open each listing and compare to your master record.",
            "Before holidays: set special hours everywhere at least a week ahead.",
            "After any move, phone change, or rebrand: update all listings the same day.",
            "Check for new suggested edits from the public and accept or reject them.",
            "Add one fresh photo to your main profile each month.",
        ]),
        _sec(t[3], [
            "Re-run the free SolvFix exposure scan after your Day 30 check, then monthly.",
            "Compare: how many listings show the exact same name, address, and phone as last time?",
            "Note any new duplicates or wrong numbers and add them to next week’s checklist.",
            "Results vary by platform; this tracks consistency, not rankings.",
        ]),
    ]


# ---------------------------------------------------------------- CueTrail
def cuetrail(a, plan):
    t = _titles(plan, ["Days 4–30 protocol", "Troubleshooting cards", "Equipment checklist", "Week 5+ modules"])
    dog = a.get("dog_name") or "your dog"
    mins = a.get("minutes", "10")
    issues = _list(a.get("issues")) or ["come"]
    drills = {
        "potty": "Potty routine: out after waking, eating, and play; reward within 2 seconds outside",
        "bite": "Mouthing: trade for a toy; pause play calmly if teeth touch skin",
        "pull": "Loose leash: stop when the leash tightens, reward at your side",
        "bark": "Barking: note the trigger, reward quiet moments, add distance from the trigger",
        "come": "Recall: say the name + ‘come’ once, reward big, practice indoors first",
        "crate": "Crate: feed meals in the crate, short door-closed periods, build slowly",
        "jump": "Jumping: greet only when four paws are on the floor; teach ‘sit’ for hellos",
    }
    cyc = [drills.get(i, drills["come"]) for i in issues] + ["Name game + eye contact, 5 reps", "Settle on a mat for 2–5 minutes", "Rest day: easy walk and sniffing"]
    days = _days(4, 30, cyc)
    return [
        _sec(t[0], [f"Sessions: about {mins} minutes a day for {dog}, split into short blocks."] + days + ["Every 7 days, make one drill slightly harder (more distance, duration, or distraction) only if the last week went well."]),
        _sec(t[1], [
            "If your dog ignores a cue → go back to an easier, quieter spot and higher-value treats.",
            "If your dog seems stressed (lip licking, yawning, tucked tail) → stop, add distance, end on an easy win.",
            "If progress stalls for a week → shorten sessions and practice at a different time of day.",
            "If accidents happen indoors → clean with an enzyme cleaner; don’t scold; take out more often.",
            "Escalate: any growling, snapping, or biting → pause and contact a certified behavior professional.",
            "Escalate: sudden behavior change, pain, or limping → see your vet first.",
        ]),
        _sec(t[2], [
            "Flat collar or well-fitted harness with ID tag",
            "6-foot standard leash (avoid retractable leashes for training)",
            "Treat pouch and small, soft treats",
            "A mat or bed for settle work",
            "Appropriately sized crate (only if using crate training)",
            "Chew toys and a puzzle feeder",
            "Avoid prong, choke, or shock collars — this plan uses reward-based methods only.",
        ]),
        _sec(t[3], [
            "Week 5: add real-world distractions — practice in a quiet park corner.",
            "Week 6: ‘Leave it’ and ‘drop it’ with toys and food.",
            "Week 7: duration ‘stay’ with you stepping out of sight briefly.",
            "Week 8: polite greetings with calm visitors.",
            "Retake the quiz when your goals change and your plan rebuilds.",
            "General education only — not a substitute for a vet or certified trainer.",
        ]),
    ]


# ---------------------------------------------------------------- ReplyPath
def replypath(a, plan):
    t = _titles(plan, ["Weeks 2–4 calendar", "Message swipe file", "Proposal outline", "Weekly review ritual"])
    cap = int(a.get("capacity") or 5)
    ideal = a.get("ideal") or "your ideal client"
    offer = a.get("offer") or "your offer"
    tone = a.get("tone", "warm")
    cyc = [
        f"Research 5 {ideal} prospects; note one specific detail about each",
        f"Send {cap} personalized notes (no mass sends)",
        "Follow up on messages from 5+ days ago, once, politely",
        "Ask one past client or colleague for a referral or intro",
        "Fix one portfolio gap: add a case study or before/after",
        "Share one helpful post or comment where your clients gather",
        "Rest / admin: update your tracker",
    ]
    cal = _days(8, 28, cyc)
    open_line = {"direct": "Quick note —", "warm": "Hi [Name], hope your week is going well.", "expert": "I noticed something about [their site/product] that might help:"}.get(tone, "Hi [Name],")
    return [
        _sec(t[0], cal),
        _sec(t[1], [
            f"First note: “{open_line} I help {ideal} with {offer}. I saw [specific detail] and had one idea: [idea]. Would a 15-minute call be useful?”",
            "Follow-up (once, after 5–7 days): “Just floating this back up in case it got buried. No worries if the timing isn’t right.”",
            "Referral ask: “Do you know anyone who might need help with [offer]? I’d appreciate an intro if it’s a fit.”",
            "After a no: “Thanks for letting me know — mind if I check back in a few months?”",
            "Edit every template heavily; send one at a time; follow each platform’s rules; stop if someone asks you to.",
        ]),
        _sec(t[2], [
            "1. Their goal in their words",
            "2. Scope: what’s included and what’s not",
            "3. Timeline with 2–3 milestones",
            "4. What you need from them and by when",
            "5. Assumptions and change process",
            "6. Investment and payment terms (your choice — this isn’t pricing advice)",
            "7. Next step: how to say yes",
        ]),
        _sec(t[3], [
            "Messages sent vs. planned this week",
            "Replies received and conversations started",
            "Follow-ups due next week",
            "One thing that worked, one thing to change",
            "Process metrics only — client wins and income are never promised.",
        ]),
    ]


# ---------------------------------------------------------------- Turnday
def turnday(a, plan):
    t = _titles(plan, ["Full turnover checklist by room", "Restock par sheet", "Seasonal message pack", "Weekly 20-minute host review"])
    tone = a.get("tone", "warm")
    hi = {"warm": "Hi [Guest]! ", "crisp": "Hello [Guest], ", "boutique": "Welcome, [Guest]. ", "playful": "Hey [Guest]! "}.get(tone, "Hi [Guest], ")
    return [
        _sec(t[0], [
            "Entry: sweep/vacuum, wipe door handles, check lockbox/smart lock battery — photo of entry",
            "Kitchen: dishes, wipe counters and appliances, empty fridge of guest items, take out trash — photo of counters",
            "Bathroom: toilet, shower, sink, mirror, fresh towels folded the same way — photo of shower and towels",
            "Bedrooms: fresh linens, check under beds, fluff pillows, test lamps — photo of each made bed",
            "Living area: cushions, remotes, Wi‑Fi card in place — photo of the room",
            "Final walk: lights off, thermostat set, windows locked, report any damage with photos",
        ]),
        _sec(t[1], [
            "Per stay: 2 bath towels + 1 hand towel per guest; 1 set of sheets per bed (+1 spare set on site)",
            "Toilet paper: 2 rolls per bathroom + 4 spare",
            "Coffee/tea: enough for 2 cups per guest per night",
            "Dish soap, sponge, trash bags: replace when half used",
            "Hand soap and shampoo: refill bottles to at least half",
            "Count spares at every turnover; reorder when you hit the ‘par’ minimum",
        ]),
        _sec(t[2], [
            f"Winter: “{hi}Heads up: it’s chilly this week. Extra blankets are in the closet and the thermostat guide is on the fridge.”",
            f"Summer: “{hi}Hot week ahead! Fans are in the hall closet. Please close blinds during the day to keep it cool.”",
            f"Holiday: “{hi}Happy holidays! Here are a few local spots open over the break: [list].”",
            f"Slow season: “{hi}Thanks for staying with us. If you enjoyed it, we’d love an honest review.”",
            "Keep messages accurate; don’t promise amenities you can’t provide.",
        ]),
        _sec(t[3], [
            "Average reply time this week — any messages that waited too long?",
            "Turnovers completed on time? Any late or missed?",
            "Guest issues raised and how they were solved",
            "Restock items running low",
            "One fix for next week",
        ]),
    ]


# ---------------------------------------------------------------- ProofLane
def prooflane(a, plan):
    t = _titles(plan, ["Email script library", "Shot-list templates", "Delivery checklist", "Seasonal booking calendar"])
    return [
        _sec(t[0], [
            "Inquiry reply: “Thanks for reaching out! I’d love to hear more about [date/event]. Here’s my availability and a link to my packages: [link].”",
            "Follow-up (3 days): “Just checking you saw my note — happy to answer any questions.”",
            "Booking confirmed: “You’re booked! Contract and invoice are attached. Next step: [prep call/date].”",
            "Prep (1 week before): timeline, location, what to wear, backup plan for weather.",
            "Delivery: “Your gallery is ready: [link]. Download by [date]; let me know if anything looks off.”",
            "Review request (2 weeks after): “If you enjoyed working together, an honest review would mean a lot: [link].”",
        ]),
        _sec(t[1], [
            "Getting ready / setup details (3–5 frames)",
            "Key people: individuals, pairs, small groups",
            "Main moment(s) — agree on the must-haves list with the client",
            "Candid in-between moments",
            "Environment and details (venue, product, signage)",
            "Group/family list confirmed with names before the day",
        ]),
        _sec(t[2], [
            "Back up files to two places the same day",
            "Cull: first pass picks, second pass final selects",
            "Edit in a consistent style; spot-check skin tones and horizons",
            "Export web and print sizes; name files clearly",
            "Upload gallery, set expiry date, test the link",
            "Send delivery email and archive the project",
        ]),
        _sec(t[3], [
            "12 months out: open next year’s dates and announce on your site",
            "6 months out: email past clients about seasonal sessions",
            "3 months out: share recent work and remaining dates",
            "Slow months: update portfolio, pricing page, and contracts",
            "Booking volume varies — this calendar organizes your outreach, it doesn’t guarantee bookings.",
        ]),
    ]


# ---------------------------------------------------------------- Doorwell
def doorwell(a, plan):
    t = _titles(plan, ["12-month calendar by unit", "Turnover punch list", "Vendor call log", "Tenant notice outlines"])
    hvac = a.get("hvac", "furnace")
    climate = a.get("climate", "mixed")
    filt = "Replace HVAC filter" if hvac in ("furnace", "heatpump", "unsure") else "Check heating system (boiler/wall units)"
    months = [
        f"January: {filt}; test smoke/CO alarms; check for drafts" + (" and frozen-pipe risk" if climate in ("cold", "mixed") else ""),
        "February: Check under sinks for leaks; review leases expiring in the next 90 days",
        f"March: Gutters and downspouts; exterior walk-around photos",
        f"April: {filt}; service A/C or heat pump before warm weather",
        "May: Check irrigation/hoses, window screens, and caulking",
        "June: Water heater check (temperature setting, visible corrosion)",
        f"July: {filt}; check dryer vent for lint buildup",
        "August: Pest check around foundation and entry points",
        "September: Roof and gutter check before the wet season",
        f"October: {filt}; schedule heating service; test alarms again",
        "November: Weatherstrip doors, shut off exterior faucets" + (" before freezing" if climate in ("cold", "mixed") else ""),
        "December: Year review — repairs log, vendor costs, next year’s budget",
    ]
    return [
        _sec(t[0], months),
        _sec(t[1], [
            "Move-out walk-through with photos/video of every room",
            "List repairs: paint touch-ups, fixtures, appliances, flooring",
            "Deep clean: kitchen, bathrooms, windows, floors",
            "Re-key or change lock codes",
            "Test alarms, replace filter, check all lights and outlets",
            "Final photo log dated before the new tenant moves in",
        ]),
        _sec(t[2], [
            "Columns: date · vendor · trade · issue · quote · final cost · rating · notes",
            "Keep two contacts per trade (plumbing, electrical, HVAC, handyman, cleaning)",
            "Ask for license/insurance info and keep a copy",
            "Note response time — it matters more than price in emergencies",
        ]),
        _sec(t[3], [
            "Entry notice outline: date, time window, reason, contact — check your state’s notice period",
            "Maintenance update outline: what’s being fixed, when, and what tenants need to do",
            "Lease renewal outline: current terms, proposed terms, response deadline",
            "These are outlines, not legal forms. Rules vary by state and city — check local law or a licensed professional.",
        ]),
    ]


# ---------------------------------------------------------------- Chalkday
def chalkday(a, plan):
    t = _titles(plan, ["Daily post + board copy", "Photo prompts", "Holiday & local-event packs", "Weekly debrief sheet"])
    cuisine = a.get("cuisine") or "your kitchen"
    return [
        _sec(t[0], [
            f"Mon: “Start the week right: [special] — made in-house, {cuisine} style.” Board: TODAY · [special] · [price]",
            "Tue: “Two-for-Tuesday idea: pair [dish] with [drink].” Board: PAIR IT · [dish] + [drink]",
            "Wed: “Midweek pick from the chef: [special].” Board: CHEF’S PICK",
            "Thu: “Back by request: [dish].” Board: BACK AGAIN",
            "Fri: “Weekend starts here: [special].” Board: FRIDAY FEATURE",
            "Sat/Sun: “Brunch/Weekend plate: [dish].” Board: WEEKEND ONLY",
            "Keep prices and allergens accurate; only say ‘limited’ if it truly is.",
        ]),
        _sec(t[1], [
            "Shoot near a window, no overhead lights, no flash",
            "Top-down for flat plates; 45° angle for burgers, drinks, and stacks",
            "Wipe plate edges; add one garnish or hand in frame",
            "Take 3 shots: close-up, plate + table, and the board",
            "Shoot right after plating — steam and gloss fade fast",
        ]),
        _sec(t[2], [
            "Holidays: plan specials 3 weeks ahead; post a teaser 1 week ahead",
            "Sports nights: shareable plates and a simple combo",
            "Local markets/festivals: highlight a local ingredient",
            "Slow weeks: a ‘staff favorite’ series",
        ]),
        _sec(t[3], [
            "Special · portions prepped · sold · wasted",
            "What sold out early? What came back?",
            "Which post or board line did guests mention?",
            "Repeat, tweak, or retire each special",
        ]),
    ]


# ---------------------------------------------------------------- Benchnote
def benchnote(a, plan):
    t = _titles(plan, ["Day-by-day 30-day calendar", "Title & tag checklist", "Mini-collection launch timeline", "Seasonal packs"])
    cyc = ["Make", "Make", "Photo session (window light, same backdrop)", "List 2–3 items using your template", "Make", "One social post + answer messages", "Rest"]
    return [
        _sec(t[0], _days(1, 30, cyc)),
        _sec(t[1], [
            "Title: what it is + material + size/color + who it’s for, in plain words",
            "Front-load the words a shopper would type first",
            "Use all available tags with different phrases (not repeats)",
            "Description: first two lines answer ‘what is it, how big, how it’s made’",
            "Add care instructions, shipping time, and materials",
            "Education only — follow each marketplace’s rules; rankings aren’t guaranteed.",
        ]),
        _sec(t[2], [
            "Week 1: pick 6–8 pieces with one theme; finish making",
            "Week 2: photograph everything in one session; write listings",
            "Week 3: share behind-the-scenes posts; tell your email list the date",
            "Week 4: publish all listings on launch day; thank everyone who shares",
            "No fake countdowns or ‘only 1 left’ unless it’s true.",
        ]),
        _sec(t[3], [
            "Winter holidays: list gift-ready items 8 weeks ahead; post shipping cut-off dates",
            "Valentine’s/spring: small, giftable pieces 6 weeks ahead",
            "Wedding season: custom or bulk options with clear lead times",
            "Off season: restock basics, update photos, and plan the next collection",
        ]),
    ]


# ---------------------------------------------------------------- Applyward
def applyward(a, plan):
    t = _titles(plan, ["Week-by-week countdown", "Recommendation ask scripts", "Aid & scholarship tracker", "Parent / mentor check-in guide"])
    weeks = int(a.get("term") or 12)
    weeks = max(6, min(weeks, 24))
    cyc = [
        "Build your list: dream, target, and likely schools/programs with deadlines",
        "Gather documents: transcripts, test scores (if needed), activity list",
        "Brainstorm essay topics; pick one and outline it",
        "Write a rough essay draft",
        "Ask for recommendations (at least 4 weeks before the deadline)",
        "Revise essay with one trusted reader",
        "Complete application forms for the first deadline",
        "Aid forms: check FAFSA/CSS or program aid dates",
        "Submit and confirm receipt; note portal logins",
        "Send thank-you notes to recommenders",
    ]
    return [
        _sec(t[0], [f"Week {w}: {cyc[(w - 1) % len(cyc)]}" for w in range(1, weeks + 1)]),
        _sec(t[1], [
            "“Hi [Name], I’m applying to [programs] this fall. You know my work in [class/activity], and I’d be grateful if you could write a recommendation. The deadline is [date].”",
            "Attach a brag sheet: activities, a project you’re proud of, goals, and deadlines",
            "Reminder (1 week before): “Just a friendly reminder that the deadline is [date]. Thank you again!”",
            "Thank-you note after submission",
        ]),
        _sec(t[2], [
            "Columns: name · amount · deadline · requirements · documents · submitted (Y/N)",
            "Check each school’s own aid deadlines — they can differ from application deadlines",
            "Keep copies of every form you submit",
            "Organization tool only — not financial advice; no aid or admission is guaranteed.",
        ]),
        _sec(t[3], [
            "15 minutes, same day each week",
            "Ask: what got done, what’s next, what’s blocking you?",
            "Let the applicant set the agenda; offer help, not pressure",
            "End with one clear next step and its date",
        ]),
    ]


# ---------------------------------------------------------------- Movewright
def movewright(a, plan):
    t = _titles(plan, ["Week-by-week countdown", "Room-by-room packing lists", "Moving-day run sheet", "First-week setup module"])
    weeks = int(a.get("weeks") or 5)
    tasks = [
        "Decide moving method; get 2–3 quotes or reserve truck",
        "Declutter one room: keep, donate, sell, toss",
        "Order boxes, tape, labels; start packing rarely used items",
        "Change of address, utilities shut-off and start dates",
        "Pack room by room; label every box with room + contents",
        "Confirm movers/truck, parking, and elevator time",
        "Pack an ‘open first’ box and a personal essentials bag",
    ]
    countdown = [f"{w} week{'s' if w != 1 else ''} out: {tasks[(weeks - w) % len(tasks)]}" for w in range(weeks, 0, -1)]
    return [
        _sec(t[0], countdown + ["Move week: final clean, photos of the old place, hand back keys"]),
        _sec(t[1], [
            "Kitchen: pack spare dishes first; leave 1 plate, cup, and pan per person",
            "Bedroom: off-season clothes first; leave one week of clothes",
            "Bathroom: pack last; tape lids; keep medicines with you",
            "Living room: books in small boxes; wrap screens; photo cable setups",
            "Label: room · contents · ‘fragile’ · box number",
        ]),
        _sec(t[2], [
            "Morning: strip beds, pack bedding into the ‘open first’ box",
            "Movers/truck arrive: walk-through, point out fragile items",
            "Last load: check every closet, cabinet, and drawer",
            "Old home: photos, meter readings, keys",
            "New home: open-first box, beds made before evening",
        ]),
        _sec(t[3], [
            "Day 1: test smoke/CO alarms, find the water shut-off and breaker panel",
            "Day 2: kitchen and bathroom unpacked",
            "Day 3: bedrooms and work-from-home setup",
            "Day 4–7: update address on remaining accounts, flatten boxes",
            "Note any damage from the move and contact your mover the same week",
        ]),
    ]


# ---------------------------------------------------------------- Dewlist
def dewlist(a, plan):
    t = _titles(plan, ["4-week habit tracker", "Ingredient label explainer", "Seasonal routine swaps", "Questions to bring to your dermatologist"])
    return [
        _sec(t[0], [
            "Each day: ☐ AM routine ☐ PM routine ☐ Sunscreen (if outdoors) ☐ One-word ‘how does it feel’ note",
            "Week 1: keep it simple — cleanser, moisturizer, sunscreen",
            "Week 2: same routine; note anything that stings or feels tight",
            "Week 3: if all is calm, consider adding one product, patch-tested first",
            "Week 4: review notes; keep what feels good, drop what doesn’t",
            "No before/after promises — skin changes vary and take time.",
        ]),
        _sec(t[1], [
            "Ingredients are listed from most to least (above about 1%)",
            "‘Fragrance’ or ‘parfum’ can mean many ingredients — note it if you’re sensitive",
            "Humectants (like glycerin) attract water; occlusives (like petrolatum) seal it in",
            "Patch-test new products on a small area for a few days",
            "Education only — not a product prescription.",
        ]),
        _sec(t[2], [
            "Dry/cold months: richer moisturizer at night; gentler cleanser",
            "Humid months: lighter textures; keep sunscreen",
            "Indoor heating/AC: consider a humidifier and drink water",
            "Travel: pack your basic routine in small containers",
        ]),
        _sec(t[3], [
            "What’s the main concern and how long have I had it?",
            "What products am I using now (bring photos of labels)?",
            "Is anything I’m using irritating or interacting?",
            "Which sunscreen type suits my skin?",
            "When should I follow up?",
            "See a doctor or dermatologist for rashes, changing moles, or anything painful.",
        ]),
    ]


# ---------------------------------------------------------------- Nestday
def nestday(a, plan):
    t = _titles(plan, ["Sample day blocks", "Caregiver hand-off sheet", "Age-transition modules", "Questions for your pediatrician"])
    wake = a.get("wake", "7")
    w = int(wake) if str(wake).isdigit() else 7
    return [
        _sec(t[0], [
            f"~{w}:00 Wake, feed, diaper, light and cuddles",
            f"~{w + 1}:30 Calm play, outside time if possible",
            "Watch for sleepy cues (yawning, rubbing eyes, looking away) — start the nap routine then",
            "Midday: feed, nap, quiet play — times shift with age and cues",
            "Late afternoon: walk or floor play",
            "Evening: bath (optional), feed, short book or song, sleep space",
            "These are examples. Follow your child’s cues and your pediatrician’s advice.",
        ]),
        _sec(t[1], [
            "Usual wake time and bedtime",
            "Feeding: type, amounts or timing, and how they show hunger",
            "Nap routine steps and sleep space",
            "Soothing tips that work",
            "Allergies, medicines, and emergency contacts",
            "Pediatrician name and phone",
        ]),
        _sec(t[2], [
            "Nap transitions: many babies drop naps gradually; expect some messy weeks",
            "Sleep changes around growth spurts, teething, or new skills are common",
            "Keep the bedtime routine the same even when timing changes",
            "Safe sleep basics: back to sleep, firm flat surface, no loose bedding — follow current pediatric guidance",
            "General education only — ask your pediatrician about your child.",
        ]),
        _sec(t[3], [
            "Is my child’s sleep and feeding typical for their age?",
            "How do I know they’re getting enough to eat?",
            "What sleep changes should I expect next?",
            "When should I call you vs. go to urgent care?",
            "Call your pediatrician right away for fever in young infants, feeding refusal, or anything that worries you.",
        ]),
    ]


# ---------------------------------------------------------------- Gatherweek
def gatherweek(a, plan):
    t = _titles(plan, ["4-week announcement calendar", "Volunteer shift templates", "Newcomer onboarding checklist", "Seasonal & event-week playbooks"])
    tone = a.get("tone", "warm")
    hi = {"warm": "Hi friends! ", "formal": "Dear members, ", "brief": "", "joyful": "Hello, wonderful people! "}.get(tone, "Hi all, ")
    return [
        _sec(t[0], [
            f"Week 1: “{hi}Here’s what’s coming up: [events]. Sign-ups for [role] are open: [link].”",
            f"Week 2: “{hi}Thank you to everyone who helped last week! Still need 2 people for [role].”",
            f"Week 3: “{hi}Save the date: [event]. Bring a friend.”",
            f"Week 4: “{hi}Monthly wrap-up: [highlights]. Next month we need [roles].”",
            "Send on the same day and time each week so people know when to look.",
        ]),
        _sec(t[1], [
            "Sign-up: “We need [number] people for [role] on [date], [time]. It takes about [length]. Sign up: [link].”",
            "Reminder (2 days before): “Thanks for signing up for [role] on [date]! Arrive at [time]; [contact] will meet you.”",
            "Swap: “Can’t make it? Reply here and we’ll help find a swap.”",
            "Thank-you: “Thank you for helping with [role] — it made a real difference.”",
        ]),
        _sec(t[2], [
            "First visit: personal welcome and a simple info card",
            "Within a week: a short follow-up message",
            "Second visit: introduce them to 2 people",
            "First month: invite them to an easy, low-commitment role",
            "Check in after their first volunteer shift",
        ]),
        _sec(t[3], [
            "6 weeks out: set the date, roles, and a lead for each role",
            "4 weeks out: open sign-ups and announce",
            "2 weeks out: fill gaps with personal asks",
            "Event week: daily reminders, setup checklist, backup volunteers",
            "After: thank-yous and a 15-minute debrief",
        ]),
    ]


GENERATORS: dict[str, Callable[[dict, dict], list[dict]]] = {
    "shelfspeak": shelfspeak, "signmatch": signmatch, "cuetrail": cuetrail, "replypath": replypath,
    "turnday": turnday, "prooflane": prooflane, "doorwell": doorwell, "chalkday": chalkday,
    "benchnote": benchnote, "applyward": applyward, "movewright": movewright, "dewlist": dewlist,
    "nestday": nestday, "gatherweek": gatherweek,
}


def full_sections(slug: str, answers: dict, plan: dict) -> list[dict]:
    fn = GENERATORS.get(slug)
    if not fn:
        return []
    return fn(answers or {}, plan or {})
