# Demo video script (target 3:00; the sprint plan asks for 2 to 3 minutes)

You record; this file tells you what to show, what to say and when. Everything below is something the simulation really shows.

## Before you record (10 minutes)
1. **Close** every other window and silence notifications. Screen 1920x1080 if possible.
2. **Install and build** the latest version (see `START_HERE.md`) and check once: `bash scripts/run_clean.sh speed:=4` then Ctrl+C.
3. Open three browser tabs (do not load them yet): `http://localhost:8081` (simulation), `http://localhost:8080` (Command Post), `http://localhost:8081/flow` (data flow + beacon table). Zoom 110 %.
4. Put these images ready in a viewer (open the file, press F11 for full screen): `docs/diagrams/architecture.png`, page 4 of `docs/Living_Map_Technical_Report.pdf` (failure table) and `docs/diagrams/fig_results.png`, `docs/proto_arena_plan.png`.
5. **Screen recorder.** Press **PrtSc**, choose the video (screen recording) icon, select the full screen, start. If a recording stops after 30 s, remove the limit once: `gsettings set org.gnome.settings-daemon.plugins.media-keys max-screencast-length 0` and use **Ctrl+Alt+Shift+R** to start and stop (red dot). Files land in `~/Videos`.
6. Record the narration **live** while the run plays (read the lines below), or record the screen first and the voice afterwards. English, calm, about 140 words per minute.
7. Launch command for the take (speed 4 makes the run last about 2.4 minutes of real time):
```bash
bash ~/living_map_ws/src/living_map_core/scripts/run_clean.sh speed:=4 2>&1 | tee ~/launch.log
```

## What the run does (simulated seconds; divide by 4 for real seconds at speed:=4)
| sim time | event | real time |
|---|---|---|
| 0 s | the Writer leaves the van and drives to the door **by GPS** (about 3 s), then explores with no GPS | 0 s |
| 30 s | a **forged packet is rejected** (CRC/MAC) | 7 s |
| 46 s | gas leak found (P0) -> **first order**, fire truck at 48 s | 12 s |
| 89 s / 90 s | an animal is found -> ambulance order | 22 s |
| 116 s | a person is found behind rubble: flagged **heavy rescue** (the robots skip it) | 29 s |
| 192 s | second floor reached (stairs); animal on floor 1 | 48 s |
| 276-368 s | fires on floor 1 -> **drone** orders; first reachable person at 360 s -> ambulance + drone | 69-92 s |
| about 530 s | the Writer finishes exploring | 133 s |
| about 570 s | all four fires out, 4 of 5 people rescued: results card appears | 143 s |

Exact times shift by a few seconds between runs; follow the screen, not the clock.

## Shot list
| Video time | On screen | Say (narration) | Caption |
|---|---|---|---|
| 0:00-0:12 | title slide (page 1 of the report) | "When a robot fails inside a burning building, everything it learned is lost. The Living Map gives the building its own memory." | The Living Map: Fire / Hazardous Building |
| 0:12-0:35 | `architecture.png` full screen | "A Writer robot explores the GPS-denied building and leaves small radio beacons. A van, the Outside Network Area, is the only link to the outside. The Command Post ranks the events and briefs the Executors. Robots never talk to each other, and never directly to the Command Post." | Air-gap: one crossing |
| 0:35-0:45 | terminal, run the command above, then the simulation page | "We start the whole system with one command." | single-command launch |
| 0:45-1:00 | **simulation page**: Writer moving, beacons appearing | "The Writer maps the building with LiDAR and senses temperature, thermal image and gas. A fire needs two of three sensors to agree, so a steam pipe is rejected." | Writer autonomy, 2-of-3 rule |
| 1:00-1:15 | **flow page**: beacon table, GPS columns, the "forged packet REJECTED" line | "Each beacon is 32 bytes. The van checks the CRC and the authentication tag, so a forged packet is rejected, rebuilds the position from egocentric hops, and converts it to GPS from the entrance anchor." | 32 B beacon, CRC16 + MAC, frame translation |
| 1:15-1:35 | **Command Post page**: live map, ranked orders, the incidents card | "At the Command Post, every event has a priority number: zero is the most urgent, and the number falls while an event waits. Once per second the Command Post groups related events, here a gas leak, into one order, so we do not send one order per detection." | Priority 0 to infinity, 1 s decision cycle |
| 1:35-1:55 | **simulation page**: Executors leaving, reaching targets, "order updated" lines | "The Executors are briefed at the van and plan straight to their targets. When a hazard is cleared, the Command Post tells the ambulance through the van." | Executor navigation, ORDER_UPDATE |
| 1:55-2:20 | wait for the **results card** (or stop at about 570 s); show it | "Once briefed, the Executor reaches a person in 39 seconds instead of 270 seconds when it searches blind. The whole building is handled: four of four fires out and four of five people rescued; the fifth is behind rubble and handed to the human team. The price is the Writer's exploration time: end to end, the first person is reached after about 400 seconds in this layout." | Executor search time: 39 s vs 270 s (blind); end to end about 409 s |
| 2:20-2:45 | `fig_results.png` and the failure table | "We tested five failure cases. A destroyed beacon is recovered from its neighbour. If the Writer is lost, the Command Post keeps the memory. Urgent alerts bypass the queue. Rubble is flagged for human rescue. And we show where we fail: very strong radio attenuation breaks the beacon chain, which is why Phase 2 uses a sub-gigahertz radio." | 5 failure cases, one honest limit |
| 2:45-3:00 | `proto_arena_plan.png` | "Next is a real prototype: a seven by five metre plywood arena generated from the same map, with two robots, a van and a laptop as Command Post." | Phase 2: physical prototype |

## If something goes wrong
* A web page is empty: reload it; check `bash scripts/check_run.sh`.
* **Do not claim Gazebo** in the video unless the Gazebo window really shows the building during your take. If it does not, record only the web pages; the report already says the Gazebo world needs a visual check.
* Run too slow or too fast: change `speed:=4`.

## After recording
Trim to 3:00 or less; check that the voice is clear; save as `LivingMap_demo.mp4` (or `.webm`). If `ffmpeg` is installed: `ffmpeg -i in.webm -ss 00:00:03 -to 00:03:00 -c copy out.webm`. Upload where the organisers ask (unknown: see `SUBMISSION_CHECKLIST.md`).
