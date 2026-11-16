import json
P='/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl'
with open(P) as f:
    r=json.loads(f.readline())
ks=sorted(r)
print(len(ks))
print([k for k in ks if not k.startswith(('lv_','hist','st_'))][:400])
for k in ('name','seed','m_road_ttc3','m_road_vs','end_stop','end_stop2','ttc_net','ttc3','m_ttc3_all','m_ttc3_lc','accel_len','accel2_len','r2_merge'):
    print(k, json.dumps(r.get(k))[:500])
