# Correction to baseline v1

`BASELINE.md` stays as written, as the record of that check. V367 found that its braking at 3, 4.5 and 7 m/s², free-road ALKS braking and sawtooth statements do not hold: they come from a once-per-second sample that misses P0's hard ALKS braking. Flow, delay, TTC and fuel were not biased by the sampling. Use baseline v2 (V376).
