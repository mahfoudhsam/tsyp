"""Regenerates FAILURE_CASES.md and the numbers in README.md / PROTOTYPE_ARENA.md from docs/results.json (+ the navigation benchmark output).
Usage: python3 tools/collect_results.py; python3 tools/bench_nav.py 7 3 11 1 2 5 9 13 > /tmp/bench.out; python3 tools/refresh_docs.py /tmp/bench.out"""
import json, os, re, sys, statistics as st
H = os.path.dirname(os.path.abspath(__file__)); DOCS = os.path.join(H, "..", "docs"); ROOT = os.path.join(H, "..", "..", "..")
R = json.load(open(os.path.join(DOCS, "results.json"))); S = R["baseline_seeds"]; IM, BA, RF = R["uplink_immediate"], R["uplink_batched"], R["rf_stress"]; fb, fw = R["fault_beacon_destroyed"], R["fault_writer_lost"]
mean = lambda k: st.mean(v[k] for v in S.values())
fp, e2e, wfp, wd, end, perr = mean("first_person_s"), mean("first_person_end_to_end_s"), mean("writer_first_reachable_person_s"), mean("writer_done_s"), mean("end_s"), mean("pos_err_m")
bl = S["7"]["blind_first_person_s"]; got = sum(min(v["beacons"], int(v["delivery"].split("/")[0])) for v in S.values()); tot = sum(v["beacons"] for v in S.values())
save = round(100 * (1 - BA["uplink_messages"] / IM["uplink_messages"])); d30 = RF["30 dB/wall"]["delivery"].split("/"); arena = R["proto_arena_seeds"]
a_steam = sum(1 for v in arena.values() if v["steam_rejected"] >= 1); a_deb = sum(1 for v in arena.values() if "DEBRIS" in v["event_types"]); a_end = [v["end_s"] for v in arena.values()]

