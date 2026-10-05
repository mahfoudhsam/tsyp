"""Builds docs/Living_Map_Technical_Report.pdf (IEEE-style, two columns, 6 pages) from the diagrams and docs/results.json.
Usage: python3 tools/build_report.py"""
import os, json, statistics as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, FrameBreak, NextPageTemplate, KeepTogether, Preformatted, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

HERE = os.path.dirname(os.path.abspath(__file__)); DOCS = os.path.join(HERE, "..", "docs"); DIA = os.path.join(DOCS, "diagrams")
R = json.load(open(os.path.join(DOCS, "results.json"))); NR = json.load(open(os.path.join(DOCS, "nav_results.json")))
FD = "/usr/share/fonts/truetype/dejavu/"
for n, f in (("Body", "DejaVuSerifCondensed.ttf"), ("Body-B", "DejaVuSerifCondensed-Bold.ttf"), ("Body-I", "DejaVuSerifCondensed-Italic.ttf"), ("Body-BI", "DejaVuSerifCondensed-BoldItalic.ttf"), ("Mono", "DejaVuSansMono.ttf"), ("Sans-B", "DejaVuSansCondensed-Bold.ttf"), ("Sans", "DejaVuSansCondensed.ttf")):
    pdfmetrics.registerFont(TTFont(n, FD + f))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-B", italic="Body-I", boldItalic="Body-BI")

