# Round 4 adaptivity headroom scan (Addendum E): results

*2026-10-03 06:50 · raw `/home/catalin/work/phd/vsl_lab_runs/t2/round4_gscan_1791033206` · J = delay + 40 s/stop, median of 10 seeds*

**DRL targets (G ≥ 10 % and H ≥ 10 %): none**

| family | G | H | pooled best | per-condition best | J pooled | J lookup | J adaptive |
|---|---|---|---|---|---|---|---|
| demand D1/D2/D3/D4 | 2.2% | 2.2% | const:0.75 | {'D1': 'nc', 'D2': 'const:0.8', 'D3': 'const:0.8', 'D4': 'const:0.75'} | 433.5 | 423.9 | 449.3 |
| compliance C1/D3/C2 | 0.8% | 0.8% | const:0.8 | {'C1': 'const:0.75', 'D3': 'const:0.8', 'C2': 'const:0.8'} | 419.4 | 416.2 | 450.3 |
| trucks K1/D3/K2 | 4.0% | 4.0% | const:0.8 | {'K1': 'const:0.7', 'D3': 'const:0.8', 'K2': 'const:0.85'} | 459.0 | 440.7 | 504.3 |
| incident D2/I1 | 2.5% | 2.5% | const:0.65 | {'D2': 'const:0.8', 'I1': 'const:0.65'} | 353.8 | 345.1 | 385.0 |
| incident D3/I2 | 1.4% | 1.4% | const:0.8 | {'D3': 'const:0.8', 'I2': 'const:0.75'} | 568.8 | 560.8 | 585.0 |

J per condition and controller (median of 10 seeds):

| controller | D1 | D2 | D3 | D4 | C1 | C2 | K1 | K2 | I1 | I2 |
|---|---|---|---|---|---|---|---|---|---|---|
| const:0.6 | 214 | 226 | 691 | 984 | 686 | 585 | 580 | 770 | 509 | 741 |
| const:0.65 | 205 | 218 | 633 | 931 | 665 | 608 | 544 | 734 | 490 | 710 |
| const:0.7 | 198 | 211 | 478 | 892 | 549 | 564 | 264 | 713 | 593 | 710 |
| const:0.75 | 192 | 203 | 450 | 889 | 491 | 505 | 325 | 672 | 590 | 700 |
| const:0.8 | 187 | 200 | 422 | 954 | 501 | 335 | 300 | 655 | 591 | 716 |
| const:0.85 | 189 | 205 | 552 | 901 | 525 | 468 | 367 | 636 | 568 | 715 |
| const:0.9 | 188 | 207 | 544 | 953 | 549 | 455 | 409 | 656 | 587 | 700 |
| nc | 184 | 201 | 535 | 900 | 499 | 504 | 521 | 679 | 582 | 734 |
| vslad:90:0.8 | 186 | 197 | 501 | 913 | 509 | 341 | 381 | 630 | 572 | 669 |
