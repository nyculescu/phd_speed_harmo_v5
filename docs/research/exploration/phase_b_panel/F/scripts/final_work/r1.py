"""Named fields from the recorded v2.3 reading (no dump)."""
import json
J = json.load(open('/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/baseline_v5/readings/read6_v23_supplement.json'))
print('top', sorted(J)[:40])
C = J['cells']['TRUCK']
print('TRUCK keys', sorted(C))
mro = C['map_report_only']
print('map_report_only arms', len(mro), sorted(mro)[:30])
p = mro['p333']
print('p333 keys', sorted(p))
