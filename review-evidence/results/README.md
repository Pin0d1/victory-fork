# Results on Windows 11

The GPU comparisons used separate Cargo target directories per source tree. Before running them, the driver checked that each binary listed the test introduced by its own patch. Each data point below was repeated in a fresh process. The strict harness prints the adapter ID and confirms the debug layer, GPU-based validation, synchronized queue validation and full state tracking. The transcripts use LF line endings and omit trailing whitespace.

| Input | Baseline | Change | Runs |
| --- | --- | --- | --- |
| Descriptor-using draw on RTX 2060 SUPER | Debug error 645. The probe requested 2,097,152 entries on a device reporting 1,000,000. | No debug errors. Every draw case still returned 16/16 green pixels and three IA vertices. | 2 per build |
| Same draw on WARP | Correct pixels, no debug errors | Correct pixels, no debug errors | 2 per build |
| Third indirect record is overwritten with zero vertices | 9 IA vertices | 6 IA vertices | 2 per adapter per build |
| #555 alias journal, two GPU readbacks, synchronous write destination | All 3 tests pass on the PR head with the test-only commit | | 2 per test |
| #71 delayed COPY followed by restoration | CPU word 29, then 29 again. The second GPU change flag was 0. The producer wrote 17. | [Snapshot candidate](../candidates/README.md) | 2 per adapter |
| #191 ordered stores then equality wait | Returned `(true, 0)`. Expected `(false, 1)`. | [Ordered-store candidate](../candidates/README.md) | 2 |
| #191 overlapping bytes through sibling mappings | All three checks returned `None`. Only the middle interval should produce a read dependency. | [Physical-dependency candidate](../candidates/README.md) | 2 per adapter |
| #220 ordered reference with GPU count 63 | Record 50 was `[0, 0, 50, 250]`. Expected `[5, 1, 50, 250]`. | [Admission policy candidate](../candidates/README.md) | 2 per adapter |

The [earlier snapshot controls](snapshot-control) each recorded 17 after the first fetch and again after restoration, with the second GPU change flag equal to zero. Three runs per adapter are retained.

The candidate patches linked in the last rows were evaluated in the earlier audit on the prerequisite trees listed there. The public-head transcripts here come from reruns on the pinned PR revisions. The scripts and outputs use synthetic data. The table reports buffer contents, draw counts and D3D12 diagnostics. [Machine-readable results](checks.json) · [Commands and pinned sources](../README.md)

Prepared with the help of Codex 6.2 Astra Max.
