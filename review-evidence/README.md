# Windows renderer regression tests

This directory contains synthetic inputs, source patches and process transcripts for specific VIctory GPU changes. The two production changes each have one commit on top of `310c6eb6c16822ab95076aad61fce19bba86bb98`. The review probes live on this branch so they can also run against the unmodified implementation.

## Reproduce a result

Use an x64 Windows developer shell with Git, Python 3, the repository's pinned Rust toolchain and the Windows SDK. Install Windows Graphics Tools for the debug-layer cases. The GPU harness compiles its small mesh shader locally with the SDK's `dxc.exe`.

```powershell
git clone --branch review/gpu-validation --single-branch https://github.com/Pin0d1/victory-fork.git review-material
$replay = ".\review-material\review-evidence\replay.py"
python $replay main .\main-hardware
python $replay view-heap .\heap-hardware
python $replay indirect-window .\window-hardware
python $replay main .\main-warp --warp
python $replay indirect-window .\window-warp --warp
```

Pass a fresh directory for each invocation. The driver fetches the pinned commit and builds into the new checkout. It prints the complete test output, saves each transcript beside the checkout's Cargo manifest and reports a failed assertion or a debug-layer error with a nonzero exit code. The default selects the hardware adapter that D3D12 would normally use. `--warp` selects software rendering.

| Case | What it checks |
| --- | --- |
| `main`, `view-heap` | A synthetic draw runs with D3D12 debug, GPU-based and synchronized queue validation. Check the reported adapter, D3D12 message IDs and all 16 pixels. |
| `main`, `indirect-window` | Three draws initially have three vertices each. A copy replaces the third record with a zero-vertex draw. The independent answer is six input-assembler vertices. |
| `pr555` | Two GPU Shadow readbacks, two journal consumers of section aliases and a synchronous file read with overlapping destination holders. |
| `pr71` | The producer writes 17. A second DIRECT submission writes 29 before the delayed COPY read. A third submission restores 17 and performs the GPU hash comparison again. |
| `pr191` | Ordered stores of 1 and 0 precede an equality wait for 1. The test reads both the prediction and the count retained by the submission wait list. |
| `pr191-physical` | Separate virtual mappings expose overlapping bytes of one section. Adjacent ranges and a removed mapping provide controls. |
| `pr220` | A CPU reference admits affordable records in input order and keeps the remainder when it rejects a record. The test compares each live GPU record and its payload against that policy. |

The publication retest used Windows 11, a Ryzen 5 5600, an RTX 2060 SUPER and WARP. The conclusions concern these synthetic inputs. [Run transcripts](results) · [Candidate patches and source trees for the open PR discussions](candidates/README.md)

Prepared with the help of Codex 6.2 Astra Max.
