"""Reads scalar tags from TensorBoard event files with the standard library only."""
import struct, sys, glob, statistics as st

def varint(b, i):
    x = s = 0
    while True:
        c = b[i]; i += 1
        x |= (c & 0x7F) << s
        if c < 0x80:
            return x, i
        s += 7

def fields(b):
    i = 0
    while i < len(b):
        k, i = varint(b, i)
        f, w = k >> 3, k & 7
        if w == 0:
            v, i = varint(b, i)
        elif w == 1:
            v = b[i:i + 8]; i += 8
        elif w == 2:
            n, i = varint(b, i); v = b[i:i + n]; i += n
        elif w == 5:
            v = b[i:i + 4]; i += 4
        else:
            return
        yield f, w, v

def scalars(path, want):
    out = {}
    with open(path, "rb") as fh:
        while True:
            h = fh.read(12)
            if len(h) < 12:
                break
            n = struct.unpack("<Q", h[:8])[0]
            d = fh.read(n); fh.read(4)
            step, summ = 0, None
            for f, w, v in fields(d):
                if f == 2 and w == 0:
                    step = v
                elif f == 5 and w == 2:
                    summ = v
            if summ is None:
                continue
            for f, w, v in fields(summ):
                if f != 1:
                    continue
                tag = val = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1 and w2 == 2:
                        tag = v2.decode()
                    elif f2 == 2 and w2 == 5:
                        val = struct.unpack("<f", v2)[0]
                if tag is not None and val is not None and (want is None or tag in want):
                    out.setdefault(tag, {})[step] = val
    return out

if __name__ == "__main__":
    d = sys.argv[1]
    want = set(sys.argv[2].split(",")) if len(sys.argv) > 2 and sys.argv[2] != "ALL" else None
    for run in sorted(glob.glob(d + "/C*")):
        for f in sorted(glob.glob(run + "/events.out.tfevents.*")):
            s = scalars(f, want)
            if want is None:
                print(run.split("/")[-1], sorted(s))
                continue
            for tag in sorted(s):
                xs = [s[tag][k] for k in sorted(s[tag])]
                if tag == "ppo/wall_s":
                    dd = [b - a for a, b in zip(xs, xs[1:])]
                    print(run.split("/")[-1], tag, "updates", len(xs), "first %.1f last %.0f" % (xs[0], xs[-1]), "per-update median %.1f min %.1f max %.1f" % (st.median(dd), min(dd), max(dd)))
                else:
                    print(run.split("/")[-1], tag, "updates", len(xs), "median %.4g min %.4g max %.4g mean %.4g" % (st.median(xs), min(xs), max(xs), st.fmean(xs)))