rows = "\n".join(f"| {k} | {v['repeaters']} of {v['beacons']} | {v['delivery']} | {v['fires_out']} | {v['rescued']} | {v['first_person_s'] if v['first_person_s'] else 'never'} |" for k, v in RF.items())
dl = lambda D, p: f"{D['delay_by_priority'][p]['mean_s']} / {D['delay_by_priority'][p]['max_s']}"
open(os.path.join(DOCS, "FAILURE_CASES.md"), "w").write(f"""# Failure cases: analysis and measured behaviour

All numbers are produced by `python3 tools/collect_results.py` (simulation, seed 7 unless stated; results in `docs/results.json`).
"Delivery a/b" in the table below is *delivered packets / send attempts*; the number of beacons the Command Post actually received is stated in words.

| # | Failure case | Root cause | Mitigation in the system | Measured outcome |
|---|---|---|---|---|
| 1 | Beacon destruction | gas explosion or thermal runaway destroys a dropped beacon | mirror frames (each beacon stores a neighbour's id + seq), heartbeat, `BEACON_LOST` record | mission unchanged: {fb['fires_out']} fires out, {fb['rescued']} rescued; a `BEACON_LOST` record reaches the Command Post |
| 2 | Writer trapped / lost | collapse blocks the Writer's exit, or the Writer fails | the van forwards every record at once, so the Command Post already holds the memory; Executors act on it | Writer killed at 420 s: {fw['fires_out']} fires out, {fw['rescued']} rescued; the unexplored part of the building is missed |
| 3 | Priority inversion / steam false positive | steam looks like fire; a 120 s batch delays an urgent alert | 2-of-3 sensor rule + persistence rejects steam; class P0 and escalated records bypass the queue; critical priority skips the wait | P0 delay {BA['delay_by_priority']['P0']['mean_s']} s even in batched mode; P1 delayed {BA['delay_by_priority']['P1']['mean_s']} s mean (max {BA['delay_by_priority']['P1']['max_s']} s) in batched mode |
| 4 | Impassable debris | rubble blocks a ground robot | `DEBRIS` beacon with `human_intervention_required`; the Executor skips the target | skipped in every run (`BCN_013`), no robot stuck |
| 5 | RF attenuation | dense concrete blocks beacon radio | repeater beacons, ARQ x3, store-and-forward, relays carry ancestors' packets | works up to about 12 dB per wall, degrades at 18 and 24, **fails at 30** (table below) |

## 1. Beacon destruction
* **How it is detected:** every beacon carries a *mirror frame* (id + sequence of a neighbour). When a node stops answering, a **neighbour re-broadcasts the mirrored record as a `BEACON_LOST` packet** (id 1000 + beacon id, class P3; "silence is data"), so the Command Post learns of the loss and keeps the last known data (`Mesh.lost_reported`).
* **Reproduce:** `run_clean.sh speed:=6 fault:=beacon_destroyed` (or `python3 -m living_map_core.standalone --fault beacon_destroyed`).
* **Result:** the mission outcome equals the baseline ({fb['fires_out']} fires, {fb['rescued']} people).
* **Residual risk:** if a beacon and its neighbour are destroyed together, the mirror copy is lost too.

## 2. Writer trapped / lost
* **Why it works:** in `immediate` uplink mode the Command Post receives each record when the van does. The Writer is not needed after it has reported.
* **Reproduce:** `run_clean.sh speed:=6 fault:=writer_lost` (Writer stops at 420 s).
* **Result:** {fw['fires_out']} fires out and {fw['rescued']} people rescued instead of 4/4 and 4/5, because the part of the building the Writer had not reached is unknown. This is the honest cost of losing the Writer.
* **Residual risk:** no second Writer is deployed. A Phase 2 option is a second explorer or an Executor that also maps.

## 3. Priority inversion and steam
* **Steam:** `Detector` needs two of three votes (air above 70 C, thermal above 150 C, gas above 50 ppm) for three consecutive readings. A steam pipe only raises the air temperature, so it counts as `steam_rejected`. Covered by `test_detector_rejects_steam`; in the 5 baseline seeds the Writer never came close to the steam source, so the rejection is **not** exercised on the large map. On the prototype arena (a wider kettle-like plume at the corridor start) it is rejected on {a_steam} of 5 seeds.
* **Batching delay** ({BA['uplink_messages']} uplink messages instead of {IM['uplink_messages']}, -{save} %), delay at the Command Post by class:

| class | immediate: mean / max (s) | batched: mean / max (s) |
|---|---|---|
""" + "\n".join(f"| {p} | {dl(IM, p)} | {dl(BA, p)} |" for p in ("P0", "P1", "P2", "P3")) + f"""

* Class P0 is never held. P1 to P3 wait up to {BA['delay_by_priority']['P3']['max_s']} s. The mission ended {BA['end_s']-IM['end_s']} s later in batched mode. **Immediate mode is the default; batching is the bandwidth-saving option required by the challenge text.**
* **Preemption:** an event whose effective priority number falls below 0.3 skips the collection wait. This path is covered by unit tests (`test_critical_event_preempts_the_collection_window...`); it does not trigger in the baseline scenario.
* **Reproduce:** `run_clean.sh speed:=6 uplink:=batched`.

## 4. Impassable debris
* The Writer marks a route-blocking rubble pile as `DEBRIS` with `human_intervention_required`. The Command Post lists the victim behind it as `HEAVY_RESCUE` and does not dispatch a robot (`skipped: BCN_013`).
* Result: in all runs the fifth person is left for the human heavy-rescue team and no robot is stuck.

## 5. RF attenuation (the case where the design fails)
Radio model: RSSI = -40 - 28 log10(d) - (loss per wall) x walls - 4 dB per rubble - 18 dB per floor. The baseline uses 12 dB per wall. Stress test (the loss per wall is changed, everything else equal):

| loss per wall | repeaters / beacons | delivery (delivered / attempts) | fires out | rescued | Executor time to a person |
|---|---|---|---|---|---|
{rows}

* **Why it fails:** the Writer drops more repeaters as the link weakens and spends its budget of 44 beacons on them, so it stops before it has explored the building (events are missed). At 30 dB per wall nothing is delivered ({d30[0]} of {int(d30[1]):,} attempts).
* **Is 30 dB realistic?** NIST 1997 data at 2.4 GHz (as tabulated by Wi-Fi Vitae): plywood about 1 dB, brick about 6, concrete 102 mm about 15, concrete 203 mm about 29, reinforced concrete 203 mm about 31. So 12 dB is realistic for light masonry and **optimistic for heavy concrete**.
* **Phase 2 mitigation (not implemented yet):** a sub-GHz LoRa link (433 / 868 MHz), more relay nodes, and a beacon budget that reserves capacity for events instead of repeaters only. The prototype arena includes one foil-lined wall to measure this on hardware.
* **Reproduce:** add `"wall_db": 24` to a map JSON, or run `tools/collect_results.py` (RF section).

## What these tests do *not* show
* All runs are simulation. The radio parameters are assumed values, not measurements.
* Failure cases 1 and 2 are single-seed fault injections; case 3's steam rejection and the preemption are shown by unit tests and the arena run.
""")

