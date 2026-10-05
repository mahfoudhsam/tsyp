"""Data figures from docs/results.json -> docs/diagrams/fig_priority.png, fig_results.png"""
import json, os, math, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Serif", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "legend.fontsize": 6.5, "axes.spines.top": False, "axes.spines.right": False})
here = os.path.dirname(__file__); OUT = os.path.join(here, "..", "docs", "diagrams"); R = json.load(open(os.path.join(here, "..", "docs", "results.json")))
import sys; sys.path.insert(0, os.path.join(here, ".."))
from living_map_core.beacon_protocol import priority, confidence

# ---- Fig: the two clocks
fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.15))
t = [i * 5 for i in range(0, 181)]
for name, typ, cls, n, col in (("person in danger (P0)", "HUMAN", 0, 1, "#c62828"), ("fire (P1)", "FIRE", 1, 1, "#ef6c00"), ("gas (P1)", "GAS", 1, 1, "#6a1b9a"), ("animal (P2)", "ANIMAL", 2, 1, "#1565c0")):
    ax[0].plot(t, [priority(typ, cls, n, x) for x in t], label=name, color=col, lw=1.4)
ax[0].axhline(0.3, color="k", ls="--", lw=0.8); ax[0].text(12, 0.085, "dashed line: critical threshold 0.3 (skips the wait)", fontsize=6.3)
ax[0].set_yscale("log"); ax[0].set_ylim(0.05, 40); ax[0].set_xlabel("time since detection (s)"); ax[0].set_ylabel("priority number pi  (0 = most urgent)")
ax[0].set_title("(a) pi(t) = pi0 e^(-0.004 t): never negative, never reset", loc="left"); ax[0].legend(frameon=False, loc="upper right")
tm = [i * 0.5 for i in range(0, 61)]
for typ, col in (("FIRE", "#ef6c00"), ("GAS", "#6a1b9a"), ("HUMAN", "#c62828")): ax[1].plot(tm, [confidence(typ, x * 60) for x in tm], color=col, lw=1.4, label={"FIRE": "fire / gas (0.10 per min)", "GAS": None, "HUMAN": "person / animal (0.01 per min)"}[typ])
ax[1].set_xlabel("age of the observation (min)"); ax[1].set_ylabel("confidence in the stored data"); ax[1].set_ylim(0, 1.05)
ax[1].set_title("(b) the other clock: observations get stale", loc="left"); ax[1].legend(frameon=False, loc="lower left")
fig.tight_layout(pad=0.6); fig.savefig(os.path.join(OUT, "fig_priority.png"), dpi=300); plt.close(fig)

# ---- Fig: results
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.2))
seeds = R["baseline_seeds"]; fp = st.mean(v["first_person_s"] for v in seeds.values()); bl = st.mean(v["blind_first_person_s"] for v in seeds.values())
e2e = st.mean(v["first_person_end_to_end_s"] for v in seeds.values())
vals = [bl, fp, e2e]; b = ax[0].bar(["blind\nrobot", "Executor\nbriefed", "end to\nend"], vals, color=["#b0bec5", "#2e7d32", "#ef6c00"], width=0.6)
for r, v in zip(b, vals): ax[0].text(r.get_x() + r.get_width() / 2, v + 6, f"{v:.0f} s", ha="center", fontsize=7)
ax[0].set_ylabel("time to reach the first person (s)"); ax[0].set_title("(a) 5 seeds, mean", loc="left"); ax[0].set_ylim(0, 470); ax[0].tick_params(axis="x", labelsize=6.3)
im, ba = R["uplink_immediate"]["delay_by_priority"], R["uplink_batched"]["delay_by_priority"]; ps = ["P0", "P1", "P2", "P3"]; x = range(4)
ax[1].bar([i - 0.2 for i in x], [im[p]["mean_s"] for p in ps], 0.4, label=f'immediate ({R["uplink_immediate"]["uplink_messages"]} messages)', color="#1565c0")
ax[1].bar([i + 0.2 for i in x], [ba[p]["mean_s"] for p in ps], 0.4, label=f'batched ({R["uplink_batched"]["uplink_messages"]} messages)', color="#ef6c00")
ax[1].set_xticks(list(x)); ax[1].set_xticklabels(ps); ax[1].set_ylabel("mean delay at the Command Post (s)"); ax[1].set_title("(b) uplink: delay by priority class", loc="left"); ax[1].legend(frameon=False, loc="upper left")
rf = R["rf_stress"]; lab = list(rf.keys()); dbs = [int(k.split()[0]) for k in lab]
found = [int(rf[k]["fires_out"].split("/")[0]) for k in lab]; rep = [rf[k]["repeaters"] for k in lab]
ax[2].plot(dbs, found, "o-", color="#c62828", label="fires put out (of 4)"); ax[2].set_ylim(-0.2, 4.5); ax[2].set_xlabel("radio loss per wall (dB)"); ax[2].set_ylabel("fires put out (of 4)")
a2 = ax[2].twinx(); a2.plot(dbs, rep, "s--", color="#455a64", label="repeater beacons used"); a2.set_ylabel("repeater beacons used"); a2.spines["right"].set_visible(True); a2.set_ylim(0, 40)
ax[2].axvspan(10, 15, color="#e8f5e9"); ax[2].text(10.3, 4.15, "light masonry", fontsize=5.8); ax[2].axvspan(27, 32, color="#ffebee"); ax[2].text(27.2, 4.15, "thick concrete", fontsize=5.8)
ax[2].set_title("(c) RF attenuation stress", loc="left"); fig.tight_layout(pad=0.6); fig.savefig(os.path.join(OUT, "fig_results.png"), dpi=300); plt.close(fig)
print("figures written")
