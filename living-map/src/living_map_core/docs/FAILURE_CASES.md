# Failure cases: analysis and measured behaviour

All numbers are produced by `python3 tools/collect_results.py` (simulation, seed 7 unless stated; results in `docs/results.json`).
"Delivery a/b" in the table below is *delivered packets / send attempts*; the number of beacons the Command Post actually received is stated in words.

| # | Failure case | Root cause | Mitigation in the system | Measured outcome |
|---|---|---|---|---|
| 1 | Beacon destruction | gas explosion or thermal runaway destroys a dropped beacon | mirror frames (each beacon stores a neighbour's id + seq), heartbeat, `BEACON_LOST` record | mission unchanged: 4/4 fires out, 4/5 rescued; a `BEACON_LOST` record reaches the Command Post |
| 2 | Writer trapped / lost | collapse blocks the Writer's exit, or the Writer fails | the van forwards every record at once, so the Command Post already holds the memory; Executors act on it | Writer killed at 420 s: 2/4 fires out, 3/5 rescued; the unexplored part of the building is missed |
| 3 | Priority inversion / steam false positive | steam looks like fire; a 120 s batch delays an urgent alert | 2-of-3 sensor rule + persistence rejects steam; class P0 and escalated records bypass the queue; critical priority skips the wait | P0 delay 0.3 s even in batched mode; P1 delayed 27.2 s mean (max 96.5 s) in batched mode |
| 4 | Impassable debris | rubble blocks a ground robot | `DEBRIS` beacon with `human_intervention_required`; the Executor skips the target | skipped in every run (`BCN_013`), no robot stuck |
| 5 | RF attenuation | dense concrete blocks beacon radio | repeater beacons, ARQ x3, store-and-forward, relays carry ancestors' packets | works up to about 12 dB per wall, degrades at 18 and 24, **fails at 30** (table below) |

## 1. Beacon destruction
* **How it is detected:** every beacon carries a *mirror frame* (id + sequence of a neighbour). When a node stops answering, a **neighbour re-broadcasts the mirrored record as a `BEACON_LOST` packet** (id 1000 + beacon id, class P3; "silence is data"), so the Command Post learns of the loss and keeps the last known data (`Mesh.lost_reported`).
* **Reproduce:** `run_clean.sh speed:=6 fault:=beacon_destroyed` (or `python3 -m living_map_core.standalone --fault beacon_destroyed`).
* **Result:** the mission outcome equals the baseline (4/4 fires, 4/5 people).
* **Residual risk:** if a beacon and its neighbour are destroyed together, the mirror copy is lost too.

## 2. Writer trapped / lost
* **Why it works:** in `immediate` uplink mode the Command Post receives each record when the van does. The Writer is not needed after it has reported.
* **Reproduce:** `run_clean.sh speed:=6 fault:=writer_lost` (Writer stops at 420 s).
* **Result:** 2/4 fires out and 3/5 people rescued instead of 4/4 and 4/5, because the part of the building the Writer had not reached is unknown. This is the honest cost of losing the Writer.
* **Residual risk:** no second Writer is deployed. A Phase 2 option is a second explorer or an Executor that also maps.

## 3. Priority inversion and steam
* **Steam:** `Detector` needs two of three votes (air above 70 C, thermal above 150 C, gas above 50 ppm) for three consecutive readings. A steam pipe only raises the air temperature, so it counts as `steam_rejected`. Covered by `test_detector_rejects_steam`; in the 5 baseline seeds the Writer never came close to the steam source, so the rejection is **not** exercised on the large map. On the prototype arena (a wider kettle-like plume at the corridor start) it is rejected on 5 of 5 seeds.
* **Batching delay** (11 uplink messages instead of 40, -72 %), delay at the Command Post by class:

| class | immediate: mean / max (s) | batched: mean / max (s) |
|---|---|---|
| P0 | 0.3 / 0.5 | 0.3 / 0.5 |
| P1 | 0.2 / 0.5 | 27.2 / 96.5 |
| P2 | 0.2 / 0.5 | 48.5 / 75.0 |
| P3 | 0.1 / 0.5 | 38.3 / 109.5 |

* Class P0 is never held. P1 to P3 wait up to 109.5 s. The mission ended 28 s later in batched mode. **Immediate mode is the default; batching is the bandwidth-saving option required by the challenge text.**
* **Preemption:** an event whose effective priority number falls below 0.3 skips the collection wait. This path is covered by unit tests (`test_critical_event_preempts_the_collection_window...`); it does not trigger in the baseline scenario.
* **Reproduce:** `run_clean.sh speed:=6 uplink:=batched`.

## 4. Impassable debris
* The Writer marks a route-blocking rubble pile as `DEBRIS` with `human_intervention_required`. The Command Post lists the victim behind it as `HEAVY_RESCUE` and does not dispatch a robot (`skipped: BCN_013`).
* Result: in all runs the fifth person is left for the human heavy-rescue team and no robot is stuck.

## 5. RF attenuation (the case where the design fails)
Radio model: RSSI = -40 - 28 log10(d) - (loss per wall) x walls - 4 dB per rubble - 18 dB per floor. The baseline uses 12 dB per wall. Stress test (the loss per wall is changed, everything else equal):

| loss per wall | repeaters / beacons | delivery (delivered / attempts) | fires out | rescued | Executor time to a person |
|---|---|---|---|---|---|
| 12 dB/wall | 25 of 40 | 40/40 | 4/4 | 4/5 | 39.5 |
| 18 dB/wall | 31 of 45 | 45/45 | 3/4 | 4/5 | 39.5 |
| 24 dB/wall | 34 of 46 | 46/70 | 1/4 | 4/5 | 39.0 |
| 30 dB/wall | 34 of 46 | 0/11361 | 0/4 | 0/5 | never |

* **Why it fails:** the Writer drops more repeaters as the link weakens and spends its budget of 44 beacons on them, so it stops before it has explored the building (events are missed). At 30 dB per wall nothing is delivered (0 of 11,361 attempts).
* **Is 30 dB realistic?** NIST 1997 data at 2.4 GHz (as tabulated by Wi-Fi Vitae): plywood about 1 dB, brick about 6, concrete 102 mm about 15, concrete 203 mm about 29, reinforced concrete 203 mm about 31. So 12 dB is realistic for light masonry and **optimistic for heavy concrete**.
* **Phase 2 mitigation (not implemented yet):** a sub-GHz LoRa link (433 / 868 MHz), more relay nodes, and a beacon budget that reserves capacity for events instead of repeaters only. The prototype arena includes one foil-lined wall to measure this on hardware.
* **Reproduce:** add `"wall_db": 24` to a map JSON, or run `tools/collect_results.py` (RF section).

## What these tests do *not* show
* All runs are simulation. The radio parameters are assumed values, not measurements.
* Failure cases 1 and 2 are single-seed fault injections; case 3's steam rejection and the preemption are shown by unit tests and the arena run.
