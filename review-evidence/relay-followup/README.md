# Relay readback and ordered waits on Windows

These synthetic tests compare the actual CPU-visible words after D3D12 submissions. They use the implementation's normal compare, plan and landing code. No game files are needed. The revision and SHA-256 of each test patch are in [runs.json](runs.json). Every matrix row names its [process transcript](transcripts), including the expected failing assertions.

## Which submission supplied the bytes?

Each 64 KiB piece starts on a 64 KiB boundary and has a known first word. The first tracked DIRECT submission writes 17. In the two-flight case, a second tracked submission writes 29 to the same pieces. Both GPU submissions complete before the test asks the relay to land the first one. The first landing should return 17 for every piece and the second should return 29 for every piece. The test controls the landing schedule directly.

A separate persistence test overwrites the live DIRECT resource with 29 without registering a second plan, lands the first plan, restores 17 on DIRECT, and submits a tracked compare of the same ranges. That compare reports zero changed pieces. The test records any CPU words that still contain 29. These two schedules check different guarantees.

| Build and settings | Pieces | First landing, producer words | First landing, later words |
| --- | ---: | ---: | ---: |
| #688 at 7e7bb18, staging enabled | 256 | 256 | 0 |
| #688 at 7e7bb18, staging enabled | 257 | 256 | 1 |
| fxceless main at 9376fd6, in-flight staging enabled, 1 MiB | 16 | 16 | 0 |
| Same main and settings | 17 | 0 | 17 |
| #648 at 4d28486, in-flight staging enabled, 1 MiB | 4 | 4 | 0 |
| Same #648 and settings | 5 | 4 | 1 |
| Same #648 and settings | 17 | 4 | 13 |
| Pooled #71 comparison branch at 981eaae | 257 | 257 | 0 |

Each row repeated twice per adapter on an RTX 2060 SUPER and WARP. The two-flight test also read 29 from every word of the second landing. The persistent control preserved exactly the stale words from the first landing after the unchanged compare. On #688, all 256 staged pieces had a staging flag and the extra piece carried the overflow flag. On #648 and main, the printed staging/overflow bit fields belong to the #688 encoding and have no meaning. The 1 MiB setting deliberately exercises overflow. Measuring the frequency of overflow during gameplay requires a game trace.

## Reuse of completed snapshots on #71

The comparison is between ef4f510 and its single follow-up commit 981eaae. Both use the original 310c6eb + c57c9b0 comparison base, copy the producer's declared ranges on DIRECT and retain that data until the relay finishes. The follow-up pools placement-aligned buffers. Its 64 MiB cap includes idle buffers and buffers still in use. Under pressure it evicts idle buffers or uses the existing wait for a live fetch. Reuse can retain up to 64 MiB after a burst.

The allocation test warms up one flight at each of 1, 2, 4 and 8 MiB, then repeats the size sequence for 48 flights. One word changes per flight. It waits for landing, checks the CPU word every time and reads the delta of the renderer's device-local UAV buffer creation and requested-byte counters. Three fresh processes were run per build and adapter, alternating build order. After warm-up the original made 48 allocations totalling 180 MiB per run. The pool made zero in each run. The measured workload still copies 180 MiB on DIRECT. Wall time in each log covers the 48 complete synthetic flights, including CPU work and fence waits. The allocation counters accumulate over the run. Repeated game measurements on the new branch remain outstanding. [RTX 5080 report on the original snapshot](https://github.com/fxceless/victory-fork/pull/71#issuecomment-7156304501)

On the clean pooled branch, the locked all-features workspace suite passed 522 tests with 9 ignored. Two GPU tests also launched child processes for isolation. The release build of victory-gpu and the asset policy check passed. The policy checked 169 files.

## Ordered queue waits on #785

