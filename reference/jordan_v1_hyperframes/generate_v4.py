from __future__ import annotations

import json
import urllib.parse
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIO = json.loads((ROOT / "audio_manifest.json").read_text(encoding="utf-8-sig"))
BLOCKS = [(item["id"], float(item["start"])) for item in AUDIO["blocks"]]
STARTS = dict(BLOCKS)
TOTAL = float(AUDIO["duration"])
ENDS = {bid: (BLOCKS[i + 1][1] if i + 1 < len(BLOCKS) else TOTAL) for i, (bid, _) in enumerate(BLOCKS)}


LOW_RES = {
    "bite_mj_meals.mp4", "bite_mj_conditioning.mp4", "seventy_two_ten.mp4",
    "flu_game_backstory.mp4", "running_with_bulls.mp4", "camp_shooting.mp4",
    "bite_mj_outofshape.mp4", "bite_mj_practice.mp4", "jordan_rules.mp4",
    "finals_backstage_1996.mp4",
}


def f(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def dur(block: str) -> float:
    return ENDS[block] - STARTS[block]


def attrs(uid: str, block: str, track: int = 0) -> str:
    return f'id="{uid}" data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}" data-track-index="{track}" data-layout-allow-overlap data-layout-allow-occlusion'


def media_url(path: str) -> str:
    if path.startswith("editorial/"):
        return f"assets/{path}"
    return f"assets/images/{path}"


def video(block: str, asset: str, eyebrow: str = "", headline: str = "", *, uid: str | None = None,
          treatment: str = "auto", position: str = "50% 50%", start: float | None = None,
          duration: float | None = None) -> str:
    clip_start = STARTS[block] if start is None else start
    clip_duration = dur(block) if duration is None else duration
    name = uid or f"v-{block.lower()}"
    framed = asset in LOW_RES or treatment in {"archive", "interview"}
    mode = "film-frame" if framed else "hero-footage"
    copy = ""
    if eyebrow or headline:
        copy = f'''<aside class="video-copy" data-layout-allow-overlap><p data-layout-allow-overlap>{escape(eyebrow)}</p><h2 data-layout-allow-overlap>{headline}</h2><span>CELEB WORKOUT / FILM STUDY</span></aside>'''
    video_class = "film-frame-video" if framed else "hero-video"
    return f'''<video id="{name}" class="clip scene-video {video_class}" src="assets/video/{escape(asset)}" data-start="{f(clip_start)}" data-duration="{f(clip_duration)}" data-track-index="1" data-media-start="0" muted playsinline style="object-position:{escape(position)}"></video>
    <div id="{name}-scene" class="clip video-layout {mode}" data-video-id="{name}" data-start="{f(clip_start)}" data-duration="{f(clip_duration)}" data-track-index="3" data-layout-allow-overlap data-layout-allow-occlusion>
      <div class="video-shell"><div class="video-shade"></div></div>{copy}
      <div class="folio">{escape(block)} / 23</div></div>'''


def montage(block: str, assets: list[str], eyebrow: str, headline: str) -> str:
    length = dur(block)
    unit = length / len(assets)
    parts = []
    for index, asset in enumerate(assets):
        start = STARTS[block] + unit * index
        current = length - unit * index if index == len(assets) - 1 else unit
        parts.append(video(block, asset, uid=f"v-{block.lower()}-{index}", start=start, duration=current))
    parts.append(f'''<div id="montage-{block.lower()}" class="clip montage-copy" data-start="{f(STARTS[block])}" data-duration="{f(min(length, 7.2))}" data-track-index="4" data-layout-allow-overlap data-layout-allow-occlusion><p>{escape(eyebrow)}</p><h2>{headline}</h2></div>''')
    return "\n".join(parts)


def photo_story(block: str, images: list[tuple[str, str]], eyebrow: str, headline: str) -> str:
    figures = "".join(
        f'''<figure><img src="{escape(media_url(src))}"/><figcaption><b>0{idx + 1}</b>{escape(label)}</figcaption></figure>'''
        for idx, (src, label) in enumerate(images)
    )
    return f'''<div {attrs(f"photos-{block.lower()}", block)} class="clip photo-feature photos-{len(images)}">
      <header class="page-mast"><strong>CELEB WORKOUT</strong><span>MICHAEL JORDAN / THE WORK BEHIND THE BODY</span></header>
      <div class="photo-feature-grid">{figures}</div>
      <div class="photo-deck"><p>{escape(eyebrow)}</p><h2>{headline}</h2></div><div class="page-number">{escape(block)}</div>
    </div>'''


def evidence(block: str, publication: str, date: str, headline: str, before: str, marked: str,
             after: str, source_url: str, visual: str, *, crop: str = "50% 50%") -> str:
    domain = urllib.parse.urlparse(source_url).netloc.replace("www.", "")
    return f'''<div {attrs(f"evidence-{block.lower()}", block)} class="clip evidence-spread">
      <header class="page-mast"><strong>{escape(publication)}</strong><span>{escape(date)} / SOURCE FILE</span></header>
      <div class="evidence-grid">
        <figure class="evidence-visual"><img src="{escape(media_url(visual))}" style="object-position:{escape(crop)}"/><figcaption>ORIGINAL REPORTING / ARCHIVAL IMAGE</figcaption></figure>
        <article class="evidence-copy"><span>FIELD NOTE {escape(block)}</span><h2>{escape(headline)}</h2>
          <p>{escape(before)} <mark><i></i><b>{escape(marked)}</b></mark> {escape(after)}</p>
          <footer>{escape(domain)}</footer></article>
      </div><div class="page-number">{escape(block)}</div>
    </div>'''


def feature_opener(block: str, asset: str, line1: str, line2: str, eyebrow: str, media_start: float = 0) -> str:
    vid = f"opener-video-{block.lower()}"
    return f'''<video id="{vid}" class="clip opener-video" src="assets/video/{escape(asset)}" data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}" data-track-index="1" data-media-start="{f(media_start)}" muted playsinline></video>
    <div {attrs(f"opener-{block.lower()}", block, 2)} class="clip feature-opener" data-video-id="{vid}">
      <div class="opener-shade"></div><section class="opener-page" data-layout-allow-overlap><p>{escape(eyebrow)}</p><h1 data-layout-allow-overlap><span data-layout-allow-overlap>{escape(line1)}</span><span data-layout-allow-overlap>{escape(line2)}</span></h1><i></i><small>THE SYSTEM / REPORTED &amp; RECONSTRUCTED</small></section>
      <div class="cover-kicker">MICHAEL JORDAN</div><div class="page-number">{escape(block)}</div>
    </div>'''


def compare(block: str, left: str, right: str, left_label: str, right_label: str, headline: str) -> str:
    return f'''<div {attrs(f"compare-{block.lower()}", block)} class="clip compare-feature">
      <header class="page-mast"><strong>BODY OF WORK</strong><span>THEN / BUILT</span></header>
      <div class="compare-grid"><figure><img src="{escape(media_url(left))}"/><figcaption>{escape(left_label)}</figcaption></figure><figure><img src="{escape(media_url(right))}"/><figcaption>{escape(right_label)}</figcaption></figure></div>
      <h2>{headline}</h2><div class="compare-rule"></div><div class="page-number">{escape(block)}</div></div>'''


def number_scene(block: str, eyebrow: str, number: str, unit: str, headline: str, sub: str = "") -> str:
    marked_headline = headline.replace('<em>', '<em data-layout-allow-overlap>')
    return f'''<div {attrs(f"stat-{block.lower()}", block)} class="clip stat-feature">
      <header class="page-mast light"><strong data-layout-allow-overlap>CELEB WORKOUT / DATA</strong><span>{escape(block)}</span></header>
      <div class="stat-number" data-layout-allow-overlap><b data-layout-allow-overlap>{escape(number)}</b><span data-layout-allow-overlap>{escape(unit)}</span></div>
      <article data-layout-allow-overlap><p>{escape(eyebrow)}</p><h2 data-layout-allow-overlap>{marked_headline}</h2><h3>{escape(sub)}</h3></article><div class="stat-rail"></div></div>'''


def diagram(block: str, eyebrow: str, headline: str, steps: list[tuple[str, str]]) -> str:
    nodes = "".join(f'''<div class="diagram-node"><b>{escape(big)}</b><span>{escape(small)}</span></div>''' for big, small in steps)
    return f'''<div {attrs(f"diagram-{block.lower()}", block)} class="clip diagram-feature">
      <header class="page-mast"><strong>TRAINING FILE</strong><span>{escape(block)}</span></header>
      <div class="diagram-head"><p>{escape(eyebrow)}</p><h2>{headline}</h2></div>
      <div class="diagram-rule"></div><div class="diagram-flow">{nodes}</div><footer>LOAD FOLLOWS FUNCTION / NOT APPEARANCE</footer></div>'''


def feature_spread(block: str, eyebrow: str, title: str, quote: str, source: str, image: str, *, crop: str = "50% 50%") -> str:
    return f'''<div {attrs(f"feature-{block.lower()}", block)} class="clip feature-spread">
      <header class="page-mast"><strong>LONG FORM / MICHAEL JORDAN</strong><span>{escape(block)}</span></header>
      <figure data-layout-allow-overflow><img src="{escape(media_url(image))}" style="object-position:{escape(crop)}"/><figcaption>{escape(eyebrow)}</figcaption></figure>
      <article><p>{escape(eyebrow)}</p><h2>{escape(title)}</h2><blockquote>“{escape(quote)}”</blockquote><i></i><footer>{escape(source)}</footer></article>
      <div class="page-number">{escape(block)}</div></div>'''


def people(block: str) -> str:
    return f'''<div {attrs("roster-w1", block)} class="clip roster-feature">
      <header class="page-mast"><strong>THE BREAKFAST CLUB</strong><span>5–7 A.M. / HIGHLAND PARK</span></header>
      <div class="roster-grid"><figure class="roster-main"><img src="assets/images/scottie_pippen.jpg"/><figcaption>01 / SCOTTIE PIPPEN</figcaption></figure>
      <figure><img src="assets/images/ron_harper.jpg"/><figcaption>02 / RON HARPER</figcaption></figure><figure><img src="assets/images/randy_brown.jpg"/><figcaption>03 / RANDY BROWN</figcaption></figure></div>
      <h2 data-layout-allow-overlap data-layout-allow-occlusion>BEFORE THE ARENA.<br><em>BEFORE THE CROWD.</em></h2><div class="page-number">W1</div></div>'''


def lower_interview(block: str, asset: str, name: str, role: str) -> str:
    return video(block, asset, treatment="interview") + f'''<div id="id-{block.lower()}" class="clip interview-slug" data-start="{f(STARTS[block])}" data-duration="{f(min(dur(block), 6.4))}" data-track-index="5"><span>ORAL HISTORY</span><p>{escape(role)}</p><h2>{escape(name)}</h2></div>'''


def archive_interview(block: str, asset: str, role: str, pullquote: str) -> str:
    timing = f'data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}"'
    vid = f"archive-video-{block.lower()}"
    return f'''<video id="{vid}" class="clip archive-video" src="assets/video/{escape(asset)}" {timing} data-track-index="1" data-media-start="0" muted playsinline></video>
    <div id="archive-{block.lower()}" class="clip archive-feature" data-video-id="{vid}" {timing} data-track-index="2" data-layout-allow-overlap data-layout-allow-occlusion>
      <header class="page-mast light"><strong>PRIMARY SOURCE / TAPE</strong><span>{escape(block)}</span></header>
      <div class="archive-frame"><span class="timecode">TC 00:{escape(block)}:23</span></div>
      <article><p>MICHAEL JORDAN / ARCHIVE</p><h2>{escape(role)}</h2><blockquote>{escape(pullquote)}</blockquote><i></i><footer>ORIGINAL AUDIO / EDITORIAL FRAME</footer></article></div>'''


def summary_scene(block: str) -> str:
    return f'''<div {attrs("summary-e1v4", block)} class="clip closing-summary">
      <header class="page-mast light"><strong>THE HONEST SUMMARY</strong><span>THE SYSTEM / 1989–2003</span></header>
      <h2>ORDINARY<br>WORK.<br><em>EXTRAORDINARY</em><br>CONSISTENCY.</h2>
      <div class="closing-list"><span>MOBILITY</span><span>CONDITIONING</span><span>STRENGTH</span><span>FOOD</span><span>SLEEP</span><b>REPEAT</b></div>
      <div class="closing-red" data-layout-allow-overflow></div></div>'''


SCENES: dict[str, str] = {
    "I1": feature_opener("I1", "intro_last_shot.mp4", "THE WORK", "BEHIND THE BODY", "MICHAEL JORDAN / REPORTED, NOT MYTHOLOGIZED", media_start=1.25),
    "H1": video("H1", "pistons_contact.mp4", "THE PROBLEM", "THE BEST PLAYER IN THE LEAGUE.<br><em>STILL GOING HOME.</em>"),
    "H2": evidence("H2", "CBS SPORTS", "MAY 2020", "How Jordan built for Detroit", "Detroit eliminated Chicago in", "three consecutive postseasons: 1988, 1989 and 1990.", "Twice, the loss came in the Conference Finals.", "https://www.cbssports.com/nba/news/how-michael-jordan-bulked-up-to-outmuscle-pistons-win-first-nba-championship-with-bulls", "editorial/stills/pistons_contact.jpg"),
    "H3": video("H3", "jordan_rules.mp4", "DETROIT'S PLAN", "THE JORDAN <em>RULES</em>", treatment="archive"),
    "R1": photo_story("R1", [("mj_family_young.jpg", "WILMINGTON"), ("mj_young1.jpg", "AGE 21"), ("editorial/jordan_wilmington_home.jpg", "THE FAMILY HOME")], "THE ORIGIN STORY", "LEFT OFF VARSITY.<br><em>NOT LEFT BEHIND.</em>"),
    "R2": photo_story("R2", [("mj_laney_action.jpg", "THE WORK"), ("mj_laney_dunk.jpg", "THE GROWTH")], "THE BACK GARDEN", "LARRY WON.<br>MICHAEL <em>RETURNED.</em>"),
    "R3": feature_spread("R3", "NORTH CAROLINA / 1982", "THE SHOT", "A freshman takes the final shot of the national championship.", "SPORTS ILLUSTRATED / ARCHIVAL REPORT", "editorial/jordan_1982_shot.jpg", crop="55% 36%"),
    "R4": montage("R4", ["rookie_1984.mp4", "boston_63.mp4", "defense_1988.mp4"], "1984 → 1988", "BRILLIANCE <em>WITHOUT THE RING.</em>"),
    "R5": video("R5", "dirty_defense.mp4", "DETROIT", "EVERY POSSESSION<br><em>EXPENSIVE.</em>"),
    "R6": compare("R6", "mj_skinny.jpg", "mj_built.jpg", "1985 / 195 LB", "MID-90s / BUILT FOR CONTACT", "THE FRAME <em>CHANGED</em>"),
    "R7": feature_opener("R7", "mvp_1988.mp4", "AN ENGINEERING", "PROBLEM", "SUMMER / 1990"),
    "T1": photo_story("T1", [("mj_grover_gq_2000.jpg", "JORDAN + GROVER"), ("mj_grover_press.jpg", "THE PARTNERSHIP")], "CHICAGO / 1989", "ONE TRAINER.<br><em>ALMOST NO CLIENTS.</em>"),
    "T2": lower_interview("T2", "bite_grover_letter.mp4", "TIM GROVER", "HOW THE LETTER REACHED JORDAN"),
    "T3": evidence("T3", "GQ", "THE ASSIST", "The letter that found Jordan", "Grover learned Jordan was tired of", "being knocked around by Detroit", "and wrote directly to the player with a reason to answer.", "https://www.gq.com/story/tim-grover-michael-jordan-the-assist", "editorial/article_gq_grover.png", crop="50% 58%"),
    "T3b": number_scene("T3b", "THE AGREEMENT", "30", "DAYS", "BECAME <em>15 YEARS</em>", "Nothing more — unless it worked."),
    "T3c": photo_story("T3c", [("tim_grover_b.jpg", "THE TRAINER"), ("mj_grover_training.jpg", "THE WORK")], "THE FIRST PROGRAM", "BUILD THE BODY.<br><em>KEEP THE GAME.</em>"),
    "T4": lower_interview("T4", "bite_grover_program.mp4", "TIM GROVER", "THE FIRST PROGRAM"),
    "T5": compare("T5", "mj_skinny2.jpg", "mj_built2.jpg", "THE TALENT", "THE ARMOR", "≈15 LB <em>OF MUSCLE</em>"),
    "W1": people("W1"),
    "W1b": video("W1b", "render_ready/arriving_to_practice.mp4", "BEFORE DAWN", "THE DAY STARTED<br><em>BEFORE THE ARENA.</em>"),
    "W1c": lower_interview("W1c", "bite_grover_breakfast.mp4", "TIM GROVER", "THE BREAKFAST CLUB ROUTINE"),
    "W1d": video("W1d", "render_ready/finals_backstage_1996.mp4", "THE SECOND THREE-PEAT", "BY THEN, THIS WAS<br><em>THE TEAM'S MORNING.</em>", treatment="archive"),
    "W2": feature_opener("W2", "render_ready/bulls_backstage_1998.mp4", "UNGLAMOROUS", "ON PURPOSE", "THE PROGRAM / DAILY WORK"),
    "W3": diagram("W3", "THE PROGRAM", "BASE → FORCE → CONTROL", [("SQUAT", "BASE"), ("CLEAN", "FORCE"), ("STEP-UP", "TRANSFER"), ("CORE", "CONTROL")]),
    "W4": evidence("W4", "BASKETBALL NETWORK", "TIM GROVER", "The set never ended at six", "Grover would prescribe six repetitions.", "Jordan did twelve — every set.", "The harder job was getting him to stop.", "https://www.basketballnetwork.net/old-school/tim-grover-said-michael-jordan-gained-15-pounds-to-beat-bad-boy-pistons", "editorial/stills/grover_program.jpg"),
    "W6": feature_spread("W6", "ARCHIVE TRANSCRIPT", "NO SECRET EXERCISE", "Conditioning and nutrition are very important. I used to work out every single day.", "MICHAEL JORDAN / RECORDED AT THE TIME", "mj_dunk87.jpg"),
    "W7": archive_interview("W7", "render_ready/bite_mj_conditioning.mp4", "CONDITIONING + WEIGHTS", "WEIGHTS. AEROBIC WORK. EVERY DAY."),
    "W8": number_scene("W8", "LISTEN TO THE ORDER", "01", "FIRST", "CONDITIONING<br><em>BEFORE WEIGHTS.</em>"),
    "W9": diagram("W9", "JORDAN'S OWN SEQUENCE", "PREPARE → CONDITION → LOAD", [("STRETCH", "MOBILITY"), ("SPRINT", "STAMINA"), ("LIFT", "STRENGTH")]),
    "W10": video("W10", "bench_strategy.mp4", "THE DETAIL IN THE PHOTOGRAPHS", "LOOK AT<br><em>THE SHORTS.</em>"),
    "W11": evidence("W11", "TIM GROVER", "INTERVIEW TRANSCRIPT", "A recovery signal hidden in plain sight", "He told Jordan to grab the hem of his shorts instead of leaning on his knees.", "It reduced the load without broadcasting exhaustion.", "The detail mattered because opponents were always reading him.", "https://www.youtube.com/watch?v=lfCZOKhWqWU", "editorial/stills/bench_strategy.jpg"),
    "W12": diagram("W12", "A PROGRAM FOR A BODY", "LEFT ≠ RIGHT", [("MEASURE", "ASYMMETRY"), ("ADJUST", "LOAD"), ("TEST", "MOVEMENT")]),
    "W13": feature_spread("W13", "TRAIN THE ATHLETE — NOT THE CHART", "ASYMMETRY", "One hand might carry fifty pounds while the other carried ten. The objective was balance in motion.", "TIM GROVER / TRAINING ACCOUNT", "bulls_practice_trio.jpg"),
    "W14": number_scene("W14", "PRO BASKETBALL", "1990", "THE TURN", "WEIGHTS WERE STILL<br><em>THE ENEMY.</em>", "Players feared losing their shooting touch."),
    "W14b": video("W14b", "render_ready/running_with_bulls.mp4", "CHIP SCHAEFER", "HE ARRIVED AT<br><em>EXACTLY THAT MOMENT.</em>", treatment="archive"),
    "W14d": lower_interview("W14d", "bite_schaefer_1990.mp4", "CHIP SCHAEFER", "BULLS HEAD ATHLETIC TRAINER / 1990"),
    "W14e": evidence("W14e", "CHIP SCHAEFER", "ORAL HISTORY", "The league catches up", "In 1990, weight training was", "only beginning to take hold across professional basketball.", "Jordan and Grover were already building for contact.", "https://www.youtube.com/watch?v=D1sKOv7WFBA", "editorial/stills/schaefer_1990.jpg"),
    "W15": photo_story("W15", [("mj_rookie_1985.jpg", "WHAT HE HAD"), ("mj_1996_built.jpg", "WHAT HE BUILT")], "THE FINISHED FRAME", "THE ROUTINE WAS COPYABLE.<br><em>THE APPETITE WASN'T.</em>"),
    "W16": video("W16", "rare_practice_1998.mp4", "THE PART YOU CANNOT PROGRAM", "RETURN TO THE<br><em>DISCOMFORT.</em>"),
    "D1": feature_opener("D1", "championship_archive.mp4", "FOOD IS", "TIMING", "04 / INPUTS FOR THE WORK"),
    "D2": evidence("D2", "THE SPORTS RUSH", "REPORTING SUMMARY", "Against the era's orthodoxy", "The standard advice was carbohydrate loading:", "rice, pasta, bread — and more of it.", "Jordan's game-day plan went in the other direction.", "https://thesportsrush.com/nba-news-michael-jordan-had-the-most-odd-pregame-meal-tim-grover-explains-the-reason-behind-why-the-goat-used-to-eat-a-whole-steak-before-bulls-games/", "mj_pippen_highfive.jpg"),
    "D3": diagram("D3", "THE INPUTS", "BODY CHEMISTRY + ENERGY OUTPUT", [("BODY", "CHEMISTRY"), ("WORK", "DEMAND"), ("MEAL", "TIMING")]),
    "D4": evidence("D4", "SLAM", "GAME-DAY ROUTINE", "The unusual part was the clock", "Jordan's preferred game-day meal was steak and a potato,", "about four hours before tipoff.", "The point was predictable energy, not novelty.", "https://www.slamonline.com/the-magazine/michael-jordan-gameday-routine/", "editorial/stills/mj_meals.jpg"),
    "D5": diagram("D5", "A SIMPLE DAY", "THREE MEALS / TRAINING CLOCK", [("BREAKFAST", "FUEL"), ("PRACTICE", "WORK"), ("RECOVER", "EAT + REST")]),
    "D6": archive_interview("D6", "render_ready/bite_mj_meals.mp4", "MEALS + RECOVERY", "THREE MEALS. TRAIN. RECOVER. REST."),
    "D7": evidence("D7", "TIM GROVER", "INTERVIEW TRANSCRIPT", "The diet argument, simplified", "Every nutrition plan can work", "if the athlete actually follows it.", "Fit the diet to the body, the workload, and the time horizon.", "https://www.youtube.com/watch?v=lfCZOKhWqWU", "tim_grover_a.jpg"),
    "D8": feature_spread("D8", "THE PRINCIPLE", "THE BODY DECIDES", "The useful diet is the one that fits the athlete and survives long enough to matter.", "TIM GROVER / NUTRITION ACCOUNT", "editorial/stills/grover_letter.jpg"),
    "P1": feature_opener("P1", "dream_team_practice.mp4", "PRACTICE", "IS THE TEST", "05 / THE COMPONENT PEOPLE COPY LEAST"),
    "P2": archive_interview("P2", "render_ready/bite_mj_practice.mp4", "PRACTICE AS A TEST", "THE GAME WAS NOTHING HE HADN'T REHEARSED."),
    "P3": video("P3", "jordan_practice.mp4", "THE STANDARD", "TEAMMATES FELT IT<br><em>EVERY DAY.</em>"),
    "P4": evidence("P4", "TIM GROVER", "SIDELINE ACCOUNT", "When the whistle blew", "The room went quiet. Jordan's rule was", "practice hard enough that the game becomes easier.", "The standard also filtered the roster.", "https://www.youtube.com/watch?v=PjSFlFqxyGc", "editorial/stills/mj_practice.jpg"),
    "P5": montage("P5", ["render_ready/camp_shooting.mp4", "render_ready/united_center_warmup.mp4"], "THE EQUATION", "HARDER PRACTICE.<br><em>EASIER GAME.</em>"),
    "S1": video("S1", "pistons_sweep_1991.mp4", "1991 / EASTERN CONFERENCE FINALS", "CHICAGO MET<br><em>DETROIT AGAIN.</em>"),
    "S2": montage("S2", ["first_ring_alt.mp4", "finals_1991.mp4"], "THE ANSWER", "4–0.<br><em>THEN THE FIRST RING.</em>"),
    "S3": video("S3", "flu_game_1997.mp4", "GAME 5 / 1997 FINALS", "38 POINTS.<br><em>BARELY STANDING.</em>"),
    "S4": evidence("S4", "BLEACHER REPORT", "TRAINER'S ACCOUNT", "The night before Game Five", "One pizza was delivered. Jordan was", "the only person in the room who ate it.", "Around three a.m., Grover found him curled into a ball.", "https://bleacherreport.com/articles/1608036-michael-jordans-trainer-says-mjs-famous-flu-game-was-result-of-poisoning", "editorial/stills/flu_game.jpg"),
    "S5": evidence("S5", "THE LAST DANCE", "2020", "The account becomes public", "For twenty-three years the night was remembered as flu.", "Jordan later described food poisoning.", "The label changed. The performance did not.", "https://www.netflix.com/title/80203144", "editorial/stills/flu_game_second.jpg", crop="64% 48%"),
    "S6": video("S6", "flu_game_second.mp4", "DEPLETED / SHIVERING / STILL PLAYING", "THEN HE WALKED<br><em>ONTO THE FLOOR.</em>"),
    "S7": feature_opener("S7", "render_ready/flu_game_backstory.mp4", "44", "MINUTES", "GAME 5 / UTAH / 1997"),
    "E1V4": summary_scene("E1V4"),
    "E2V4": feature_opener("E2V4", "render_ready/seventy_two_ten.mp4", "TALENT", "MADE AVAILABLE", "THE FINISHED PRODUCT WAS BUILT"),
    "E3": archive_interview("E3", "render_ready/bite_mj_outofshape.mp4", "LOSING CONDITIONING", "CONDITIONING IS PERISHABLE."),
    "E4V4": video("E4V4", "bulls_prime.mp4", "THE REAL WORKOUT", "WHOSE SYSTEM<br><em>SHOULD WE STUDY NEXT?</em>"),
}


expected = {bid for bid, _ in BLOCKS}
if set(SCENES) != expected:
    raise RuntimeError(f"Scene map mismatch. Missing={sorted(expected - set(SCENES))}; extra={sorted(set(SCENES) - expected)}")


STYLE = r'''
@font-face{font-family:Anton;src:url("assets/fonts/Anton-Regular.ttf") format("truetype")}
@font-face{font-family:Archivo;src:url("assets/fonts/Archivo-Regular.ttf") format("truetype")}
@font-face{font-family:ArchivoBlack;src:url("assets/fonts/ArchivoBlack-Regular.ttf") format("truetype")}
:root{--red:#b22b1a;--ink:#0d0d0d;--paper:#f4f2ef;--gray:#a9a9a9;--char:#252525}
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1920px;height:1080px;overflow:hidden;background:var(--ink)}body{font-family:Archivo,Arial,sans-serif;color:var(--paper)}#root{position:relative;width:1920px;height:1080px;overflow:hidden;background:var(--ink)}.clip{position:absolute;inset:0;overflow:hidden}.scene-video,.opener-video{width:100%;height:100%;object-fit:cover;background:#080808}.hero-video{inset:0}.film-frame-video{left:88px;top:144px;right:auto;bottom:auto;width:1232px;height:792px;object-fit:contain;background:#050505}.page-mast{position:absolute;z-index:8;left:76px;right:76px;top:48px;height:50px;border-bottom:8px solid var(--red);display:flex;justify-content:space-between;align-items:flex-start;color:var(--ink);font:900 18px ArchivoBlack;letter-spacing:.14em}.page-mast span{font:600 15px Archivo;letter-spacing:.12em;color:#626262}.page-mast.light{color:var(--paper)}.page-mast.light span{color:var(--gray)}.page-number,.folio{position:absolute;font:900 15px ArchivoBlack;letter-spacing:.16em}.page-number{right:78px;bottom:42px;color:#777}.folio{right:46px;bottom:36px;color:#777}.brand-bug{position:absolute;z-index:80;right:44px;top:30px;background:var(--ink);color:var(--paper);border-bottom:5px solid var(--red);padding:12px 17px;font:900 15px ArchivoBlack;letter-spacing:.17em}.texture{position:absolute;z-index:75;inset:0;pointer-events:none;opacity:.06;background-image:radial-gradient(rgba(0,0,0,.55) .6px,transparent .7px);background-size:4px 4px;mix-blend-mode:multiply}.chapter-tab{position:absolute;z-index:77;left:0;top:34px;background:var(--paper);color:var(--ink);border-left:14px solid var(--red);padding:13px 28px 12px 34px;font:900 15px ArchivoBlack;letter-spacing:.15em;box-shadow:10px 10px 0 rgba(13,13,13,.24)}
.video-layout{background:transparent}.video-layout .video-shell{position:absolute;overflow:hidden}.hero-footage .video-shell{inset:0}.film-frame .video-shell{left:74px;top:130px;width:1260px;height:820px;border:14px solid var(--paper);box-shadow:24px 24px 0 rgba(178,43,26,.65)}.video-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(13,13,13,.84),rgba(13,13,13,.1) 58%,rgba(13,13,13,.35)),linear-gradient(0deg,rgba(13,13,13,.72),transparent 46%)}.film-frame .video-shade{background:linear-gradient(0deg,rgba(13,13,13,.22),transparent 50%)}.video-copy{position:absolute;z-index:3;left:84px;bottom:78px;width:1120px}.film-frame .video-copy{left:1400px;top:220px;bottom:auto;width:430px}.video-copy p,.montage-copy p{font:900 19px ArchivoBlack;letter-spacing:.15em;color:var(--gray);margin-bottom:17px}.video-copy p:before,.montage-copy p:before{content:"";display:inline-block;width:86px;height:8px;background:var(--red);margin-right:18px}.video-copy h2,.montage-copy h2{font:400 100px/.91 Anton;text-transform:uppercase;letter-spacing:.01em}.film-frame .video-copy h2{font-size:72px;color:var(--paper)}.video-copy em,.montage-copy em,.roster-feature em,.compare-feature em,.stat-feature em{font-style:normal;color:#d75544}.video-copy span{display:block;margin-top:34px;font:900 13px ArchivoBlack;letter-spacing:.14em;color:#747474}.montage-copy{display:flex;flex-direction:column;justify-content:flex-end;padding:0 84px 80px;background:linear-gradient(0deg,rgba(13,13,13,.88),transparent 72%)}
.feature-opener{background:transparent}.opener-video{position:absolute;inset:0}.opener-shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(13,13,13,.1),rgba(13,13,13,.66) 65%,rgba(13,13,13,.92))}.opener-page{position:absolute;right:0;top:0;width:760px;height:1080px;background:rgba(244,242,239,.96);color:var(--ink);padding:170px 76px 80px;border-left:18px solid var(--red)}.opener-page p{font:900 18px ArchivoBlack;letter-spacing:.15em;color:#666;margin-bottom:54px}.opener-page h1{font:400 124px/.86 Anton;text-transform:uppercase}.opener-page h1 span{display:block}.opener-page i{display:block;width:170px;height:12px;background:var(--red);margin:54px 0 32px}.opener-page small{font:900 14px ArchivoBlack;letter-spacing:.15em}.cover-kicker{position:absolute;left:64px;top:52px;background:var(--ink);border-top:8px solid var(--red);padding:14px 19px;font:900 17px ArchivoBlack;letter-spacing:.18em}
.photo-feature,.evidence-spread,.feature-spread,.compare-feature,.roster-feature,.diagram-feature{background:var(--paper);color:var(--ink)}.photo-feature-grid{position:absolute;left:74px;right:74px;top:126px;bottom:224px;display:grid;gap:18px}.photos-2 .photo-feature-grid{grid-template-columns:1.55fr 1fr}.photos-3 .photo-feature-grid{grid-template-columns:1.4fr 1fr;grid-template-rows:1fr 1fr}.photos-3 figure:first-child{grid-row:1/3}.photo-feature figure,.roster-feature figure,.compare-feature figure,.feature-spread figure,.evidence-visual{position:relative;overflow:hidden;background:#171717}.photo-feature img,.roster-feature img,.compare-feature img,.feature-spread img,.evidence-visual img{width:100%;height:100%;object-fit:cover}.photo-feature figcaption,.roster-feature figcaption,.compare-feature figcaption,.feature-spread figcaption,.evidence-visual figcaption{position:absolute;left:18px;bottom:18px;background:var(--ink);color:var(--paper);padding:10px 14px;font:900 16px ArchivoBlack;letter-spacing:.08em}.photo-feature figcaption b{color:var(--red);margin-right:11px}.photo-deck{position:absolute;left:76px;right:76px;bottom:48px;height:138px;display:flex;justify-content:space-between;align-items:flex-start;gap:44px}.photo-deck p{font:900 18px ArchivoBlack;letter-spacing:.15em;color:var(--red);padding-top:9px}.photo-deck h2{font:400 73px/.9 Anton;text-align:right;text-transform:uppercase}
.evidence-grid{position:absolute;left:76px;right:76px;top:132px;bottom:68px;display:grid;grid-template-columns:1.08fr .92fr;gap:54px}.evidence-visual{border-top:14px solid var(--red)}.evidence-copy{padding:28px 24px 0 0}.evidence-copy>span{font:900 15px ArchivoBlack;letter-spacing:.16em;color:#777}.evidence-copy h2{font:400 72px/.9 Anton;text-transform:uppercase;margin:30px 0 44px}.evidence-copy p{font:400 38px/1.34 Georgia,serif}.evidence-copy mark{position:relative;background:transparent;color:inherit}.evidence-copy mark b{position:relative;z-index:2;font-weight:700}.evidence-copy mark i{position:absolute;z-index:1;left:-6px;right:-6px;bottom:1px;height:88%;background:rgba(178,43,26,.3);transform-origin:left center}.evidence-copy footer{position:absolute;right:24px;bottom:20px;font:900 14px ArchivoBlack;letter-spacing:.12em;color:#686868}
.feature-spread{display:grid;grid-template-columns:1.18fr .82fr;padding:128px 76px 70px;gap:44px}.feature-spread figure{height:854px;border-top:14px solid var(--red)}.feature-spread article{padding:28px 24px}.feature-spread article>p{font:900 17px ArchivoBlack;letter-spacing:.15em;color:var(--red)}.feature-spread h2{font:400 102px/.88 Anton;margin:28px 0 56px}.feature-spread blockquote{font:700 42px/1.28 Georgia,serif}.feature-spread article i{display:block;width:150px;height:10px;background:var(--red);margin:42px 0 28px}.feature-spread article footer{font:900 15px ArchivoBlack;letter-spacing:.11em}
.compare-feature{padding:128px 76px 74px}.compare-grid{height:790px;display:grid;grid-template-columns:1fr 1fr;gap:18px}.compare-grid figure{border-top:13px solid var(--red)}.compare-feature h2{position:absolute;z-index:4;left:50%;bottom:60px;transform:translateX(-50%) rotate(-1deg);white-space:nowrap;background:var(--ink);color:var(--paper);padding:14px 28px;font:400 72px Anton;text-transform:uppercase}.compare-rule{position:absolute;z-index:3;left:50%;top:118px;width:12px;height:864px;background:var(--red);transform:translateX(-50%)}
.stat-feature{background:var(--ink);color:var(--paper)}.stat-number{position:absolute;left:90px;top:190px;display:flex;align-items:flex-end}.stat-number b{font:400 440px/.72 Anton;color:var(--red)}.stat-number span{font:400 104px/.85 Anton;margin-left:24px;margin-bottom:32px}.stat-feature article{position:absolute;left:1040px;right:100px;top:265px}.stat-feature article p{font:900 19px ArchivoBlack;letter-spacing:.15em;color:var(--gray);margin-bottom:30px}.stat-feature article h2{font:400 99px/.9 Anton;text-transform:uppercase}.stat-feature article h3{font:600 24px/1.4 Archivo;color:var(--gray);margin-top:34px}.stat-rail{position:absolute;left:90px;right:90px;bottom:82px;height:14px;background:linear-gradient(90deg,var(--red) 0 62%,#383838 62%)}
.diagram-feature{padding:140px 76px 70px}.diagram-head{display:flex;align-items:flex-start;justify-content:space-between;gap:80px}.diagram-head p{font:900 18px ArchivoBlack;letter-spacing:.15em;color:var(--red);padding-top:16px}.diagram-head h2{font:400 92px/.9 Anton;text-align:right;text-transform:uppercase}.diagram-rule{height:11px;background:var(--red);margin:58px 0 86px;transform-origin:left}.diagram-flow{display:flex;align-items:center;justify-content:center;gap:54px}.diagram-node{position:relative;width:330px;height:230px;border:4px solid var(--ink);border-top:18px solid var(--ink);display:flex;flex-direction:column;align-items:center;justify-content:center}.diagram-node:not(:last-child):after{content:"";position:absolute;right:-58px;top:100px;width:55px;height:8px;background:var(--red)}.diagram-node b{font:400 58px Anton}.diagram-node span{font:900 15px ArchivoBlack;letter-spacing:.15em;color:#6a6a6a;margin-top:10px}.diagram-feature footer{position:absolute;left:76px;bottom:48px;font:900 14px ArchivoBlack;letter-spacing:.14em;color:#777}
.roster-feature{padding:126px 76px 64px}.roster-grid{height:788px;display:grid;grid-template-columns:1.38fr .72fr;grid-template-rows:1fr 1fr;gap:18px}.roster-main{grid-row:1/3}.roster-feature h2{position:absolute;right:108px;bottom:74px;background:var(--paper);padding:20px 24px;font:400 68px/.92 Anton;text-align:right}.interview-slug{inset:auto auto 60px 72px;width:780px;height:176px;background:var(--paper);color:var(--ink);border-left:15px solid var(--red);padding:24px 34px;box-shadow:18px 18px 0 rgba(13,13,13,.55)}.interview-slug span{font:900 13px ArchivoBlack;letter-spacing:.15em;color:#777}.interview-slug p{font:900 17px ArchivoBlack;letter-spacing:.12em;color:var(--red);margin-top:8px}.interview-slug h2{font:400 55px Anton;margin-top:4px}
.archive-feature{background:transparent;color:var(--paper)}.archive-video{left:82px;top:146px;right:auto;bottom:auto;width:1156px;height:806px;object-fit:contain;background:#050505}.archive-frame{position:absolute;left:70px;top:134px;width:1180px;height:830px;border:12px solid var(--paper);box-shadow:22px 22px 0 rgba(178,43,26,.56);overflow:hidden}.timecode{position:absolute;left:18px;bottom:15px;background:var(--ink);padding:7px 10px;font:900 12px ArchivoBlack;letter-spacing:.12em}.archive-feature article{position:absolute;left:1340px;right:74px;top:210px}.archive-feature article p{font:900 16px ArchivoBlack;letter-spacing:.15em;color:#d75544}.archive-feature h2{font:400 76px/.9 Anton;margin:26px 0 48px}.archive-feature blockquote{font:700 38px/1.22 Georgia,serif}.archive-feature article i{display:block;width:150px;height:10px;background:var(--red);margin:42px 0 28px}.archive-feature footer{font:900 13px ArchivoBlack;letter-spacing:.14em;color:#777}
.closing-summary{background:var(--ink);color:var(--paper);padding:150px 86px 80px}.closing-summary h2{position:relative;z-index:2;font:400 128px/.83 Anton;letter-spacing:.01em}.closing-summary h2 em{font-style:normal;color:#d75544}.closing-list{position:absolute;z-index:2;right:86px;top:220px;width:620px;display:grid;gap:14px}.closing-list span,.closing-list b{border-top:4px solid #555;padding:13px 0;font:900 28px ArchivoBlack;letter-spacing:.11em}.closing-list b{color:#d75544;border-color:var(--red)}.closing-red{position:absolute;right:-240px;bottom:-380px;width:900px;height:900px;border-radius:50%;background:var(--red);opacity:.22}
.page-mast{left:300px;right:330px}.page-mast span{color:#5d5d5d}.page-mast.light span{color:#b5b5b5}.page-number{bottom:24px;color:#5d5d5d}.folio,.video-copy span{color:#8b8b8b}.photo-deck{right:150px}.diagram-feature footer,.feature-spread article footer{color:#5d5d5d}.chapter-tab{inset:auto;right:auto;bottom:auto;width:auto;height:auto}
'''


CHAPTERS = {
    "R1": "01 / THE ROLE", "T1": "02 / THE TURN", "W1": "03 / THE WORKOUT",
    "D1": "04 / THE DIET", "P1": "05 / PRACTICE", "S1": "06 / THE RESULTS", "E1V4": "07 / THE POINT",
}


def build_html() -> str:
    scenes = "\n".join(SCENES[bid] for bid, _ in BLOCKS)
    tabs = "\n".join(
        f'''<div id="chapter-{bid.lower()}" class="clip chapter-tab" data-start="{f(STARTS[bid])}" data-duration="4.4" data-track-index="78" data-layout-allow-overlap data-layout-allow-occlusion>{escape(label)}</div>'''
        for bid, label in CHAPTERS.items()
    )
    return f'''<!doctype html><html lang="en" data-resolution="landscape"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1920,height=1080"/><script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{STYLE}</style></head><body><div id="root" data-composition-id="main" data-duration="{f(TOTAL)}" data-width="1920" data-height="1080" data-fps="30">
{scenes}{tabs}<div class="brand-bug" data-layout-allow-overlap data-layout-allow-occlusion>CELEB WORKOUT</div><div class="texture"></div>
<audio id="master-audio" src="assets/audio/narration.wav" data-start="0" data-duration="{f(TOTAL)}" data-track-index="90" data-volume="1"></audio>
</div><script>
window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
document.querySelectorAll('.video-layout').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration,v=document.getElementById(el.dataset.videoId),copy=el.querySelector('.video-copy');tl.fromTo(v,{{scale:1.045}},{{scale:1.005,duration:Math.max(.5,d-.1),ease:'none'}},s+.02);if(copy){{tl.set(copy,{{opacity:1,y:70}},s+.12);tl.to(copy,{{y:0,duration:.42,ease:'power4.out'}},s+.12)}}}});
document.querySelectorAll('.feature-opener').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration,p=el.querySelector('.opener-page'),v=document.getElementById(el.dataset.videoId);tl.fromTo(p,{{xPercent:102}},{{xPercent:0,duration:.72,ease:'power3.inOut'}},s+.08);tl.fromTo(v,{{scale:1.07}},{{scale:1.01,duration:Math.max(.6,d-.1),ease:'none'}},s+.02);el.querySelectorAll('h1 span').forEach((line,i)=>{{tl.set(line,{{opacity:1,y:80}},s+.62+i*.14);tl.to(line,{{y:0,duration:.22,ease:'power4.out'}},s+.62+i*.14)}})}});
document.querySelectorAll('.photo-feature,.roster-feature').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration;el.querySelectorAll('figure').forEach((fig,i)=>{{tl.set(fig,{{opacity:1,y:70}},s+.1+i*.12);tl.to(fig,{{y:0,duration:.42,ease:'power4.out'}},s+.1+i*.12);tl.fromTo(fig.querySelector('img'),{{scale:1.06}},{{scale:1.01,duration:Math.max(.5,d-.2),ease:'none'}},s+.05)}})}});
document.querySelectorAll('.evidence-spread').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration,img=el.querySelector('.evidence-visual'),mark=el.querySelector('mark i');tl.fromTo(img,{{clipPath:'inset(0 100% 0 0)'}},{{clipPath:'inset(0 0% 0 0)',duration:.72,ease:'power3.inOut'}},s+.08);tl.fromTo(mark,{{scaleX:0}},{{scaleX:1,duration:.58,ease:'power2.out'}},s+Math.min(2.0,d*.32));tl.fromTo(el.querySelector('.evidence-copy'),{{x:55}},{{x:0,duration:.65,ease:'power4.out'}},s+.18)}});
document.querySelectorAll('.feature-spread').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration,fig=el.querySelector('figure');tl.fromTo(fig,{{clipPath:'inset(0 0 100% 0)'}},{{clipPath:'inset(0 0 0% 0)',duration:.72,ease:'power3.inOut'}},s+.08);tl.fromTo(fig.querySelector('img'),{{scale:1.07}},{{scale:1.01,duration:Math.max(.5,d-.2),ease:'none'}},s+.06);tl.set(el.querySelector('article'),{{opacity:1,y:55}},s+.28);tl.to(el.querySelector('article'),{{y:0,duration:.42,ease:'power4.out'}},s+.28)}});
document.querySelectorAll('.compare-feature').forEach((el)=>{{const s=+el.dataset.start;const figs=el.querySelectorAll('figure');tl.fromTo(figs[0],{{x:-220}},{{x:0,duration:.62,ease:'power4.out'}},s+.05);tl.fromTo(figs[1],{{x:220}},{{x:0,duration:.62,ease:'power4.out'}},s+.11);tl.fromTo(el.querySelector('h2'),{{scale:1.18,y:30}},{{scale:1,y:0,duration:.42,ease:'power4.out'}},s+.55)}});
document.querySelectorAll('.stat-feature').forEach((el)=>{{const s=+el.dataset.start;tl.set(el.querySelector('.stat-number'),{{opacity:1,y:100}},s+.12);tl.to(el.querySelector('.stat-number'),{{y:0,duration:.48,ease:'power4.out'}},s+.12);tl.fromTo(el.querySelector('article'),{{x:80}},{{x:0,duration:.55,ease:'power4.out'}},s+.34)}});
document.querySelectorAll('.diagram-feature').forEach((el)=>{{const s=+el.dataset.start;tl.fromTo(el.querySelector('.diagram-rule'),{{scaleX:0}},{{scaleX:1,duration:.58,ease:'power2.out'}},s+.1);el.querySelectorAll('.diagram-node').forEach((n,i)=>{{tl.set(n,{{opacity:1,y:70}},s+.35+i*.12);tl.to(n,{{y:0,duration:.36,ease:'power4.out'}},s+.35+i*.12)}})}});
document.querySelectorAll('.archive-feature').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration,v=document.getElementById(el.dataset.videoId);tl.fromTo(el.querySelector('.archive-frame'),{{x:-120}},{{x:0,duration:.62,ease:'power4.out'}},s+.06);tl.fromTo(el.querySelector('article'),{{x:100}},{{x:0,duration:.62,ease:'power4.out'}},s+.16);tl.fromTo(v,{{scale:1.035}},{{scale:1,duration:Math.max(.5,d-.2),ease:'none'}},s+.04)}});
document.querySelectorAll('.interview-slug,.chapter-tab,.montage-copy').forEach((el)=>{{const s=+el.dataset.start;tl.set(el,{{opacity:1,x:-130}},s+.1);tl.to(el,{{x:0,duration:.45,ease:'power4.out'}},s+.1)}});
document.querySelectorAll('.closing-list>*').forEach((el,i)=>{{const s={f(STARTS['E1V4'])}+.2+i*.13;tl.set(el,{{opacity:1,y:55}},s);tl.to(el,{{y:0,duration:.18,ease:'power4.out'}},s)}});
window.__timelines['main']=tl;
</script></body></html>'''


(ROOT / "index.html").write_text(build_html(), encoding="utf-8")
(ROOT / "index.motion.json").write_text(json.dumps({
    "duration": TOTAL,
    "maxStaticSec": 15,
    "assertions": [
        {"kind": "appearsBy", "selector": "#opener-i1", "bySec": 0.6},
        {"kind": "appearsBy", "selector": "#evidence-h2", "bySec": STARTS["H2"] + 2.5},
        {"kind": "appearsBy", "selector": "#roster-w1", "bySec": STARTS["W1"] + 2.2},
        {"kind": "appearsBy", "selector": "#evidence-s4", "bySec": STARTS["S4"] + 2.5},
        {"kind": "staysInFrame", "selector": "#id-t2"},
        {"kind": "staysInFrame", "selector": "#summary-e1v4"},
    ],
}, indent=2), encoding="utf-8")
print(ROOT / "index.html")
