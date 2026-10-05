"""Reproducible measurements for the technical report. Writes docs/results.json.
Usage: python3 tools/collect_results.py      (about 4 minutes of CPU)"""
import sys, os, json, time, statistics as st
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from living_map_core.simulation import Simulation, run

def summ(s):
    m = s.view.metrics
    if m is None:                                   # the mission never produced a final summary (e.g. radio loss so strong that no Executor was ever sent)
        fo = sum(1 for f in s.w.fires if f["I"] < 0.1); resc = sum(1 for h in s.w.humans if h["rescued"]) + sum(1 for a in s.w.animals if a["rescued"])
        return dict(first_person_s=None, first_person_end_to_end_s=None, blind_first_person_s=None, gain_pct=None, fires_out=f"{fo}/{len(s.w.fires)}", rescued=f"{resc}/{len(s.w.humans) + len(s.w.animals)}",
                    beacons=len(s.wr.beacons), repeaters=s.wr.repeaters, delivery=f"{s.mesh.delivered}/{s.mesh.sent}", rejected_packets=s.gw.rejected, pos_err_m=None, pos_err_max_m=None, skipped=[],
                    steam_rejected=s.wr.det.steam_rejected, end_s=round(s.t), final=s.final)
    return dict(first_person_s=m["with_beacons_s"], first_person_end_to_end_s=m.get("first_person_abs_s"), blind_first_person_s=m["blind_s"], gain_pct=m["gain_pct"], fires_out=f'{m["fires_out"]}/{m["fires"]}', rescued=f'{m["rescued"]}/{m["people"]}',
                beacons=m["beacons"], repeaters=m["repeaters"], delivery=m["delivery"], rejected_packets=m["rejected"], pos_err_m=m["position_error_m"], pos_err_max_m=m["position_error_max_m"],
                skipped=list(m.get("skipped", [])), steam_rejected=s.wr.det.steam_rejected, end_s=round(s.t), final=s.final, orders=len(s.cp.orders), order_updates=sum(1 for e in s.cp.flow if "ORDER_UPDATE" in e["label"]), preempts=sum(1 for e in s.cp.flow if "PREEMPT" in e["label"]))

def run_spy(seed):
    """baseline run that also records when the Writer reported the first REACHABLE person and when it finished exploring"""
    s = Simulation("none", True, None, seed=seed); person = done = None
    while s.t < 1400 and not s.final:
        s.step(0.5)
        if person is None and any(r["type"] == "HUMAN" and not r["human_needed"] for r in s.cp.records.values()): person = s.t
        if done is None and s.wr.done: done = s.t
    out = summ(s); out["writer_first_reachable_person_s"] = person; out["writer_done_s"] = done; return out

def delay_run(uplink, seed=7):
    s = Simulation("none", True, None, seed=seed, uplink=uplink); calls = []; orig = s.cp.ingest
    def spy(msg, now):
        if msg.get("records"): calls.append((now, msg.get("reason"), [(r["prio"], r["type"], r["t0"]) for r in msg["records"]]))
        return orig(msg, now)
    s.cp.ingest = spy
    while s.t < 1400 and not s.final: s.step(0.5)
    by = {}
    for now, why, recs in calls:
        for prio, typ, t0 in recs: by.setdefault(prio, []).append(max(0.0, now - t0))
    out = dict(uplink_messages=len(calls), reasons={}, delay_by_priority={})
    for now, why, recs in calls: out["reasons"][why] = out["reasons"].get(why, 0) + 1
    for p, v in sorted(by.items()): out["delay_by_priority"][f"P{p}"] = dict(n=len(v), mean_s=round(st.mean(v), 1), max_s=round(max(v), 1))
    out.update(summ(s)); return out

if __name__ == "__main__":
    R = {}; t00 = time.time()
    R["baseline_seeds"] = {str(sd): run_spy(sd) for sd in (7, 3, 11, 1, 2)}; print("baseline done", round(time.time() - t00), "s", flush=True)
    R["fault_beacon_destroyed"] = summ(run(fault="beacon_destroyed", seed=7)); R["fault_writer_lost"] = summ(run(fault="writer_lost", seed=7)); print("faults done", flush=True)
    R["uplink_immediate"] = delay_run("immediate"); R["uplink_batched"] = delay_run("batched"); print("uplink done", flush=True)
    PROTO = os.path.join(os.path.dirname(__file__), "..", "maps", "proto_arena.json"); R["proto_arena_seeds"] = {}
    for sd in (7, 3, 11, 1, 2):
        s = run(map_path=PROTO, max_t=600.0, seed=sd); o = summ(s); o["event_types"] = sorted({r["type"] for r in s.cp.records.values()} - {"REPEATER"}); R["proto_arena_seeds"][str(sd)] = o
    print("arena done", flush=True)
    R["rf_stress"] = {}
    for db in (12, 18, 24, 30):
        s = Simulation("none", True, None, seed=7); s.w.wall_db = float(db)
        while s.t < 1400 and not s.final: s.step(0.5)
        R["rf_stress"][f"{db} dB/wall"] = summ(s); print("rf", db, "done", flush=True)
    os.makedirs("docs", exist_ok=True); json.dump(R, open("docs/results.json", "w"), indent=1); print("wrote docs/results.json in", round(time.time() - t00), "s")
