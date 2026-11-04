"""Upstream travel of a dipped-speed group, measured from where X acts (V342)."""
from collections import deque

import numpy as np

T_N, X_N = 150, 65


def beyond(v, n, v0, n0, x0):
    ok = (n >= 2) & (n0 >= 2) & (v0 > 0)
    mask = np.zeros_like(ok)
    mask[ok] = 1.0 - v[ok] / v0[ok] >= 0.30
    j0 = int(x0 // 100)
    mask[:, j0:] = False
    seen = np.zeros_like(mask)
    best = (0.0, 0.0)
    for t0, x in zip(*np.nonzero(mask)):
        if seen[t0, x]:
            continue
        q, cells = deque([(t0, x)]), []
        seen[t0, x] = True
        while q:
            a, b = q.popleft()
            cells.append((a, b))
            for da in (-1, 0, 1):
                for db in (-1, 0, 1):
                    c, d = a + da, b + db
                    if 0 <= c < T_N and 0 <= d < X_N and mask[c, d] and not seen[c, d]:
                        seen[c, d] = True
                        q.append((c, d))
        if len(cells) < 3 or max(c[1] for c in cells) < j0 - 2:
            continue
        lo = min(c[1] for c in cells)
        r = (j0 - lo) * 100.0
        if r > best[0]:
            t_start, t_far = min(c[0] for c in cells), min(c[0] for c in cells if c[1] == lo)
            best = (float(r), r / max((t_far - t_start) * 10.0, 10.0))
    return best