# ---- README front: results block
rd = open(os.path.join(ROOT, "README.md")).read()
block = f"""## Results (simulation, 5 seeds, `python3 tools/collect_results.py`)
| measure | value |
|---|---|
| Executor time to a person, from leaving the van | **{fp:.0f} s** vs **{bl:.0f} s** for the same robot searching blind |
| end to end (Writer drives to the door by GPS, explores, briefing, Executor), first person reached | **{e2e:.0f} s** (the Writer finds the first reachable person after {wfp:.0f} s and finishes exploring after {wd:.0f} s) |
| whole mission | about {end:.0f} s: 4/4 fires out, 4/5 people rescued (the 5th is sealed behind rubble and flagged for human rescue) |
| beacons delivered | {got}/{tot} ({100*got/tot:.0f} %) |
| position error | {perr:.2f} m mean |
| uplink | immediate: {IM['uplink_messages']} messages; batched: {BA['uplink_messages']} (-{save} %), class P1 delayed {BA['delay_by_priority']['P1']['mean_s']:.0f} s on average |
| radio attenuation stress | fires out 4/4 at 12 dB per wall, 3/4 at 18, 1/4 at 24, 0/4 at 30: **the design fails under very strong attenuation** |
| prototype arena (7.2 x 4.8 m, 5 seeds) | fire out, 3/4 rescued, all beacons delivered; steam rejected on {a_steam}/5, debris beacon on {a_deb}/5 seeds |

Read the two first rows together: the chain does not make the *first* arrival earlier end to end (the Writer must explore first); it removes blind searching inside the hazard, lets one Writer pass serve every Executor, and handles the whole building.

"""
a = rd.index("## Results (simulation, 5 seeds"); b = rd.index("## Where to read more"); rd = rd[:a] + block + rd[b:]
bench = sys.argv[1] if len(sys.argv) > 1 else None
if bench and os.path.exists(bench):
    rows_b = [l.split() for l in open(bench) if re.match(r"\s+\d+\s+(trail|direct)\s+\|", l)]
    def col(nav, i): return [float(r[i]) for r in rows_b if r[1] == nav]
    # columns: seed nav | first fires rescued dist busy missions failed end
    T = {n: dict(first=col(n, 3), dist=col(n, 6), busy=col(n, 7), end=col(n, 10)) for n in ("trail", "direct")}
    if all(T[n]["first"] for n in T):
        f = lambda n, k, fn=st.mean: fn(T[n][k]); d = round(100 * (1 - f("direct", "dist") / f("trail", "dist"))); bsy = round(100 * (1 - f("direct", "busy") / f("trail", "busy")))
        worse = [(round(100 * (dd / td - 1), 1)) for dd, td in zip(T["direct"]["dist"], T["trail"]["dist"]) if dd > td]
        tbl = (f"| Executor time to the first person (from leaving the van) | {f('trail','first'):.1f} s (median {f('trail','first',st.median):.0f} s) | {f('direct','first'):.1f} s (median {f('direct','first',st.median):.0f} s) |\n"
               f"| total robot distance | {f('trail','dist'):.0f} m | {f('direct','dist'):.0f} m (-{d} %) |\n| total robot busy time | {f('trail','busy'):.0f} s | {f('direct','busy'):.0f} s (-{bsy} %) |\n| mission end | {f('trail','end'):.0f} s | {f('direct','end'):.0f} s |")
        json.dump(dict(trail_first=f("trail", "first"), direct_first=f("direct", "first"), trail_first_med=f("trail", "first", st.median), direct_first_med=f("direct", "first", st.median), trail_dist=f("trail", "dist"), direct_dist=f("direct", "dist"), dist_pct=d,
                       trail_busy=f("trail", "busy"), direct_busy=f("direct", "busy"), busy_pct=bsy, trail_end=f("trail", "end"), direct_end=f("direct", "end"), worse=worse, n=len(T["trail"]["first"])), open(os.path.join(DOCS, "nav_results.json"), "w"), indent=1)
        a = rd.index("| Executor time to the first person (from leaving the van) |"); b = rd.index("Honest notes: in 2 of 8 seeds"); rd = rd[:a] + tbl + "\n\n" + rd[b:]
        rd = re.sub(r"Honest notes: in 2 of 8 seeds the new method drove slightly MORE distance \([^)]*\)", f"Honest notes: in {len(worse)} of {len(T['trail']['first'])} seeds the new method drove slightly MORE distance ({', '.join('+'+str(w)+' %' for w in worse) or 'none'})", rd, count=1)
open(os.path.join(ROOT, "README.md"), "w").write(rd)

# ---- PROTOTYPE_ARENA.md: the 5-seed table and the steam / GPS notes
pa = open(os.path.join(DOCS, "PROTOTYPE_ARENA.md")).read()
trows = "\n".join(f"| {k} | {v['fires_out']} | {v['rescued']} | {v['delivery']} | {v['steam_rejected']} | {', '.join(t for t in v['event_types'] if t in ('DEBRIS',)) or '-'} | {v['end_s']} |" for k, v in arena.items())
a = pa.index("| seed | fire out |"); b = pa.index("Problems the arena exposed")
pa = pa[:a] + "| seed | fire out | people rescued | beacons delivered | steam rejected | debris beacon | done at (sim s) |\n|---|---|---|---|---|---|---|\n" + trows + f"\n\nThe 4th person is behind the rubble (heavy rescue by design). The steam false alarm (a kettle-like plume at the corridor start) is rejected on {a_steam} of 5 seeds; the debris beacon appears on {a_deb} of 5 seeds, depending on the Writer's route. In every run the Writer starts at the van, drives to the door by GPS (about 3 s) and explores without GPS.\n\n" + pa[b:]
pa = pa.replace("Steam: a mug of hot water.", "Steam: a kettle or humidifier (a mug warms the air too little for the rule to see it).")
open(os.path.join(DOCS, "PROTOTYPE_ARENA.md"), "w").write(pa); print("docs refreshed")
