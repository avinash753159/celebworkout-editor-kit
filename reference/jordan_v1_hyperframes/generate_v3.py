from __future__ import annotations

import json
import urllib.parse
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
audio = json.loads((ROOT / "audio_manifest.json").read_text(encoding="utf-8-sig"))
BLOCKS = [(item["id"], float(item["start"])) for item in audio["blocks"]]
STARTS = dict(BLOCKS)
TOTAL = float(audio["duration"])
ENDS = {bid: (BLOCKS[i + 1][1] if i + 1 < len(BLOCKS) else TOTAL) for i, (bid, _) in enumerate(BLOCKS)}


def f(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def dur(block: str) -> float:
    return ENDS[block] - STARTS[block]


def attrs(uid: str, block: str, track: int = 0) -> str:
    return f'id="{uid}" data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}" data-track-index="{track}"'


def video(block: str, asset: str, eyebrow: str = "", headline: str = "", *, uid: str | None = None,
          treatment: str = "full", position: str = "50% 50%", start: float | None = None,
          duration: float | None = None) -> str:
    clip_start = STARTS[block] if start is None else start
    clip_duration = dur(block) if duration is None else duration
    name = uid or f"v-{block.lower()}"
    overlay = ""
    if eyebrow or headline:
        overlay = f'''<div class="video-caption" data-layout-allow-overlap><p data-layout-allow-overlap>{escape(eyebrow)}</p><h2 data-layout-allow-overlap>{headline}</h2></div>'''
    return f'''<video id="{name}" class="clip scene-video video-scene" src="assets/video/{escape(asset)}" data-start="{f(clip_start)}" data-duration="{f(clip_duration)}" data-track-index="0" data-media-start="0" muted playsinline style="object-position:{escape(position)}"></video>
    <div id="{name}-layer" class="clip video-layer video-{treatment}" data-start="{f(clip_start)}" data-duration="{f(clip_duration)}" data-track-index="3"><div class="video-vignette"></div>{overlay}</div>'''


def montage(block: str, assets: list[str], eyebrow: str, headline: str) -> str:
    length = dur(block)
    unit = length / len(assets)
    parts = []
    for index, asset in enumerate(assets):
        start = STARTS[block] + unit * index
        current = length - unit * index if index == len(assets) - 1 else unit
        parts.append(video(block, asset, uid=f"v-{block.lower()}-{index}", start=start, duration=current))
    parts.append(f'''<div id="o-{block.lower()}" class="clip montage-label" data-start="{f(STARTS[block])}" data-duration="{f(min(length, 6.8))}" data-track-index="4">
      <p>{escape(eyebrow)}</p><h2>{headline}</h2></div>''')
    return "\n".join(parts)


def photo_story(block: str, images: list[tuple[str, str]], eyebrow: str, headline: str) -> str:
    cards = "".join(
        f'''<figure data-layout-allow-overflow><img src="assets/images/{escape(src)}"/><figcaption>{escape(label)}</figcaption></figure>'''
        for src, label in images
    )
    return f'''<div {attrs(f"p-{block.lower()}", block)} class="clip photo-story cols-{len(images)}" data-layout-allow-occlusion>
      <div class="photo-grid">{cards}</div><div class="photo-copy"><p>{escape(eyebrow)}</p><h2>{headline}</h2></div>
    </div>'''


def source_page(block: str, publication: str, date: str, headline: str, before: str, marked: str,
                after: str, source_url: str, *, dark: bool = False) -> str:
    domain = urllib.parse.urlparse(source_url).netloc.replace("www.", "")
    variant = " source-dark" if dark else ""
    return f'''<div {attrs(f"src-{block.lower()}", block)} class="clip source-scene{variant}">
      <div class="source-desk"><div class="source-page">
        <div class="source-mast"><strong>{escape(publication)}</strong><span>{escape(date)}</span></div>
        <div class="source-rule"></div><h2>{escape(headline)}</h2>
        <p class="source-body">{escape(before)} <span class="marker"><i></i>{escape(marked)}</span> {escape(after)}</p>
        <div class="source-meta">SOURCE &nbsp;·&nbsp; {escape(domain)}</div>
      </div></div><div class="focus-corner">SOURCE / EVIDENCE</div>
    </div>'''


def type_video(block: str, asset: str, line1: str, line2: str, eyebrow: str) -> str:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080"><text x="960" y="515" text-anchor="middle" font-family="Impact,Arial Black" font-size="255" fill="white">{escape(line1)}</text><text x="960" y="780" text-anchor="middle" font-family="Impact,Arial Black" font-size="255" fill="white">{escape(line2)}</text></svg>'''
    mask = urllib.parse.quote(svg)
    uid = f"type-{block.lower()}"
    return f'''<video id="{uid}-ghost" class="clip type-ghost" src="assets/video/{escape(asset)}" data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}" data-track-index="0" data-media-start="0" muted playsinline></video>
      <video id="{uid}-fill" class="clip type-fill" src="assets/video/{escape(asset)}" data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}" data-track-index="1" data-media-start="0" muted playsinline style="-webkit-mask-image:url('data:image/svg+xml,{mask}');mask-image:url('data:image/svg+xml,{mask}');-webkit-mask-mode:alpha;mask-mode:alpha"></video>
      <div {attrs(uid, block, 4)} class="clip type-overlay"><p>{escape(eyebrow)}</p><div class="type-edge"></div><div class="type-words"><span>{escape(line1)}</span><span>{escape(line2)}</span></div></div>'''


def compare(block: str, left: str, right: str, left_label: str, right_label: str, headline: str) -> str:
    return f'''<div {attrs(f"cmp-{block.lower()}", block)} class="clip compare-scene">
      <div class="compare-panel left"><img src="assets/images/{escape(left)}"/><span>{escape(left_label)}</span></div>
      <div class="compare-panel right"><img src="assets/images/{escape(right)}"/><span>{escape(right_label)}</span></div>
      <div class="compare-strike" data-layout-allow-overflow></div><h2>{headline}</h2>
    </div>'''


def number_scene(block: str, eyebrow: str, number: str, unit: str, headline: str, sub: str = "") -> str:
    return f'''<div {attrs(f"num-{block.lower()}", block)} class="clip number-scene" data-layout-allow-overlap>
      <div class="number-grid"></div><p data-layout-allow-overlap>{escape(eyebrow)}</p><div class="number" data-layout-allow-overlap><b data-layout-allow-overlap>{escape(number)}</b><span data-layout-allow-overlap>{escape(unit)}</span></div>
      <h2 data-layout-allow-overlap>{headline}</h2><h3 data-layout-allow-overlap>{escape(sub)}</h3>
    </div>'''


def diagram(block: str, eyebrow: str, headline: str, steps: list[tuple[str, str]]) -> str:
    nodes = "".join(f'''<div class="diagram-node"><b>{escape(big)}</b><span>{escape(small)}</span></div>''' for big, small in steps)
    return f'''<div {attrs(f"diag-{block.lower()}", block)} class="clip diagram-scene">
      <p>{escape(eyebrow)}</p><h2>{headline}</h2><div class="diagram-flow">{nodes}</div>
    </div>'''


def book(block: str, eyebrow: str, title: str, quote: str, source: str, image: str) -> str:
    return f'''<div {attrs(f"book-{block.lower()}", block)} class="clip book-scene">
      <div class="book-grid"></div><div class="book-wrap">
        <section class="book-page book-left"><p>{escape(eyebrow)}</p><h2>{escape(title)}</h2><div class="book-photo"><img src="assets/images/{escape(image)}"/></div></section>
        <section class="book-page book-right"><span>FIELD NOTE / SOURCE</span><blockquote>“{escape(quote)}”</blockquote><i></i><footer>{escape(source)}</footer></section>
      </div>
    </div>'''


def people(block: str) -> str:
    persons = [
        ("scottie_pippen.jpg", "SCOTTIE PIPPEN"),
        ("ron_harper.jpg", "RON HARPER"),
        ("randy_brown.jpg", "RANDY BROWN"),
    ]
    cards = "".join(f'''<figure><img src="assets/images/{src}"/><span>{name}</span></figure>''' for src, name in persons)
    return f'''<div {attrs("people-w1", block)} class="clip people-scene"><div class="people-row">{cards}</div>
      <div class="people-title"><p>5–7 A.M. · HIGHLAND PARK</p><h2>THE BREAKFAST <em>CLUB</em></h2></div></div>'''


def lower_interview(block: str, asset: str, name: str, role: str) -> str:
    return video(block, asset, treatment="interview") + f'''<div id="lt-{block.lower()}" class="clip interview-id" data-start="{f(STARTS[block])}" data-duration="{f(min(dur(block), 6.0))}" data-track-index="5">
      <p>{escape(role)}</p><h2>{escape(name)}</h2></div>'''


def archive_interview(block: str, asset: str, role: str, pullquote: str) -> str:
    timing = f'data-start="{f(STARTS[block])}" data-duration="{f(dur(block))}"'
    return f'''<div id="ai-bg-{block.lower()}" class="clip archive-interview-bg" {timing} data-track-index="0">
      <div class="archive-side"><p>ARCHIVAL TAPE · MICHAEL JORDAN</p><h2>{escape(role)}</h2><i></i><blockquote>{escape(pullquote)}</blockquote><span>PRIMARY-SOURCE AUDIO</span></div></div>
      <video id="ai-{block.lower()}" class="clip scene-video video-scene archive-window-video" src="assets/video/{escape(asset)}" {timing} data-track-index="2" data-media-start="0" muted playsinline></video>'''


def summary_scene(block: str) -> str:
    return f'''<div {attrs("summary-e1", block)} class="clip summary-scene"><p>THE HONEST SUMMARY</p>
      <div class="summary-words"><span>SQUATS</span><span>SPRINTS</span><span>STRETCHING</span><span>STEAK</span><span>SLEEP</span><b>DECISION</b></div>
      <h2>THERE WAS NO TRICK.</h2></div>'''


SCENES: dict[str, str] = {
    "I1": type_video("I1", "intro_last_shot.mp4", "WHAT HE", "ACTUALLY DID", "MICHAEL JORDAN · THE SYSTEM BEHIND THE BODY"),
    "H1": video("H1", "pistons_contact.mp4", "THE PROBLEM", "THE BEST PLAYER IN THE LEAGUE.<br><em>STILL GOING HOME.</em>"),
    "H2": source_page("H2", "CBS SPORTS", "MAY 2020", "How Jordan built for Detroit", "Detroit eliminated Chicago in", "three consecutive postseasons: 1988, 1989 and 1990.", "Twice, the loss came in the Conference Finals.", "https://www.cbssports.com/nba/news/how-michael-jordan-bulked-up-to-outmuscle-pistons-win-first-nba-championship-with-bulls"),
    "H3": video("H3", "jordan_rules.mp4", "DETROIT'S PLAN", "THE JORDAN <em>RULES</em>"),
    "R1": photo_story("R1", [("mj_family_young.jpg", "WILMINGTON"), ("mj_young1.jpg", "AGE 21"), ("mj_young2.jpg", "NORTH CAROLINA")], "THE ORIGIN STORY", "LEFT OFF VARSITY.<br><em>NOT LEFT BEHIND.</em>"),
    "R2": photo_story("R2", [("mj_laney_action.jpg", "THE WORK"), ("mj_laney_dunk.jpg", "THE GROWTH")], "THE BACK GARDEN", "LARRY WON.<br>MICHAEL <em>RETURNED.</em>"),
    "R3": book("R3", "NORTH CAROLINA · 1982", "THE SHOT", "A freshman takes the final shot of the national championship.", "DEAN SMITH / UNIVERSITY OF NORTH CAROLINA", "dean_smith.jpg"),
    "R4": montage("R4", ["rookie_1984.mp4", "boston_63.mp4", "defense_1988.mp4"], "1984 → 1988", "BRILLIANCE <em>WITHOUT THE RING.</em>"),
    "R5": video("R5", "dirty_defense.mp4", "DETROIT", "EVERY POSSESSION<br><em>EXPENSIVE.</em>"),
    "R6": compare("R6", "mj_skinny.jpg", "mj_built.jpg", "1985 · 195 LB", "MID-90s · BUILT FOR CONTACT", "THE FRAME <em>CHANGED</em>"),
    "R7": type_video("R7", "mvp_1988.mp4", "ENGINEERING", "PROBLEM", "SUMMER · 1990"),
    "T1": photo_story("T1", [("mj_grover_gq_2000.jpg", "JORDAN + GROVER"), ("mj_grover_press.jpg", "THE PARTNERSHIP")], "CHICAGO · 1989", "ONE TRAINER.<br><em>ALMOST NO CLIENTS.</em>"),
    "T2": lower_interview("T2", "bite_grover_letter.mp4", "TIM GROVER", "HOW THE LETTER REACHED JORDAN"),
    "T3": source_page("T3", "BASKETBALL NETWORK", "ORAL HISTORY", "The letter that found Jordan", "Grover learned Jordan was tired of", "being knocked around by Detroit", "and wrote directly to the player with a reason to answer.", "https://www.basketballnetwork.net/latest-news/tim-grover-reveals-how-he-ended-up-becoming-michael-jordans-personal-trainer"),
    "T3b": number_scene("T3b", "THE AGREEMENT", "30", "DAYS", "BECAME <em>15 YEARS</em>", "Nothing more — unless it worked."),
    "T3c": photo_story("T3c", [("tim_grover_b.jpg", "THE TRAINER"), ("mj_grover_training.jpg", "THE WORK")], "THE FIRST PROGRAM", "BUILD THE BODY.<br><em>KEEP THE GAME.</em>"),
    "T4": lower_interview("T4", "bite_grover_program.mp4", "TIM GROVER", "THE FIRST PROGRAM"),
    "T5": compare("T5", "mj_skinny2.jpg", "mj_built2.jpg", "THE TALENT", "THE ARMOR", "≈15 LB <em>OF MUSCLE</em>"),
    "W1": people("W1"),
    "W1b": video("W1b", "arriving_to_practice.mp4", "BEFORE DAWN", "THE DAY STARTED<br><em>BEFORE THE ARENA.</em>"),
    "W1c": lower_interview("W1c", "bite_grover_breakfast.mp4", "TIM GROVER", "THE BREAKFAST CLUB ROUTINE"),
    "W1d": video("W1d", "finals_backstage_1996.mp4", "THE SECOND THREE-PEAT", "BY THEN, THIS WAS<br><em>THE TEAM'S MORNING.</em>"),
    "W2": type_video("W2", "bulls_backstage_1998.mp4", "UNGLAMOROUS", "ON PURPOSE", "THE PROGRAM"),
    "W3": diagram("W3", "THE PROGRAM", "BASE → FORCE → CONTROL", [("SQUAT", "BASE"), ("CLEAN", "FORCE"), ("STEP-UP", "TRANSFER"), ("CORE", "CONTROL")]),
    "W4": source_page("W4", "BASKETBALL NETWORK", "TIM GROVER", "The set never ended at six", "Grover would prescribe six repetitions.", "Jordan did twelve — every set.", "The harder job was getting him to stop.", "https://www.basketballnetwork.net/old-school/tim-grover-said-michael-jordan-gained-15-pounds-to-beat-bad-boy-pistons"),
    "W6": book("W6", "ARCHIVE TRANSCRIPT", "NO SECRET EXERCISE", "Conditioning and nutrition are very important. I used to work out every single day.", "MICHAEL JORDAN / RECORDED AT THE TIME", "mj_dunk87.jpg"),
    "W7": archive_interview("W7", "bite_mj_conditioning.mp4", "CONDITIONING + WEIGHTS", "WEIGHTS. AEROBIC WORK. EVERY DAY."),
    "W8": number_scene("W8", "LISTEN TO THE ORDER", "01", "FIRST", "CONDITIONING<br><em>BEFORE WEIGHTS.</em>"),
    "W9": diagram("W9", "JORDAN'S OWN SEQUENCE", "PREPARE → CONDITION → LOAD", [("STRETCH", "MOBILITY"), ("SPRINT", "STAMINA"), ("LIFT", "STRENGTH")]),
    "W10": video("W10", "bench_strategy.mp4", "THE DETAIL IN THE PHOTOGRAPHS", "LOOK AT<br><em>THE SHORTS.</em>"),
    "W11": source_page("W11", "TIM GROVER", "INTERVIEW TRANSCRIPT", "A recovery signal hidden in plain sight", "He told Jordan to", "grab the hem of his shorts instead of leaning on his knees.", "It reduced the load without broadcasting exhaustion.", "https://www.youtube.com/watch?v=lfCZOKhWqWU", dark=True),
    "W12": diagram("W12", "A PROGRAM FOR A BODY", "LEFT ≠ RIGHT", [("MEASURE", "ASYMMETRY"), ("ADJUST", "LOAD"), ("TEST", "MOVEMENT")]),
    "W13": book("W13", "TRAIN THE ATHLETE — NOT THE CHART", "ASYMMETRY", "One hand might carry fifty pounds while the other carried ten. The objective was balance in motion.", "TIM GROVER / TRAINING ACCOUNT", "bulls_practice_trio.jpg"),
    "W14": number_scene("W14", "PRO BASKETBALL", "1990", "THE TURN", "WEIGHTS WERE STILL<br><em>THE ENEMY.</em>", "Players feared losing their shooting touch."),
    "W14b": video("W14b", "running_with_bulls.mp4", "CHIP SCHAEFER", "HE ARRIVED AT<br><em>EXACTLY THAT MOMENT.</em>"),
    "W14d": lower_interview("W14d", "bite_schaefer_1990.mp4", "CHIP SCHAEFER", "BULLS HEAD ATHLETIC TRAINER · 1990"),
    "W14e": source_page("W14e", "CHIP SCHAEFER", "ORAL HISTORY", "The league catches up", "In 1990, weight training was", "only beginning to take hold across professional basketball.", "Jordan and Grover were already building for contact.", "https://www.youtube.com/watch?v=D1sKOv7WFBA"),
    "W15": photo_story("W15", [("mj_rookie_1985.jpg", "WHAT HE HAD"), ("mj_1996_built.jpg", "WHAT HE BUILT")], "THE FINISHED FRAME", "THE ROUTINE WAS COPYABLE.<br><em>THE APPETITE WASN'T.</em>"),
    "W16": video("W16", "rare_practice_1998.mp4", "THE PART YOU CANNOT PROGRAM", "RETURN TO THE<br><em>DISCOMFORT.</em>"),
    "D1": type_video("D1", "championship_archive.mp4", "THE", "DIET", "04 · INPUTS FOR THE WORK"),
    "D2": source_page("D2", "THE SPORTS RUSH", "REPORTING SUMMARY", "Against the era's orthodoxy", "The standard advice was carbohydrate loading:", "rice, pasta, bread — and more of it.", "Jordan's game-day plan went in the other direction.", "https://thesportsrush.com/nba-news-michael-jordan-had-the-most-odd-pregame-meal-tim-grover-explains-the-reason-behind-why-the-goat-used-to-eat-a-whole-steak-before-bulls-games/"),
    "D3": diagram("D3", "THE INPUTS", "BODY CHEMISTRY + ENERGY OUTPUT", [("BODY", "CHEMISTRY"), ("WORK", "DEMAND"), ("MEAL", "TIMING")]),
    "D4": source_page("D4", "SLAM", "GAME-DAY ROUTINE", "The unusual part was the clock", "Jordan's preferred game-day meal was", "steak and a potato, about four hours before tipoff.", "He said it provided energy and supported recovery.", "https://www.slamonline.com/the-magazine/michael-jordan-gameday-routine/", dark=True),
    "D5": diagram("D5", "A SIMPLE DAY", "THREE MEALS · TRAINING CLOCK", [("BREAKFAST", "FUEL"), ("PRACTICE", "WORK"), ("RECOVER", "EAT + REST")]),
    "D6": archive_interview("D6", "bite_mj_meals.mp4", "MEALS + RECOVERY", "THREE MEALS. TRAIN. RECOVER. REST."),
    "D7": source_page("D7", "TIM GROVER", "INTERVIEW TRANSCRIPT", "The diet argument, simplified", "Every nutrition plan can work", "if the athlete actually follows it.", "Fit the diet to the body, the workload, and the time horizon.", "https://www.youtube.com/watch?v=lfCZOKhWqWU"),
    "D8": book("D8", "THE PRINCIPLE", "THE BODY DECIDES", "The useful diet is the one that fits the athlete and survives long enough to matter.", "TIM GROVER / NUTRITION ACCOUNT", "tim_grover_a.jpg"),
    "P1": type_video("P1", "dream_team_practice.mp4", "PRACTICE IS", "COMPETITION", "05 · THE COMPONENT PEOPLE COPY LEAST"),
    "P2": archive_interview("P2", "bite_mj_practice.mp4", "PRACTICE AS A TEST", "THE GAME WAS NOTHING HE HADN'T REHEARSED."),
    "P3": video("P3", "jordan_practice.mp4", "THE STANDARD", "TEAMMATES FELT IT<br><em>EVERY DAY.</em>"),
    "P4": source_page("P4", "TIM GROVER", "SIDELINE ACCOUNT", "When the whistle blew", "The room went quiet. Jordan's rule was", "practice hard enough that the game becomes easier.", "The standard also filtered the roster.", "https://www.youtube.com/watch?v=PjSFlFqxyGc", dark=True),
    "P5": montage("P5", ["camp_shooting.mp4", "united_center_warmup.mp4"], "THE EQUATION", "HARDER PRACTICE.<br><em>EASIER GAME.</em>"),
    "S1": video("S1", "pistons_sweep_1991.mp4", "1991 · EASTERN CONFERENCE FINALS", "CHICAGO MET<br><em>DETROIT AGAIN.</em>"),
    "S2": montage("S2", ["first_ring_alt.mp4", "finals_1991.mp4"], "THE ANSWER", "4–0.<br><em>THEN THE FIRST RING.</em>"),
    "S3": video("S3", "flu_game_1997.mp4", "GAME 5 · 1997 FINALS", "38 POINTS.<br><em>BARELY STANDING.</em>"),
    "S4": source_page("S4", "BLEACHER REPORT", "TRAINER'S ACCOUNT", "The night before Game Five", "One pizza was delivered. Jordan was", "the only person in the room who ate it.", "Around three a.m., Grover found him curled into a ball.", "https://bleacherreport.com/articles/1608036-michael-jordans-trainer-says-mjs-famous-flu-game-was-result-of-poisoning"),
    "S5": source_page("S5", "THE LAST DANCE", "2020", "The account becomes public", "For twenty-three years the night was remembered as flu.", "Jordan later described food poisoning.", "The label changed. The performance did not.", "https://www.netflix.com/title/80203144", dark=True),
    "S6": video("S6", "flu_game_second.mp4", "DEPLETED · SHIVERING · STILL PLAYING", "THEN HE WALKED<br><em>ONTO THE FLOOR.</em>"),
    "S7": type_video("S7", "flu_game_backstory.mp4", "44", "MINUTES", "GAME 5 · UTAH · 1997"),
    "E1": summary_scene("E1"),
    "E2": type_video("E2", "seventy_two_ten.mp4", "TALENT", "BECAME SYSTEM", "THE FINISHED PRODUCT WAS BUILT"),
    "E3": archive_interview("E3", "bite_mj_outofshape.mp4", "LOSING CONDITIONING", "CONDITIONING IS PERISHABLE."),
    "E4": video("E4", "bulls_prime.mp4", "CELEB WORKOUT", "WHO SHOULD WE<br><em>TRAIN LIKE NEXT?</em>"),
}

expected = {bid for bid, _ in BLOCKS}
if set(SCENES) != expected:
    raise RuntimeError(f"Scene map mismatch. Missing={sorted(expected - set(SCENES))}; extra={sorted(set(SCENES) - expected)}")


STYLE = r'''
@font-face{font-family:Anton;src:url("assets/fonts/Anton-Regular.ttf") format("truetype")}
@font-face{font-family:Archivo;src:url("assets/fonts/Archivo-Regular.ttf") format("truetype");font-weight:400}
@font-face{font-family:Archivo;src:url("assets/fonts/Archivo-Medium.ttf") format("truetype");font-weight:600}
@font-face{font-family:ArchivoBlack;src:url("assets/fonts/ArchivoBlack-Regular.ttf") format("truetype");font-weight:900}
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1920px;height:1080px;overflow:hidden;background:#0d0d0d}body{font-family:Archivo,Arial,sans-serif;color:#f4f2ef}#root{position:relative;width:1920px;height:1080px;overflow:hidden;background:#0d0d0d}.clip{position:absolute;inset:0;overflow:hidden}.scene-video{width:100%;height:100%;object-fit:cover;background:#0d0d0d}.video-scene{background:#0d0d0d}.video-vignette{position:absolute;inset:0;background:linear-gradient(90deg,rgba(13,13,13,.92),rgba(13,13,13,.16) 66%,rgba(13,13,13,.28)),linear-gradient(0deg,rgba(13,13,13,.75),transparent 55%)}.video-interview .video-vignette{background:linear-gradient(0deg,rgba(13,13,13,.38),transparent 48%)}.video-caption{position:absolute;left:104px;bottom:92px;width:1160px}.video-caption p,.montage-label p{font:900 23px/1 ArchivoBlack;letter-spacing:.15em;color:#a9a9a9;margin-bottom:18px}.video-caption p:before,.montage-label p:before{content:"";display:inline-block;width:104px;height:9px;background:#b22b1a;margin-right:20px}.video-caption h2,.montage-label h2{font:400 112px/.92 Anton;text-transform:uppercase;letter-spacing:.01em;text-wrap:balance}.video-caption em,.montage-label em{font-style:normal;color:#b22b1a}.montage-label{display:flex;flex-direction:column;justify-content:flex-end;padding:0 104px 90px;background:linear-gradient(0deg,rgba(13,13,13,.86),transparent 74%)}.photo-story{background:#f4f2ef;color:#0d0d0d;padding:58px 62px}.photo-grid{display:grid;grid-template-columns:repeat(2,1fr);height:794px;gap:20px}.cols-3 .photo-grid{grid-template-columns:repeat(3,1fr)}.photo-grid figure{position:relative;overflow:hidden;background:#252525;border-top:14px solid #b22b1a}.photo-grid img{width:100%;height:100%;object-fit:cover;filter:saturate(.88) contrast(1.04)}.photo-grid figcaption{position:absolute;left:18px;bottom:18px;background:#0d0d0d;color:#f4f2ef;padding:9px 13px;font:900 20px ArchivoBlack;letter-spacing:.06em}.photo-copy{height:178px;padding:27px 10px 0;display:flex;justify-content:space-between;align-items:flex-start;gap:40px}.photo-copy p{font:900 21px ArchivoBlack;letter-spacing:.13em;color:#b22b1a;padding-top:10px}.photo-copy h2{font:400 74px/.92 Anton;text-align:right;text-transform:uppercase}.photo-copy em{font-style:normal;color:#b22b1a}.source-scene{background:#d8d3ca;color:#171717;padding:58px 106px}.source-desk{height:960px;background:linear-gradient(135deg,#b9b3a8,#ece7dd);padding:46px 180px;box-shadow:inset 0 0 160px rgba(13,13,13,.28)}.source-page{position:relative;height:868px;background:#f4f2ef;padding:74px 88px 62px;box-shadow:0 30px 60px rgba(13,13,13,.34);transform-origin:center center}.source-dark{background:#0d0d0d}.source-dark .source-desk{background:linear-gradient(135deg,#161616,#333)}.source-mast{display:flex;justify-content:space-between;align-items:center;font:900 25px ArchivoBlack;letter-spacing:.12em}.source-mast span{font:600 17px Archivo;color:#686868}.source-rule{height:8px;background:#b22b1a;margin:24px 0 48px}.source-page h2{font:400 76px/.96 Anton;text-transform:uppercase;max-width:1180px;margin-bottom:58px}.source-body{font:400 47px/1.42 Georgia,serif;max-width:1240px}.marker{position:relative;z-index:1;font-weight:700;padding:0 4px}.marker i{position:absolute;z-index:-1;left:-5px;right:-5px;bottom:2px;height:83%;background:rgba(178,43,26,.34);transform-origin:left center}.source-meta{position:absolute;bottom:44px;left:88px;font:900 17px ArchivoBlack;letter-spacing:.12em;color:#676767}.focus-corner{position:absolute;right:36px;top:42px;writing-mode:vertical-rl;font:900 15px ArchivoBlack;letter-spacing:.14em;color:#f4f2ef;background:#0d0d0d;padding:14px 10px;border-bottom:5px solid #b22b1a}.type-video{background:#0d0d0d}.type-ghost,.type-fill{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.type-ghost{filter:blur(18px) saturate(.65);opacity:.16;transform:scale(1.08)}.type-fill{-webkit-mask-size:100% 100%;mask-size:100% 100%;-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;filter:saturate(1.15) contrast(1.08)}.type-video p{position:absolute;left:0;right:0;top:110px;text-align:center;font:900 22px ArchivoBlack;letter-spacing:.18em;color:#a9a9a9}.type-edge{position:absolute;left:50%;top:155px;width:190px;height:11px;background:#b22b1a;transform:translateX(-50%)}.compare-scene{display:grid;grid-template-columns:1fr 1fr;background:#0d0d0d}.compare-panel{position:relative;overflow:hidden}.compare-panel img{width:100%;height:100%;object-fit:cover}.compare-panel:after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(13,13,13,.84),transparent 58%)}.compare-panel span{position:absolute;z-index:2;bottom:58px;left:62px;background:#0d0d0d;padding:10px 16px;border-left:9px solid #b22b1a;font:900 23px ArchivoBlack;letter-spacing:.06em}.compare-panel.right span{left:auto;right:62px}.compare-strike{position:absolute;z-index:3;left:50%;top:-120px;width:22px;height:1320px;background:#b22b1a;transform:rotate(8deg)}.compare-scene h2{position:absolute;z-index:4;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-2deg);white-space:nowrap;background:#f4f2ef;color:#0d0d0d;padding:20px 36px;font:400 82px Anton;text-transform:uppercase}.compare-scene h2 em{font-style:normal;color:#b22b1a}.number-scene,.diagram-scene,.summary-scene{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:#0d0d0d;padding:92px}.number-grid,.book-grid{position:absolute;inset:0;background-image:linear-gradient(rgba(169,169,169,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(169,169,169,.08) 1px,transparent 1px);background-size:82px 82px}.number-scene>p,.diagram-scene>p,.summary-scene>p{z-index:1;font:900 24px ArchivoBlack;letter-spacing:.16em;color:#a9a9a9;margin-bottom:24px}.number{z-index:1;display:flex;align-items:flex-end;gap:22px}.number b{font:400 290px/.75 Anton;color:#b22b1a}.number span{font:400 96px/.8 Anton;padding-bottom:16px}.number-scene h2{z-index:1;font:400 105px/.92 Anton;text-transform:uppercase;margin-top:40px}.number-scene h2 em{font-style:normal;color:#b22b1a}.number-scene h3{z-index:1;font:600 26px Archivo;margin-top:24px;color:#a9a9a9}.diagram-scene{background:#f4f2ef;color:#0d0d0d}.diagram-scene>p{color:#b22b1a}.diagram-scene h2{font:400 105px/.9 Anton;text-transform:uppercase;margin-bottom:80px}.diagram-flow{display:flex;align-items:stretch;justify-content:center;gap:78px}.diagram-node{position:relative;width:310px;height:210px;background:#0d0d0d;color:#f4f2ef;border-top:15px solid #b22b1a;display:flex;flex-direction:column;align-items:center;justify-content:center}.diagram-node:not(:last-child):after{content:"→";position:absolute;right:-63px;top:60px;color:#b22b1a;font:400 65px Anton}.diagram-node b{font:400 56px Anton}.diagram-node span{font:900 18px ArchivoBlack;letter-spacing:.13em;color:#a9a9a9;margin-top:10px}.book-scene{background:#cfc9bf;padding:74px 104px;perspective:1800px}.book-wrap{position:absolute;inset:82px 120px;display:grid;grid-template-columns:1fr 1fr;filter:drop-shadow(0 35px 34px rgba(13,13,13,.34))}.book-page{background:#f4f2ef;color:#0d0d0d;padding:76px 70px;overflow:hidden}.book-left{border-right:2px solid #bab5ad;transform-origin:right center}.book-right{transform-origin:left center}.book-left>p{font:900 20px ArchivoBlack;letter-spacing:.14em;color:#b22b1a}.book-left>h2{font:400 100px/.9 Anton;margin-top:26px}.book-photo{height:520px;margin-top:42px;overflow:hidden;border-top:13px solid #b22b1a}.book-photo img{width:100%;height:100%;object-fit:cover}.book-right>span{font:900 18px ArchivoBlack;letter-spacing:.13em;color:#777}.book-right blockquote{font:700 48px/1.28 Georgia,serif;margin-top:80px}.book-right i{display:block;width:190px;height:12px;background:#b22b1a;margin:48px 0 28px}.book-right footer{font:900 18px ArchivoBlack;letter-spacing:.1em}.people-scene{background:#0d0d0d;padding:58px 68px 160px}.people-row{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;height:780px}.people-row figure{position:relative;overflow:hidden;border-top:15px solid #b22b1a}.people-row img{width:100%;height:100%;object-fit:cover}.people-row span{position:absolute;left:20px;bottom:18px;background:#0d0d0d;padding:10px 15px;font:900 22px ArchivoBlack}.people-title{position:absolute;left:74px;right:74px;bottom:38px;display:flex;align-items:flex-end;justify-content:space-between}.people-title p{font:900 20px ArchivoBlack;letter-spacing:.13em;color:#a9a9a9}.people-title h2{font:400 78px Anton}.people-title em{font-style:normal;color:#b22b1a}.interview-id{inset:auto auto 62px 76px;width:950px;height:174px;background:#f4f2ef;color:#0d0d0d;border-left:16px solid #b22b1a;padding:28px 36px;box-shadow:16px 16px 0 rgba(13,13,13,.7)}.interview-id p{font:900 19px ArchivoBlack;letter-spacing:.12em;color:#b22b1a;margin-bottom:8px}.interview-id h2{font:400 58px Anton}.summary-scene{align-items:flex-start;text-align:left}.summary-words{display:flex;flex-wrap:wrap;gap:16px;width:1510px}.summary-words span,.summary-words b{font:400 80px Anton;background:#f4f2ef;color:#0d0d0d;padding:8px 19px}.summary-words b{background:#b22b1a;color:#f4f2ef}.summary-scene h2{font:400 132px Anton;margin-top:56px}.summary-scene>p{color:#b22b1a}.chapter-tab{position:absolute;z-index:48;left:0;top:45px;background:#0d0d0d;border-left:12px solid #b22b1a;padding:13px 24px 12px 30px;font:900 16px ArchivoBlack;letter-spacing:.14em}.brand-bug{position:absolute;z-index:49;right:48px;top:39px;background:#0d0d0d;border-bottom:4px solid #b22b1a;padding:10px 13px;font:900 16px ArchivoBlack;letter-spacing:.17em}.texture{position:absolute;z-index:50;inset:0;pointer-events:none;opacity:.1;background-image:repeating-linear-gradient(0deg,transparent 0,transparent 3px,rgba(255,255,255,.09) 4px)}
.type-overlay{background:transparent}.type-overlay p{position:absolute;left:0;right:0;top:110px;text-align:center;font:900 22px ArchivoBlack;letter-spacing:.18em;color:#a9a9a9}.type-words{position:absolute;left:0;right:0;top:296px;display:flex;flex-direction:column;align-items:center;font:400 255px/.99 Anton;text-transform:uppercase;white-space:nowrap;color:transparent;-webkit-text-stroke:2px rgba(244,242,239,.32)}
.chapter-tab{right:auto;bottom:auto;width:max-content;height:auto}.brand-bug{left:auto;bottom:auto;width:max-content;height:auto}.book-right>span{color:#6e6e6e}
.archive-interview-bg{background:#d7d2c8;color:#111;padding:80px 72px}.archive-interview-bg:before{content:"";position:absolute;left:58px;top:66px;width:1214px;height:852px;background:#111;box-shadow:24px 24px 0 rgba(13,13,13,.2)}.archive-window-video{left:88px;top:96px;right:auto;bottom:auto;width:1154px;height:792px;object-fit:contain;background:#080808;filter:saturate(.78) contrast(1.06)}.archive-side{position:absolute;right:74px;top:166px;width:520px}.archive-side>p{font:900 18px ArchivoBlack;letter-spacing:.15em;color:#ac2919}.archive-side h2{font:400 76px/.92 Anton;text-transform:uppercase;margin-top:26px}.archive-side i{display:block;width:160px;height:10px;background:#b22b1a;margin:36px 0}.archive-side blockquote{font:700 38px/1.18 Georgia,serif}.archive-side span{display:block;margin-top:42px;font:900 16px ArchivoBlack;letter-spacing:.14em;color:#5b5b5b}.type-words{color:#0d0d0d;-webkit-text-fill-color:#0d0d0d;opacity:.28}.video-caption em,.montage-label em{color:#bd4839}
'''


CHAPTERS = {
    "R1": "01 · THE ROLE", "T1": "02 · THE TURN", "W1": "03 · THE WORKOUT",
    "D1": "04 · THE DIET", "P1": "05 · PRACTICE", "S1": "06 · THE RESULTS", "E1": "07 · THE POINT",
}


def build_html() -> str:
    scenes = "\n".join(SCENES[bid] for bid, _ in BLOCKS)
    tabs = "\n".join(
        f'''<div id="chapter-{bid.lower()}" class="clip chapter-tab" data-start="{f(STARTS[bid])}" data-duration="4.4" data-track-index="8">{escape(label)}</div>'''
        for bid, label in CHAPTERS.items()
    )
    return f'''<!doctype html><html lang="en" data-resolution="landscape"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1920,height=1080"/><script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{STYLE}</style></head><body><div id="root" data-composition-id="main" data-duration="{f(TOTAL)}" data-width="1920" data-height="1080" data-fps="30">
{scenes}{tabs}<div class="brand-bug">CELEB WORKOUT</div><div class="texture"></div>
<audio id="master-audio" src="assets/audio/narration.wav" data-start="0" data-duration="{f(TOTAL)}" data-track-index="10" data-volume="1"></audio>
</div><script>
window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
document.querySelectorAll('video.video-scene').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration;tl.fromTo(el,{{scale:1.045}},{{scale:1.0,duration:Math.max(.25,d-.1),ease:'none'}},s+.03);const layer=document.getElementById(el.id+'-layer'),c=layer?layer.querySelector('.video-caption'):null;if(c){{tl.fromTo(c,{{y:70,opacity:0}},{{y:0,opacity:1,duration:.64,ease:'expo.out'}},s+.18)}}}});
document.querySelectorAll('.source-scene').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration,p=el.querySelector('.source-page'),m=el.querySelector('.marker i');tl.fromTo(p,{{scale:1.04,y:24}},{{scale:1.0,y:-12,duration:Math.max(.5,d-.2),ease:'none'}},s+.03);tl.fromTo(m,{{scaleX:0}},{{scaleX:1,duration:.82,ease:'power3.out'}},s+Math.min(2.1,d*.3));}});
document.querySelectorAll('.photo-story').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration;el.querySelectorAll('figure').forEach((fig,i)=>{{tl.fromTo(fig,{{y:100,opacity:0}},{{y:0,opacity:1,duration:.62,ease:'expo.out'}},s+.12+i*.14);tl.fromTo(fig.querySelector('img'),{{scale:1.08}},{{scale:1.015,duration:Math.max(.5,d-.25),ease:'none'}},s+.08)}})}});
document.querySelectorAll('.compare-scene').forEach((el)=>{{const s=+el.dataset.start;tl.fromTo(el.querySelector('.left'),{{x:-260}},{{x:0,duration:.72,ease:'expo.out'}},s+.05);tl.fromTo(el.querySelector('.right'),{{x:260}},{{x:0,duration:.72,ease:'expo.out'}},s+.12);tl.fromTo(el.querySelector('h2'),{{scale:1.35,opacity:0}},{{scale:1,opacity:1,duration:.52,ease:'expo.out'}},s+.62)}});
document.querySelectorAll('video.type-fill').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration;tl.fromTo(el,{{scale:1.14,opacity:0}},{{scale:1,opacity:1,duration:.75,ease:'expo.out'}},s+.1);tl.fromTo(el,{{x:-12}},{{x:12,duration:Math.max(.4,d-.9),ease:'none'}},s+.82)}});
document.querySelectorAll('.number-scene').forEach((el)=>{{const s=+el.dataset.start;tl.fromTo(el.querySelector('.number'),{{scale:1.5,opacity:0}},{{scale:1,opacity:1,duration:.62,ease:'expo.out'}},s+.18);tl.fromTo(el.querySelector('h2'),{{y:60,opacity:0}},{{y:0,opacity:1,duration:.52,ease:'power4.out'}},s+.58)}});
document.querySelectorAll('.diagram-scene').forEach((el)=>{{const s=+el.dataset.start;el.querySelectorAll('.diagram-node').forEach((n,i)=>tl.fromTo(n,{{y:90,opacity:0}},{{y:0,opacity:1,duration:.5,ease:'power4.out'}},s+.35+i*.2))}});
document.querySelectorAll('.book-scene').forEach((el)=>{{const s=+el.dataset.start,d=+el.dataset.duration;tl.fromTo(el.querySelector('.book-left'),{{rotationY:-76}},{{rotationY:0,duration:.8,ease:'expo.out'}},s+.08);tl.fromTo(el.querySelector('.book-right'),{{rotationY:76}},{{rotationY:0,duration:.8,ease:'expo.out'}},s+.08);tl.fromTo(el.querySelector('.book-wrap'),{{scale:1}},{{scale:1.075,x:-36,duration:Math.max(.5,d-.95),ease:'none'}},s+.88)}});
document.querySelectorAll('.interview-id,.chapter-tab,.montage-label').forEach((el)=>{{const s=+el.dataset.start;tl.fromTo(el,{{x:-140,opacity:0}},{{x:0,opacity:1,duration:.55,ease:'expo.out'}},s+.12)}});
document.querySelectorAll('.summary-words>*').forEach((el,i)=>{{const s={f(STARTS['E1'])};tl.fromTo(el,{{y:65,opacity:0}},{{y:0,opacity:1,duration:.4,ease:'power4.out'}},s+.25+i*.14)}});
window.__timelines['main']=tl;
</script></body></html>'''


(ROOT / "index.html").write_text(build_html(), encoding="utf-8")
(ROOT / "index.motion.json").write_text(json.dumps({
    "duration": TOTAL,
    "maxStaticSec": 15,
    "assertions": [
        {"kind": "appearsBy", "selector": "#type-i1", "bySec": 0.5},
        {"kind": "appearsBy", "selector": "#src-h2", "bySec": STARTS["H2"] + 3.0},
        {"kind": "appearsBy", "selector": "#people-w1", "bySec": STARTS["W1"] + 2.5},
        {"kind": "appearsBy", "selector": "#src-s4", "bySec": STARTS["S4"] + 3.0},
        {"kind": "staysInFrame", "selector": "#lt-t2"},
        {"kind": "staysInFrame", "selector": "#summary-e1"},
    ],
}, indent=2), encoding="utf-8")
print(ROOT / "index.html")
