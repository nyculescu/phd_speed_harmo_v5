import numpy as np
z = np.load("/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/f_scalars.npz", allow_pickle=True)
print("files", len(z.files), z.files[:70])
K = list(z["keys"]) if "keys" in z.files else None
print("n keys", len(K) if K else None)
print([k for k in K if any(s in k for s in ("coll", "full", "passed", "stuck", "backlog", "all_delay", "ttc_net", "seed", "contact"))])
for a in z.files[:3]:
    print(a, z[a].shape)
