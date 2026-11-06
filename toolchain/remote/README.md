# Running v5b1 on a rented machine

Two scripts take a fresh Ubuntu CLI machine to a working, checked copy of the project:
- `remote.sh` runs on the laptop;
- `bootstrap.sh` runs on the remote.

No GitHub key or other secret goes to the remote. The code travels as a `git archive` of HEAD, and results come back with rsync.

Status: written on 2026-11-06 and not yet run on a remote. The first deploy is its test.

## Minimum machine

| | Minimum (one training slot or evaluation, like the laptop) | For four training slots at once |
|---|---|---|
| CPU | x86-64, 16 cores / 32 threads, boost ≥ 5 GHz (e.g. Ryzen 9 7950X or 9950X) | x86-64, 64+ cores / 128 threads |
| RAM | 32 GB | 64 GB |
| Disk | 30 GB | 50 GB |
| GPU | none (SUMO and the small policy nets run on the CPU) | none |
| OS | Ubuntu 22.04 (vast.ai's base) or later. Before 26.04, Python 3.14 comes as uv's standalone build. | same |

The sizes come from the laptop (i9-13980HX, 32 threads):
- **Training slot:** 5 learners × 3 SUMO envs is about 20 processes and 5 GB of memory, peaking at 6.5 GB (measured 2026-11-06).
- **Evaluation:** fastest at threads − 1 workers (31 on 32; V425-V426).
- **Disk:** the venv takes 2.1 GB, and round 1's outputs 64 MB.

One PPO update waits for its slowest SUMO episode and then a single-thread update, which takes 29.5 s on the laptop. Clock speed therefore sets the time per update, and core count sets how many slots and evaluation workers run at once. A many-core server CPU at about 3.5 GHz is likely to update more slowly than the laptop. That is an estimate, not a measurement.

ARM is untested. The pinned libsumo and torch CPU wheels are x86-64 builds.

## One command

From nothing to a running job, from the repo on the laptop:
```
bash toolchain/remote/remote.sh launch NAME 'python ...'
```
This:
1. picks the cheapest vast.ai offer that fits one training, and shows it;
2. rents it after you type `yes`;
3. waits for SSH, deploys and runs the acceptance checks;
4. starts the job only if the checks pass.

If you have already rented in the console, paste the instance's SSH command instead:
```
bash toolchain/remote/remote.sh up "ssh -p 41234 root@ssh5.vast.ai" NAME 'python ...'
```
Every command below also takes the pasted SSH command in place of `HOST PORT`.

Renting goes through `vast.py`, which wraps the vastai CLI 1.11.0. The CLI lives in its own venv at `/home/catalin/work/phd/vastai_venv`, apart from the locked toolchain.
- `vast.py offers [N]`: list the cheapest fitting offers. Spends nothing.
- `vast.py rent [OFFER_ID]`: rent that offer, or the cheapest.
- `vast.py list`: your instances.
- `vast.py destroy ID`: stop the instance and its billing. Fetch results first.

The fit is:
- x86-64;
- ≥ 24 threads allocated;
- ≥ 32 GB RAM;
- ≥ 40 GB disk;
- reliability > 0.99;
- ≥ 2 days maximum duration;
- ≥ 100 Mbps download;
- no Xeon E5/E7 (2014–2016, about half the laptop's speed per core).

Renting and destroying ask for a typed `yes`. `--yes` skips the prompt and is only for an offer the author approved in writing.

Once per laptop:
- `vastai set api-key KEY`;
- the laptop's public SSH key added to the vast.ai account.

Template settings:
- base it on "NVIDIA CUDA" (`vastai/base-image`), a container. The "Ubuntu 22.04 VM" template (`vastai/kvm`) only runs on hosts with `vms_enabled=true`, which leaves far fewer offers;
- launch mode: interactive shell server, SSH, with direct SSH on;
- no ports and no Docker options;
- disk 40 GB;
- Private;
- extra filters `cpu_arch in ['amd64'] cpu_cores_effective>=24 cpu_ram>=32 reliability>0.99`;
- On-start Script: the whole of `onstart.sh`. It builds the venv in the background during boot, then runs the stock `entrypoint.sh`. `bootstrap.sh` waits for the build and reuses what it built.

The machine's image comes from a saved console template. Make it from "NVIDIA CUDA" (`vastai/base-image`): launch type SSH, 40 GB disk, no on-start script. Put its hash in `toolchain/remote/vast_template`, or in `VAST_TEMPLATE`. Without a template, the launch uses `VAST_IMAGE`, which defaults to `ubuntu:22.04`; whether that image has SSH ready is untested.

## Acceptance checks

Every deploy runs these checks; a job starts only if all of them pass:
1. imports and the netconvert version;
2. `tests/test_round1.py`;
3. `checks1.py rows`: rows stored on the laptop (simulation, rules and a trained policy) must reproduce on every key;
4. `fingerprint.py`: one fixed-seed training update must give the same weight fingerprint as on the laptop.

The laptop's reference lives in `fingerprint.ref` and belongs to one version of `v5b/`. Make it on the laptop with `fingerprint.py OUT --write toolchain/remote/fingerprint.ref` when no training is running, and remake it whenever `v5b/` changes. Without a valid reference, check 4 says so and does not fail.

If checks 3 and 4 pass on every machine, the hardware cannot change the results. Trainings may then run one per machine, and the candidates still compare fairly.

## Steps

1. **Rent.** Pick an Ubuntu image with SSH access. Add the laptop's public key (`~/.ssh/id_ed25519.pub`) to the provider's account. Note the host and port from its SSH command, e.g. `ssh -p 41234 root@ssh5.vast.ai`. These are vast.ai-style details; check them in the provider's console.
2. **Deploy**, from the repo on the laptop:
   ```
   bash toolchain/remote/remote.sh deploy HOST PORT
   ```
   This runs:
   - apt packages;
   - Python 3.14;
   - the venv at the laptop's path `/home/catalin/work/phd/phd_speed_harmo_v5b1_toolchain/venv`, from `toolchain/requirements_lock.txt`;
   - `tests/test_round1.py`;
   - `checks1.py rows`: rows stored on the laptop must reproduce on every key.

   It ends with `ACCEPT PASS`. Expected time is a few minutes plus the rows check, but that is untested.
3. **Run** a job in tmux. It survives logout and stays pinned to the snapshot it started from:
   ```
   bash toolchain/remote/remote.sh run HOST PORT NAME 'python -m v5b.fleet.c_train ...'
   ```
   `python` is the venv's, because `env.sh` puts the venv first on PATH. It also unsets `SUMO_HOME` and sets `OMP_NUM_THREADS=1`.
4. **Watch** with `remote.sh status HOST PORT`.
5. **Fetch** with `remote.sh fetch HOST PORT RUN`. Results land in `/home/catalin/work/phd/v5b1_runs/RUN_remote` on the laptop.
6. **Stop the rental** once the results are fetched.

## Rules that change on a remote

- **Paths.** The remote mirrors the laptop's paths under `/home/catalin/work/phd`. Scripts with hard-coded paths, such as `chain1.sh` and `common1.py`, therefore run unchanged.
- **Workers.** `chain1.sh` fixes `W=31`. Future scripts should take the worker count from the machine: threads − 1.
- **CPU and fans.** The CPU guard, the night cap (V432) and the health monitor's coretemp reading serve the laptop's fans and heat. They are not deployed here. Containers usually have no systemd and no coretemp. Whether the 90 % rule applies on a rented machine is the author's call.
- **Numbers across machines.** A different CPU or build can change results in the last digits, and trajectories can then diverge. The `rows` check shows whether that happens. Every arm of one comparison is trained and evaluated on one platform. A move in the middle of a round is a protocol deviation and goes in the ledger.
- **Seeds.** Seeds follow the same approval rule as on the laptop.