The test installs the specified ordered stores in the pending list, then calls both the predictor and the production queue predicate used by release_held. The CPU word is a mapped local u64 and the equality wait asks for 1. On 67c6c89 the predictor returns false for queued stores 1 then 0. With a current CPU word of 0 the queue returns false. With a current CPU word of 1 the same queue returns true before the stores land. An empty list with CPU value 1 and a final queued store of 1 serve as positive controls. The PR's own helper test passes. Both the new queue test and the main comparison are in the transcripts. The fixture calls the queue predicate directly.

## Reproducing the measurements

Use Windows x64, the Rust MSVC toolchain, the Windows SDK and DirectX Graphics Tools. The test machine used Rust 1.98.1, Windows 11, a Ryzen 5 5600, an RTX 2060 SUPER (10de:1f06) and WARP (1414:008c). Use a separate checkout and Cargo target directory for each build. To reproduce #688, open PowerShell in the checkout containing this evidence directory.

~~~powershell
$evidence = (Resolve-Path 'review-evidence/relay-followup').Path
git fetch https://github.com/fxceless/victory-fork.git refs/pull/688/head
git worktree add --detach ../relay-check-688 7e7bb180625298dd418cb7ce71923140363ff02f
Push-Location ../relay-check-688
git apply --check "$evidence/patches/pr688.patch.txt"
git apply "$evidence/patches/pr688.patch.txt"
$env:CARGO_TARGET_DIR = Join-Path $PWD 'target-review'
$env:VICTORY_RELAY = '2'
$env:VICTORY_CARD_BUFFERS = '1'
$env:VICTORY_CARD_BUFFERS_MIN_MB = '1'
$env:VICTORY_KEEP_SNAPSHOTS = '0'
$env:VICTORY_RELAY_COPY_QUEUE = '1'
$env:VICTORY_CARD_INLINE_STAGE = '1'
$env:VICTORY_D3D12_DEBUG = '1'
$env:PROBE_PIECES = '257'
$env:PROBE_TRACKED_LATER = 'yes'
cargo test --locked -p victory-gpu --lib --features diagnostics host::followup_readback::changed_pieces_preserve_the_producer_after_a_later_direct_write -- --exact --nocapture --test-threads=1
Pop-Location
~~~

For the persistence case, clear the PROBE_TRACKED_LATER environment variable. For the boundary control, set PROBE_PIECES to 256. Set VICTORY_D3D12_WARP=1 for WARP and clear it for the hardware run. Confirm the adapter ID in the transcript. The readback patch requires the debug layer, GPU-based validation, synchronized queue validation and full resource-state tracking whenever VICTORY_D3D12_DEBUG is set. It prints validation messages independently of the byte assertions.

For #648 and main, use the matching patch and revision in runs.json, set VICTORY_CARD_FETCH_INFLIGHT=1 and VICTORY_CARD_FETCH_INFLIGHT_MB=1. For the two #71 builds, fetch the candidate and its parent from the personal fork.

~~~powershell
git fetch https://github.com/Pin0d1/victory-fork.git refs/heads/review/pr71-pooled-snapshots
~~~

Apply the matching original-snapshot or pooled-snapshot test patch. To run the 48-flight benchmark, clear VICTORY_D3D12_DEBUG and use the same Cargo command with test name host::followup_pool_bench::repeated_flights_measure_committed_snapshot_creation. For #785 use pr785.patch.txt, VICTORY_LATE_WAIT=1 and test name list::pending_overwrite_goes_through_the_queue_predicate. The main.patch.txt file also carries that queue test.

The matrix also records three earlier [alias tests](https://github.com/Pin0d1/victory-fork/commit/b63010881edd8d98e2eef0754bf38e474b0ce35b) shared by #438 and #555, and targeted raster, heap and indirect-window checks from the local merges of #662 and #663 with 9376fd6. Their earlier [test fixtures](https://github.com/Pin0d1/victory-fork/tree/8d327133b76d0decf8b859a48f38e58f3a08aa35/review-evidence) are public.

Prepared with the help of Codex 6.2 Astra Max.
