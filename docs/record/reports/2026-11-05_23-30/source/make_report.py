"""Builds the sweep report from sweep1.json. usage: make_report.py sweep1.json out.html"""
import json
import sys

r = json.load(open(sys.argv[1]))
w = lambda x, unit="delay": f"{abs(x):.0f} % {'less' if x >= 0 else 'more'}"
rows = []
for q, x in r["levels"].items():
    a = x["arms"]
    pol_d = sorted(a[f"d{i}"]["delay_vs_nc"][0] for i in range(5))[2]
    pol_t = sorted(a[f"d{i}"]["ttc"] for i in range(5))[2]
    rows.append(f"<tr><td>{float(q):,.0f}</td><td>{a['nc']['delay']:,.0f}</td><td>{max(v['served'] for v in a.values()):.2f}</td><td>{w(a['p333']['delay_vs_nc'][0])}</td><td>{w(a['os1_15_10']['delay_vs_nc'][0])}</td>"
                f"<td>{w(pol_d)}</td><td>{a['nc']['ttc']:,.0f}</td><td>{a['p333']['ttc']:,.0f}</td><td>{a['os1_15_10']['ttc']:,.0f}</td><td>{pol_t:,.0f}</td><td>{'yes' if x['clean'] else 'no'}</td></tr>")
html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Demand Sweep Range</title>
<style>:root{{--bg:#FFF8E7;--ink:#30302C;--line:#D6D0C2;--panel:#F7F0DF;--dim:#66645D}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#1B1A17;--ink:#EDE8DA;--line:#45413A;--panel:#25231F;--dim:#A8A394}}}}
:root[data-theme="dark"]{{--bg:#1B1A17;--ink:#EDE8DA;--line:#45413A;--panel:#25231F;--dim:#A8A394}}body{{margin:0;padding:16px;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}main{{max-width:1050px}}
.wrap{{overflow-x:auto}}table{{border-collapse:collapse;font-size:13.5px}}th,td{{border:1px solid var(--line);padding:3px 7px;text-align:right}}th{{background:var(--panel)}}p,li{{max-width:80ch}}.dim{{color:var(--dim);font-size:13px}}</style></head><body><main>
<h1>Demand sweep: the training range for round 1</h1>
<p class="dim">2026-11-05, V416-V419. Plant r2m3 (plant_c3), training slowdowns, constant demand 2,500-7,500 veh/h, 10 seeds (7,440,600-609), 1,680 runs, 0 failed. Medians of 10 paired seeds; "less" and "fewer" mean better than no control. Code {r.get('code', '6d3a1a6')}.</p>
<h2>What it shows</h2>
<ul>
<li><b>Pre-registered readings (V416 range rule and V418 impact band):</b> both give <b>2,500-6,250 veh/h, with no edges</b>.
  <ul>
    <li>The lower end is the bottom of the grid: every controller has at least 10 % less delay than no control even at 2,500, so the sweep never found where impact stops.</li>
    <li>The upper end is set by served demand: the best arm serves 91 % at 6,250 and 88 % at 6,500. No arm had a teleport or a collision above the limit.</li>
  </ul></li>
<li><b>Delay does not mark a band.</b> Gaps of 0.8 s cut delay against no control's 1.6 s at every level, by 11-40 %. That holds for both rules and all the policies, so it is a property of the headway, not of DRL.</li>
<li><b>Close-following marks a band.</b>
  <ul>
    <li>The policies (median of 5) have fewer close-following seconds than no control only at 5,000-5,500.</li>
    <li>p333 and os1_15_10 have fewer only at 5,000 (os1_15_10 also at 5,250).</li>
    <li>Below 5,000, no control's counts are tiny (0-59 seconds per run) and every controller has more.</li>
    <li>From 5,750 up, the policies are about level with no control, while the rules have more.</li>
  </ul></li>
<li><b>Post-hoc reading, not pre-registered:</b> a close-following band of about 5,000-5,500, with edges at 4,500-4,750 and 5,750-6,000, so a training range of about 4,500-6,000. This matches the earlier exploratory band (V409).</li>
</ul>
<h2>Per level</h2>
<div class="wrap"><table><tr><th>Demand</th><th>No control delay, veh-s</th><th>Best served share</th><th>p333 delay</th><th>os1_15_10 delay</th><th>Policies delay</th><th>Close-following s: no control</th><th>p333</th><th>os1_15_10</th><th>policies</th><th>Clean</th></tr>
{''.join(rows)}</table></div>
<p class="dim">Delay columns give each controller against no control. Close-following columns give seconds per run, read once a second, so that tiny counts are not inflated into large percentages. Policies are baseline-v3 d0-d4, trained at 4,090, 4,600 and 5,300 only.</p>
</main></body></html>"""
open(sys.argv[2], "w").write(html)