PW, PH = letter; M = 0.55 * 72; W = PW - 2 * M; GAP = 0.22 * 72; CW = (W - GAP) / 2
BODY = ParagraphStyle("body", fontName="Body", fontSize=8.7, leading=10.5, alignment=TA_JUSTIFY, spaceAfter=3.6)
H1 = ParagraphStyle("h1", fontName="Sans-B", fontSize=9.2, leading=11.2, spaceBefore=6, spaceAfter=3, textColor=colors.HexColor("#0d2a5c"), alignment=TA_LEFT)
H2 = ParagraphStyle("h2", fontName="Body-BI", fontSize=8.7, leading=10.5, spaceBefore=2.5, spaceAfter=1.5)
BUL = ParagraphStyle("bul", parent=BODY, leftIndent=9, bulletIndent=1, spaceAfter=1.6)
CAP = ParagraphStyle("cap", fontName="Body-I", fontSize=7.6, leading=9, alignment=TA_JUSTIFY)
TC = ParagraphStyle("tc", fontName="Body", fontSize=7.2, leading=8.4, alignment=TA_LEFT)
TCB = ParagraphStyle("tcb", parent=TC, fontName="Body-B")
TCAP = ParagraphStyle("tcap", fontName="Sans-B", fontSize=7.2, leading=8.6, alignment=TA_CENTER, spaceBefore=3, spaceAfter=2)
TITLE = ParagraphStyle("title", fontName="Sans-B", fontSize=17, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#0d2a5c"))
SUB = ParagraphStyle("sub", fontName="Body-I", fontSize=9, leading=11, alignment=TA_CENTER)
AUTH = ParagraphStyle("auth", fontName="Body", fontSize=8, leading=10, alignment=TA_CENTER)
ABS = ParagraphStyle("abs", parent=BODY, fontName="Body-B", fontSize=8.3, leading=10)

def P(t): return Paragraph(t, BODY)
def B(t): return Paragraph(t, BUL, bulletText="\u2022")
def tbl(rows, widths, head=True, cap=None, zebra=True):
    data = [[Paragraph(str(c), TCB if (head and i == 0) else TC) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    ts = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#90a4ae")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2.2), ("RIGHTPADDING", (0, 0), (-1, -1), 2.2), ("TOPPADDING", (0, 0), (-1, -1), 1.3), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3)]
    if head: ts.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe8f5")))
    if zebra:
        for i in range(2, len(rows), 2): ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f6f8fb")))
    t.setStyle(TableStyle(ts)); out = [Paragraph(cap, TCAP)] if cap else []
    return KeepTogether(out + [t, Spacer(1, 3)])

# ------------------------------------------------------------------ page templates: figure zone on top (drawn by onPage), two text columns below
FIGS = {2: [("architecture.png", "Fig. 1. System architecture. The robots live inside; the van (Outside Network Area) is the only crossing; the Command Post is outside. Numbers 1-5 mark the flows.")],
        3: [("sequence_compact.png", "Fig. 2. End-to-end sequence from detection to a finished rescue. Every message between a robot and the Command Post passes through the van.")],
        4: [("beacon_frame.png", "Fig. 3. Beacon v2: 32 bytes. Positions are egocentric (ahead / right of the parent beacon), so no absolute coordinate exists inside the building.")],
        5: [("fig_priority.png", "Fig. 4. The two clocks. (a) The priority number pi falls while an event waits, so it becomes more urgent. (b) The confidence in an observation decays: fire and gas go stale fast."),
            ("fig_results.png", "Fig. 5. Results. (a) Time to the first person: blind robot, Executor after briefing, and end to end. (b) Uplink delay by priority class. (c) Fires put out under rising radio loss per wall (simulation, seed 7).")]}
def fig_geom(png):
    from PIL import Image
    w, h = Image.open(os.path.join(DIA, png)).size; return W, W * h / w
CAPH = 27.0
def zone_h(k):
    if k not in FIGS: return 0.0
    return sum(fig_geom(png)[1] + CAPH + 4 for png, _ in FIGS[k]) + 4
def make_onpage(k):
    def f(c, doc):
        c.saveState()
        if k in FIGS:
            y = PH - M
            for png, cap in FIGS[k]:
                w, h = fig_geom(png); c.drawImage(ImageReader(os.path.join(DIA, png)), M, y - h, w, h, mask="auto")
                p = Paragraph(cap, CAP); p.wrap(W, 40); p.drawOn(c, M, y - h - 3 - p.height); y -= h + CAPH + 4
        c.setFont("Sans", 6.5); c.setFillColor(colors.HexColor("#607d8b"))
        c.drawString(M, M - 14, "The Living Map - TSYP14 Phase 1 technical report"); c.drawRightString(PW - M, M - 14, f"{doc.page}")
        c.restoreState()
    return f
def frames_for(k):
    top = 222.0 if k == 1 else zone_h(k)
    colh = PH - 2 * M - top; fr = []
    if k == 1: fr.append(Frame(M, PH - M - top, W, top, id="top1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0))
    fr += [Frame(M, M, CW, colh, id=f"c1_{k}", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0), Frame(M + CW + GAP, M, CW, colh, id=f"c2_{k}", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]
    return fr
doc = BaseDocTemplate(os.path.join(DOCS, "Living_Map_Technical_Report.pdf"), pagesize=letter, leftMargin=M, rightMargin=M, topMargin=M, bottomMargin=M,
                      title="The Living Map: Spatial Memory for Emergency Robots - TSYP14 Phase 1 technical report", author="Team (to be filled)", subject="IEEE RAS x AESS TSYP14 Technical Challenge")
doc.addPageTemplates([PageTemplate(id=f"p{k}", frames=frames_for(k), onPage=make_onpage(k)) for k in range(1, 7)])

# ------------------------------------------------------------------ numbers from the measurements
S = R["baseline_seeds"]; fp = st.mean(v["first_person_s"] for v in S.values()); bl = st.mean(v["blind_first_person_s"] for v in S.values())
sent_unique = sum(v["beacons"] for v in S.values()); recv_unique = sum(min(v["beacons"], int(v["delivery"].split("/")[0])) for v in S.values())
perr = st.mean(v["pos_err_m"] for v in S.values()); e2e = st.mean(v["first_person_end_to_end_s"] for v in S.values()); wfp = st.mean(v["writer_first_reachable_person_s"] for v in S.values()); wdone = st.mean(v["writer_done_s"] for v in S.values()); IM, BA = R["uplink_immediate"], R["uplink_batched"]; RF = R["rf_stress"]
fp_s = f"{fp:.0f}"; bl_s = f"{bl:.0f}"
S7 = S["7"]; ords = [v["orders"] for v in S.values()]; upds = [v["order_updates"] for v in S.values()]
lost_seeds = [(int(v["beacons"]) - min(v["beacons"], int(v["delivery"].split("/")[0]))) for v in S.values()]; n_lossy = sum(1 for x in lost_seeds if x > 0)
wl = R["fault_writer_lost"]; wl_got = min(wl["beacons"], int(wl["delivery"].split("/")[0]))
d30 = RF["30 dB/wall"]["delivery"].split("/"); d30_got, d30_att = int(d30[0]), int(d30[1])
def rng(a, b, sep='-'): return str(a) if a == b else f'{a}{sep}{b}'
words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
arena = R["proto_arena_seeds"]; arena_steam = sum(1 for v in arena.values() if v["steam_rejected"] >= 1); arena_debris = sum(1 for v in arena.values() if "DEBRIS" in v["event_types"])

story = [NextPageTemplate(["p2", "p3", "p4", "p5", "p6"])]
# ------------------------------------------------------------------ title block
story += [Paragraph("The Living Map: Spatial Memory for Emergency Robots", TITLE), Spacer(1, 3),
          Paragraph("A two-robot chain that leaves its knowledge in radio beacons, for a GPS-denied Fire / Hazardous Building", SUB), Spacer(1, 5),
          Paragraph("[Team name]  -  [Member 1, Member 2, Member 3, Member 4]  -  IEEE RAS x AESS Tunisia Section, TSYP14 Technical Challenge", AUTH),
          Paragraph("Phase 1 (initial phase) technical report  -  October 2026", AUTH), Spacer(1, 6),
          Paragraph("<b>Abstract.</b> When a robot fails inside a fire-damaged building, everything it learned disappears with it. We give the building its own memory. A <i>Writer</i> robot explores a GPS-denied, two-storey building, detects fire, gas leaks, people, animals and rubble, and leaves 32-byte radio beacons that say what was found, where, and when. An <i>Outside Network Area</i> (a van) is the only link between inside and outside: it decodes the beacons, converts their private coordinates into GPS, and forwards them to a <i>Command Post</i> that ranks the events, combines related ones into single orders, and briefs the <i>Executor</i> robots, which navigate using the inherited information. Robots never talk to each other or to the Command Post directly. "
                    f"In simulation over five seeds, once briefed, an Executor reaches a person {fp_s} s after leaving the van instead of {bl_s} s when the same robot searches blind. End to end the Writer's exploration dominates: the first reachable person is found after {wfp:.0f} s and reached after {e2e:.0f} s, later than that blind find, but the whole building is handled (all four fires out, four of five victims rescued, the fifth sealed behind rubble and flagged for human rescue) without any robot searching blind inside the hazard. The mean position error is {perr:.2f} m and {100*recv_unique/sent_unique:.0f} % of the beacons reach the Command Post. We also report where the design breaks, notably under very strong radio attenuation.", ABS),
          FrameBreak()]

# ------------------------------------------------------------------ I. introduction
story += [Paragraph("I. INTRODUCTION", H1),
          P("In collapsed buildings, mines and fire-damaged structures, robots must explore, sense and communicate without GPS and with little connectivity. The knowledge a robot collects is lost when it fails, leaves or runs out of power. The TSYP14 challenge asks for a system that can <i>sense, communicate, preserve critical information and enable mission continuity</i>. We chose the <b>Fire / Hazardous Building</b> environment and built the full chain: Writer, beacons, Outside Network Area, Command Post, Executors."),
          P("<b>Contributions.</b> (1) A 32-byte <i>egocentric</i> beacon with integrity check and mirror frames. (2) A strictly air-gapped star topology with one crossing; a test fails if any robot listens to anything but the van. (3) A <i>two-clock</i> priority model, a configurable 1 s decision cycle, incident grouping, preemption and replanning at the Command Post. (4) Executor navigation that does not merely replay the Writer's trail. (5) A failure analysis backed by stress tests, including the cases where the design fails."),
          P("<b>Method.</b> The whole chain runs in a Python simulator of a two-floor building (48 x 24 m, 0.5 m cells, 4 fires, 1 gas leak, 1 steam source, 3 people, 2 animals, rubble, stairs and an atrium). The ROS 2 nodes are thin wrappers around the same code. Robots receive only sensor readings and briefings: they never read the world file. All numbers below come from <font name='Mono'>tools/collect_results.py</font> and can be reproduced."),
          tbl([["Challenge aspect (poster)", "Where", "Evidence"],
               ["Writer autonomy", "III", "frontier exploration, 2 floors, budget of 44 beacons"],
               ["Event detection, beacon deposition", "III", "5 event types, steam rejected, repeaters"],
               ["Beacon message, signal design", "IV", "32 B frame, CRC16 + MAC, aging, RF model"],
               ["Frame translation", "V", f"local to WGS84, {perr:.2f} m mean error"],
               ["Outside Network Area", "VI", "van gateway, only crossing, adaptive queue"],
               ["Executor robot", "VII", f"briefing, A*, {fp_s} s to a person vs {bl_s} s blind"],
               ["Diagrams, failure cases, plan", "II, IX, X", "Figs. 1-3, five stress-tested cases, BOM"]], [CW * 0.42, CW * 0.13, CW * 0.45], cap="TABLE I. COVERAGE OF THE CHALLENGE ASPECTS")]

# ------------------------------------------------------------------ II. architecture
story += [Paragraph("II. SYSTEM ARCHITECTURE", H1),
          P("Fig. 1 shows the three zones. <b>Inside</b> (ROS 2 domain 10) are the Writer, the beacon mesh and three Executors: an ambulance for people and animals, a fire truck for floor-0 fires and gas leaks, and a drone for upper floors that uses the stairs and the atrium. The challenge requires at least two physical robots; the simulation has four, and the prototype of Phase 2 will have two (Section X). The <b>Outside Network Area</b> is a van: it is the only point where inside and outside meet, over a UDP uplink (port 9101) and downlink (9102). The <b>Command Post</b> (domain 20) is outside."),
          P("<b>No direct link, not even a hidden one.</b> Robots publish only to the van and listen only to the van. In an earlier version the ambulance read the state that the fire truck had written into a beacon, which is an indirect robot-to-robot channel; we removed it. Now \"hazard cleared\" reaches the ambulance as a message from the Command Post, relayed by the van. <font name='Mono'>audit.py</font> lists the topics each robot subscribes to and a test fails on any violation. The only exception is the simulator's physics topic, which is not communication. The robot-to-van radio is an ideal channel marked <i>protocol TBD</i>."),
          P("<b>Data flow</b> (Fig. 2). The Writer senses and drops a beacon (1-2); the mesh relays it by RF to the van (3); the van verifies, chains the hops, translates to GPS and queues it (4); the uplink delivers it to the Command Post (5), which every second updates priorities, correlates and chooses robots (6), and sends a briefing and the first order (7); the van hands it over before the robot enters (8). While inside, the robot reports status through the van (10-11) and receives updates the same way (12-13) until it returns (15).")]

# ------------------------------------------------------------------ III. writer
story += [Paragraph("III. WRITER ROBOT: AUTONOMY AND EVENT DETECTION", H1),
          P("<b>Outdoors, then no GPS.</b> The Writer starts at the van, outside the building, and drives to the entrance door steering by GNSS fixes (noise sigma 0.8 m, an assumed value; the last 2.5 m use the LiDAR to find the door gap). No drift builds up and nothing is beaconed outdoors. At the threshold GPS is lost: the private frame is anchored on the last GNSS fix and only LiDAR and odometry remain. <b>Sensing and exploration.</b> The Writer is a tracked robot (it climbs stairs) with a 2D LiDAR (180 rays, 6 m), an air-temperature sensor, a thermal camera and a gas sensor. Its odometry drifts 1 % per metre. It explores by frontiers over its own occupancy map, uses the stairs to reach the second floor, and has a budget of 44 beacons, which forces it to choose what to record."),
          P("<b>Detection.</b> A fire needs at least two of three votes (air above 70 C, thermal maximum above 150 C, gas above 50 ppm) for three consecutive ticks. A steam pipe heats the air without a hot thermal signature, so it gets fewer than two votes and is counted as <i>steam rejected</i> and never beaconed. A gas leak is tracked to its plume peak so that the beacon points at the source (class P0 above 500 ppm). People and animals are thermal blobs with confidence of at least 0.6, persisting. Rubble that blocks a route becomes a <i>debris</i> beacon with the flag <font name='Mono'>human_intervention_required</font>."),
          P(f"<b>Classes.</b> The Writer sets a 2-bit class: P0 critical (a person near fire or gas), P1 high (a fallen person, a spreading fire), P2 medium (animal), P3 routine or blocked (debris). When its best uplink falls below -80 dBm it drops a <i>repeater</i> beacon: {S7['repeaters']} of the {S7['beacons']} beacons of the baseline run are repeaters, which shows how much of the beacon budget the radio can consume (Section IX)."),
          tbl([["Class", "Typical events (as beaconed by the Writer)", "Relay and Command Post action"],
               ["P0 critical", "person in danger near fire or gas; gas peak above 500 ppm", "at once with context; may skip the collection wait"],
               ["P1 high", "fallen person; fire", "next batch (at once in immediate mode)"],
               ["P2 medium", "animal", "next batch; processed after P0 and P1"],
               ["P3 routine / blocked", "debris that needs human heavy rescue; stairs; repeaters", "next batch; the waypoint is flagged impassable"]],
              [CW * 0.2, CW * 0.45, CW * 0.35], cap="TABLE II. EVENT TAXONOMY AND GATEWAY ACTION")]

# ------------------------------------------------------------------ IV. beacon
story += [Paragraph("IV. BEACON MESSAGE AND SIGNAL DESIGN", H1),
          P("<b>Frame</b> (Fig. 3). Each beacon is 32 bytes: type, class and flags, floor, victim count, heading, an egocentric hop to its parent (ahead, right, in decimetres), an egocentric target offset, the parent id, temperature, gas, the id and sequence of a neighbour (<i>mirror frame</i>), a CRC16 and a 3-byte truncated HMAC-SHA256. Egocentric hops mean that no absolute coordinate exists inside the building and that Writer drift does not accumulate: the van chains the hops from the entrance. A forged packet that the simulation injects at t = 30 s is rejected by the CRC/MAC check (the demo key is a constant; Phase 2 provisions a key per deployment)."),
          P("<b>Radio model</b> (assumed values). RSSI = -40 - 28 log<sub>10</sub>(d) - 12 dB per wall - 4 dB per rubble pile - 18 dB per floor slab. The packet error rate is 0 above -85 dBm, rises to 0.9 at -95 dBm and is 1 below. Each hop uses three attempts (ARQ); relays store and forward, including ancestors whose packets were lost earlier."),
          P("<b>Aging.</b> We keep two clocks (Fig. 4). The <i>confidence</i> of an observation decays as C(t) = e<super>-&lambda;t</super> with &lambda; = 0.10 per minute for fire and gas (they change fast) and 0.01 per minute for people and animals. The gateway queue score is S = (P<sub>base</sub> W N + H) C (1 + &beta; w), with P<sub>base</sub> = 10, 6, 3, 1 for classes P0 to P3, W = 3 for a person and 1 for an animal, N victims, H = 10 for gas and 6 for fire, and w the waiting time. At the Command Post, urgency is the <i>priority number</i> &pi;: lower means more urgent, and it <i>falls</i> while an event stays unresolved (Section VI).")]

# ------------------------------------------------------------------ V. frame translation
story += [Paragraph("V. FRAME TRANSLATION", H1),
          P("The anchor (&phi;<sub>0</sub>, &lambda;<sub>0</sub>, &theta;<sub>0</sub>) is the last GNSS fix at the entrance door. A private point (x, y) becomes X = x cos&theta;<sub>0</sub> - y sin&theta;<sub>0</sub>, Y = x sin&theta;<sub>0</sub> + y cos&theta;<sub>0</sub>, then &phi; = &phi;<sub>0</sub> + Y/M and &lambda; = &lambda;<sub>0</sub> + X/(N cos&phi;<sub>0</sub>), where M and N are the WGS84 meridian and prime-vertical radii at &phi;<sub>0</sub> (more accurate than one Earth radius). The demo anchor is 36.8065 N, 10.1815 E, &theta;<sub>0</sub> = 45 deg. Each record carries an uncertainty &sigma;(d) = sqrt(0.5<sup>2</sup> + (0.02 d)<sup>2</sup> + (d &middot; 2 deg)<sup>2</sup>) m at distance d from the anchor. Measured position error of the target: mean "
            f"{perr:.2f} m, maximum 0.47 m (seed 7). The Executor converts GPS back with the same anchor.")]

# ------------------------------------------------------------------ VI. ONA + CP
story += [Paragraph("VI. OUTSIDE NETWORK AREA AND COMMAND POST", H1),
          P("<b>Gateway.</b> The van rejects bad packets, drops duplicates by (id, seq), holds a packet until its parent has arrived, chains the hops, translates to GPS and queues the record. Class P0 and escalated records (a fire next to a person) go out at once <i>with their context</i>; other records leave when 120 s have passed, 8 are pending, or a score of 20 is reached. Immediate mode forwards every record. "
            f"Over one run, immediate mode sent {IM['uplink_messages']} uplink messages and batching {BA['uplink_messages']} (-{100*(1-BA['uplink_messages']/IM['uplink_messages']):.0f} %), with the same outcome, but batching delayed class P1 by {BA['delay_by_priority']['P1']['mean_s']:.0f} s on average (maximum {BA['delay_by_priority']['P1']['max_s']:.0f} s) and the mission ended {BA['end_s']-IM['end_s']} s later (Fig. 5b). Class P0 stayed at {BA['delay_by_priority']['P0']['mean_s']:.1f} s. Immediate mode is the default."),
          P("<b>Priority.</b> &pi;(t) = &pi;<sub>0</sub> e<super>-0.004 t</super>, with &pi;<sub>0</sub> = &pi;<sub>base</sub>(type) &times; class factor / N, where &pi;<sub>base</sub> = 3, 5, 6, 10, 30 for person, fire, gas, animal, debris and the class factor is 0.15, 1, 1.5, 2 for P0 to P3. A person in danger starts at 0.45, a fire at 5, a gas leak at 6, an animal at 15. The scale is 0 to +infinity, lower is more urgent, the half-life is 173 s, and the value never becomes negative. Age counts from the detection time, so repeated reports never reset it. A hazard in the same incident as a victim inherits 0.9 times the victim's value."),
          P(f"<b>Decision cycle.</b> The Command Post decides once per cycle (1 s, configurable) and never once per event: update &pi;, correlate, check robot health, replan running orders, then for each idle robot wait until the reports of the window are in. <i>Correlation</i> joins two events when at least one is a hazard, they are on the same floor, within 8 m and detected within 300 s; the grouping is transitive, so a fire, a gas leak and a person form one incident and one order. An event with &pi; below 0.3 skips the wait (<i>preemption</i>). In the baseline, "
            f"{S7['beacons']} beacons (about {S7['beacons']-S7['repeaters']} events plus {S7['repeaters']} repeaters) produced only <b>{rng(min(ords), max(ords))} orders</b> and {rng(min(upds), max(upds))} updates; the preemption path is covered by unit tests, not exercised in this scenario."),
          Preformatted("every cycle (1 s):\n  refresh pi_i = pi0_i * exp(-0.004 * age_i)\n  incidents = union-find(events related by\n      hazard, same floor, <= 8 m, <= 300 s)\n  mark robots silent > 35 s as LOST\n  for each running order: push ORDER_UPDATE if\n      new hazard / hazard cleared / new job\n  for each idle capable robot r:\n      jobs = incident jobs for r sorted by pi\n      if min(pi) < 0.3 or quiet for 1 s:\n          send ONE order(jobs) via the van", ParagraphStyle("code", fontName="Mono", fontSize=6.2, leading=7.4, leftIndent=4, spaceAfter=4, backColor=colors.HexColor("#f4f6f8"))),
          P("<b>Replanning.</b> A robot that is already inside receives an <font name='Mono'>ORDER_UPDATE</font> through the van when a hazard appears around its victim, a hazard is cleared, or a new job arrives. A robot silent for 35 s is marked lost and a capable robot takes its jobs. Executors are chosen by capability, not by a fixed table. The live map and the ranked orders are web pages (ports 8080, 8081).")]

# ------------------------------------------------------------------ VII. executors
story += [Paragraph("VII. EXECUTOR ROBOTS", H1),
          P("<b>Briefing.</b> Before entry the Executor receives, at the van, its targets (as GPS and as the chain of egocentric hops), the hazards, the stairs hints and the debris. It has no map. <b>Navigation.</b> It plans with A* straight to the target. Unknown cells are assumed passable but cost 0.6 more away from the Writer's trail, so the trail is a safe-route hint and not a rule; the robot replans from its own LiDAR when it sees a wall. For a floor change it plans to the stairs entry. With several jobs it orders them to minimise the urgency-weighted completion time (each job's completion time divided by its priority number, summed; exact for up to 7 jobs): urgent jobs first, unless a cheap one lies on the way."),
          P(f"<b>Measured gain</b> ({NR['n']} seeds, same maps, only the navigation differs; outcomes identical; times are the Executor's, from leaving the van): first person {NR['trail_first']:.1f} s to {NR['direct_first']:.1f} s (median {NR['trail_first_med']:.0f} to {NR['direct_first_med']:.0f} s), total distance {NR['trail_dist']:.0f} to {NR['direct_dist']:.0f} m (-{NR['dist_pct']} %), busy time {NR['trail_busy']:.0f} to {NR['direct_busy']:.0f} s (-{NR['busy_pct']} %), mission end {NR['trail_end']:.0f} to {NR['direct_end']:.0f} s. In {len(NR['worse'])} seeds the new method drove slightly more ({', '.join('+' + str(w) + ' %' for w in NR['worse'])}). <b>Behaviour.</b> The ambulance enters a danger zone only after the Command Post says the hazard is cleared (or its own thermal camera agrees); the fire truck keeps a stand-off and has a heat budget; the drone has a limited battery and a limited number of drops.")]

# ------------------------------------------------------------------ VIII. results
b7 = S["7"]
story += [Paragraph("VIII. RESULTS", H1),
          P(f"Table III gives the baseline over five seeds (one row per seed in Table IV) and the two faults of the challenge. <b>Two clocks must not be confused.</b> The Executor's search time (from leaving the van to a person) is {fp_s} s against {bl_s} s for the same robot searching blind. End to end, the Writer needs {wfp:.0f} s to find the first <i>reachable</i> person (it first reports an animal and a sealed person) and {wdone:.0f} s to finish exploring, so the first arrival is at {e2e:.0f} s (Fig. 5a). The benefit of the chain is that no robot searches blind inside the hazard, that one Writer pass serves every Executor, and that the whole building is handled; the cost is the Writer's exploration time. The Writer-lost run keeps working because the Command Post holds the memory, but the part of the building the Writer never reached stays unexplored."),
          tbl([["Scenario (simulation)", "1st person", "Fires out", "Rescued", "Beacons"],
               ["Blind robot alone (search time)", f"{bl_s} s", "-", "-", "-"],
               ["Baseline: Executor after briefing", f"{fp_s} s", "4/4 in all", "4/5 in all", f"{recv_unique}/{sent_unique} ({100*recv_unique/sent_unique:.0f} %)"],
               ["Baseline: end to end", f"{e2e:.0f} s", "4/4 in all", "4/5 in all", "-"],
               ["Beacon destroyed", f"{R['fault_beacon_destroyed']['first_person_s']:.0f} s", R["fault_beacon_destroyed"]["fires_out"], R["fault_beacon_destroyed"]["rescued"], "loss flagged"],
               ["Writer lost at 420 s", f"{R['fault_writer_lost']['first_person_s']:.0f} s", R["fault_writer_lost"]["fires_out"], R["fault_writer_lost"]["rescued"], f"{wl['beacons']} ({wl_got} delivered)"]],
              [CW * 0.38, CW * 0.14, CW * 0.14, CW * 0.14, CW * 0.20], cap="TABLE III. MEASURED RESULTS (SIMULATION)"),
          tbl([["Seed", "1st person", "Beacons delivered", "Position error", "Mission end"]] + [[k, f"{v['first_person_s']:.1f} s", f"{min(v['beacons'], int(v['delivery'].split('/')[0]))}/{v['beacons']}", f"{v['pos_err_m']:.2f} m", f"{v['end_s']} s"] for k, v in S.items()],
              [CW * 0.14, CW * 0.2, CW * 0.26, CW * 0.2, CW * 0.2], cap="TABLE IV. BASELINE RUNS, ONE ROW PER SEED"),
          P(f"The fifth person is sealed behind rubble in every run: the Writer flags it and the Executors skip it. In {words[n_lossy]} of five seeds a few beacons ({rng(min(x for x in lost_seeds if x), max(lost_seeds), ' to ')}) were never delivered after all retries; the missions still succeeded. A smaller 7.2 x 4.8 m prototype arena (Section X) completes on five seeds: fire out, 3/4 people rescued, all beacons delivered, and the steam false alarm rejected on {arena_steam} of 5 seeds (the debris beacon appears on {arena_debris} of 5, depending on the route).")]

# ------------------------------------------------------------------ IX. failure cases
rf = RF
story += [Paragraph("IX. FAILURE CASES", H1),
          tbl([["Case", "Mitigation", "Measured"],
               ["1 Beacon destroyed", "mirror frames; a neighbour re-broadcasts a lost beacon as BEACON_LOST", "BEACON_LOST record created; 4/4 fires, 4/5 rescued"],
               ["2 Writer trapped", "the van and Command Post keep the memory; Executors act alone", "2/4 fires, 3/5 rescued (unexplored area missed)"],
               ["3 Priority inversion, steam", "2-of-3 rule rejects steam; class P0 bypasses the queue; critical pi skips the wait", f"P0 delay {BA['delay_by_priority']['P0']['mean_s']:.1f} s even when batched; steam test and arena run reject it"],
               ["4 Impassable debris", "debris beacon with human_intervention_required; Executor skips", "skipped in every run, no robot stuck"],
               ["5 RF attenuation", "repeater beacons, ARQ, store-and-forward", f"fires out: 4/4 at 12 dB per wall, {rf['18 dB/wall']['fires_out']} at 18, {rf['24 dB/wall']['fires_out']} at 24, {rf['30 dB/wall']['fires_out']} at 30"]],
              [CW * 0.2, CW * 0.40, CW * 0.40], cap="TABLE V. FIVE FAILURE CASES AND THEIR MEASURED OUTCOME"),
          P("<b>Cases 1-4 in detail.</b> (1) Every beacon carries the id and sequence of a neighbour; when a node stops answering, a neighbour re-broadcasts the mirrored record as a <font name='Mono'>BEACON_LOST</font> packet, so the Command Post learns of the loss and keeps the last known data. (2) The Writer is killed at 420 s; because the van forwards each record at once, the Command Post already holds everything the Writer found, and the Executors finish what is known. (3) Steam is rejected by the 2-of-3 rule, and a person next to a fire is escalated so that it cannot wait in a batch. (4) Debris is a first-class event: the Executor plans around it and a sealed victim is handed to the human rescue team."),
          P(f"<b>Case 5 is where the design fails.</b> As the loss per wall rises the Writer drops more repeaters ({rf['12 dB/wall']['repeaters']}, {rf['18 dB/wall']['repeaters']}, {rf['24 dB/wall']['repeaters']}, {rf['30 dB/wall']['repeaters']}) and exhausts its 44-beacon budget before it has explored the building; at 30 dB per wall no packet gets through ({d30_got} delivered out of {d30_att:,} attempts). Measurements for 2.4 GHz [3] give about 1 dB for plywood but 15 dB for 102 mm and 29 dB for 203 mm of concrete, so the 12 dB baseline is realistic for light masonry and optimistic for heavy concrete. Our Phase 2 answers are a sub-GHz LoRa link, more and cheaper relays, and a beacon budget with a reserve for events.")]

# ------------------------------------------------------------------ X. phase 2
story += [Paragraph("X. PHASE 2 IMPLEMENTATION PLAN", H1),
          P("The finals ask for a physical prototype. We will build a modular 7.2 x 4.8 m arena from 12 mm plywood (8 sheets, 1.2 m hallways, 0.9 m doors, in the style of the RoboCup Rescue yellow arena [1][2]) with stand-ins: a heat lamp for fire, heated pads for victims, a kettle as the steam false alarm, foam rubble across a door, and one foil-lined wall to test attenuation (plywood alone is transparent to radio). The arena is generated from the same map the simulator and Gazebo use (Fig. 6)."),
          KeepTogether([Image(os.path.join(DOCS, "proto_arena_plan.png"), width=CW, height=CW * 0.61), Paragraph("Fig. 6. Prototype arena, 7.2 x 4.8 m, from <font name='Mono'>tools/make_proto_arena.py</font>.", CAP), Spacer(1, 4)]),
          tbl([["Week", "Work"],
               ["1 (Oct 6)", "decisions, orders; confirm radio band and rules with the organisers"],
               ["2-3", "Writer chassis, LiDAR, SLAM; thermal and gas sensors"],
               ["3-4", "ESP32 + LoRa beacons and van gateway; 32 B frame on air"],
               ["4-5", "Executor robot; arena built; briefing and navigation"],
               ["6", "integration; five failure cases as physical tests"],
               ["7", "user manual, repository, video"],
               ["8 (by Dec 1)", "pitch rehearsal and submission"]], [CW * 0.2, CW * 0.8], cap="TABLE VI. PHASE 2 TIMELINE"),
          tbl([["Item", "Qty", "Note"],
               ["Jetson Orin Nano 8 GB", "2", "onboard SLAM and Nav2"],
               ["RPLIDAR A3", "2", "2D LiDAR"],
               ["ESP32 + LoRa (433 / 868 MHz)", "6", "beacons; confirm band with the regulator"],
               ["UWB: DWM3001CDK (optional)", "2", "DWM1000 is end of life [4]"],
               ["Thermal camera (Lepton 3.5), MQ-4 gas", "1 set", "MQ-4 needs 24 h preheat [5]"],
               ["Plywood 12 mm, tracked chassis, batteries", "-", "arena 9 sheets; prices to be quoted"]], [CW * 0.50, CW * 0.12, CW * 0.38], cap="TABLE VII. BILL OF MATERIALS (SUMMARY)")]

# ------------------------------------------------------------------ XI. limitations + refs
story += [Paragraph("XI. LIMITATIONS", H1),
          B("All results are from our simulator. The ROS 2 graph was run by the team on Ubuntu 24.04 (reported working up to version v4_8); later versions are checked by 39 unit tests and a fake-ROS integration test. The generated Gazebo world was validated as XML and still needs a visual check; RViz and real DDS timing are not measured."),
          B("Radio loss (12 dB per wall), sensor noise and the anchor uncertainty are assumed values to be measured on hardware. The robot-to-van radio is an ideal channel (protocol TBD). The beacon key is a demo constant."),
          B("End to end, the Writer is the bottleneck: it reports the first reachable person after about six minutes in this layout. Speeding it up (several Writers, a smarter exploration order, or letting an Executor map too) is future work. The simulated Executors move at 1.2-3 m/s; prototype robots will be slower. The prototype has two robots and needs a single universal Executor role that the Command Post does not yet support. In the large building the steam source was never approached in five seeds, so steam rejection is shown by a unit test and by the arena run."),
          Paragraph("REFERENCES", H1),
          Paragraph("[1] RoboCupRescue Robot League, Rules 2026D, rrl.robocup.org.  [2] RoboCupJunior Rescue Maze rules, junior.robocup.org.  [3] NIST, <i>Electromagnetic signal attenuation in construction materials</i>, 1997 (values as tabulated at wifivitae.com).  [4] Qorvo, EVK1000 end-of-life notice PCN 21-0072, qorvo.com.  [5] Hanwei, MQ-4 gas sensor datasheet.  [6] IEEE RAS x AESS, TSYP14 challenge \"The Living Map\", 2026.", ParagraphStyle("ref", parent=BODY, fontSize=7.0, leading=8.3))]

doc.build(story)
from pypdf import PdfReader
n = len(PdfReader(os.path.join(DOCS, "Living_Map_Technical_Report.pdf")).pages); print("pages:", n)
