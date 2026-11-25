# Check a prefetched draw against the vertices the GPU executed

Six DRAW records start with three vertices each. Between recording the second and third draws, the test uses the deferred guest-copy path to replace the third record with a zero-vertex draw. After the DIRECT queue completes, it reads the guest word, the pipeline-statistics IA vertex count, the 4 × 4 render target and the window checker's counters for this list. The expected vertex count is 18 for the unchanged control and 15 for the copy.

The table applies to both tested #220 revisions, the one named in the RTX 5080 report (`f873394`) and the merge with `main` (`8107935`). The same test patch applied to all four builds.

| Source | Guest copy | Third DRAW vertex count in guest memory | IA vertices | Checker hits | Differences | Green pixels |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| #220 | No | 3 | 18 | 4 | 0 | 16 |
| #220 | Yes | 0 | 18 | 4 | 0 | 16 |
| #220 with #663 | No | 3 | 18 | 4 | 0 | 16 |
| #220 with #663 | Yes | 0 | 15 | 2 | 0 | 16 |

For each #220 revision, each row repeated twice on an RTX 2060 SUPER and twice on WARP. The existing positive control in #220 also passed twice per adapter and build. Its direct GPU write changed a dispatch record from `[5, 1, 1]` to `[11, 2, 1]`. The test patch prints those two records after the upstream assertions pass. [All 32 process transcripts](transcripts.txt) · [Test-only patch](guest-copy.patch)

On a window hit, #220 gives the checker the current GPU Shadow buffer. The guest copy can change guest memory while both the fresh clamp and the window still see the previous Shadow contents. With #663 the copy invalidates the window, so the next draw refreshes its arguments. The checker runs only on hits. The warning reports the previous execution of one host list. The periodic summary accumulates counts across lists. The RTX 5080 report used a different build. The writer responsible for those 88 mismatches is still unknown. [Window hit and refresh](https://github.com/fxceless/victory-fork/blob/f8733949f1d317e79a66365cd4036eb76cb9930b/crates/victory-gpu/src/draw.rs#L2374-L2418) · [Counter reporting](https://github.com/fxceless/victory-fork/blob/f8733949f1d317e79a66365cd4036eb76cb9930b/crates/victory-gpu/src/indirect.rs#L628-L649) · [RTX 5080 report](https://github.com/fxceless/victory-fork/pull/220#issuecomment-7153344934)

## Reproduce on Windows

From a fresh directory in an x64 Windows developer shell, use Git, the project's pinned Rust toolchain, the Windows SDK and Windows Graphics Tools. The inputs and shaders are synthetic. To repeat the comparison on the earlier #220 revision, run the same commands in another fresh directory with `$pr` set to `f8733949f1d317e79a66365cd4036eb76cb9930b`.

```powershell
git clone --depth 1 --single-branch --branch review/gpu-validation https://github.com/Pin0d1/victory-fork.git evidence
git clone --no-checkout https://github.com/fxceless/victory-fork.git source
$pr = '810793582a76c0a15da8dbfa21d69fb1a54c7aaa'
$fix = '845fc43e2c536d121b7f34df902e3395c4d7fe2d'
git -C source fetch --no-tags origin $pr
git -C source fetch --no-tags https://github.com/Pin0d1/victory-fork.git $fix
git -C source worktree add --detach ../as-submitted $pr
git -C source worktree add --detach ../with-663 $pr
$fixPatch = Join-Path (Get-Location) 'window-invalidation.patch'
git -C source diff "--output=$fixPatch" "${fix}^" $fix
git -C with-663 apply $fixPatch
$probe = (Resolve-Path 'evidence/review-evidence/window-check/guest-copy.patch').Path
git -C as-submitted apply $probe
git -C with-663 apply $probe
```

Run the following in each worktree. Use a fresh process for each test and adapter. For WARP set `$env:VICTORY_D3D12_WARP = '1'`. For hardware set `$env:VICTORY_D3D12_WARP = $null`. The new test intentionally fails its vertex-count assertion on each unmodified PR head.

```powershell
$env:CARGO_TARGET_DIR = Join-Path (Get-Location) 'target-check'
$env:VICTORY_INDIRECT_WINDOW = '1'
$env:VICTORY_INDIRECT_WINDOW_CHECK = '1'
$env:VICTORY_D3D12_DEBUG = '1'
cargo test --locked -p victory-gpu --features diagnostics --lib compare_window_checker_with_executed_vertices -- --nocapture --test-threads=1
cargo test --locked -p victory-gpu --features diagnostics --lib host_list_window_check_finds_a_record_written_under_its_window -- --nocapture --test-threads=1
```

Prepared with the help of Codex 6.2 Astra Max.
