# Proposed follow-ups to open PRs

These content patches record proposed changes discussed in the corresponding upstream threads. Each applies to its own source tree. The public production PRs for the descriptor query and the indirect window have separate branches.

Start with a fresh checkout at `c96b4f2b8365bf43d54ab074940923ef8267f4c6`. Cherry-pick the public commits in the order shown. `git rev-parse HEAD^{tree}` should match the listed source tree. Apply the indicated patch with `git apply --index` and check its result with `git write-tree`.

| Candidate | Commits to cherry-pick, in order | Source tree | Expected result tree |
| --- | --- | --- | --- |
| [Order waits after the last store](ordered-stores.patch) | `1582757f123f5e49f46ca33fc96c782182c3599f` (#191) | `d631dbf4ab29aa8941faa074a81b04a13063c860` | `2d1477703f53722f790e9d1273758848f03e2d6b` |
| [Capture changed ranges on the producing DIRECT queue](direct-snapshot.patch) | `e3962cc181a6d50028c80720e7f16fe971b46276`, `c57c9b09a7fd74c366392c373ceb61ca99e8c18a` (#71) | `4092ad20dad6e86b636d64bf6ba4fda52be52cdb` | `5a7e42d9124cc377ec648fa48cb49bfc7133387b` |
| [Resolve overlapping bytes through the alias index](physical-dependencies.patch) | `5af49b5d193b6d6b931676aa4c1066ed557bf401` (#555), `1582757f123f5e49f46ca33fc96c782182c3599f` (#191) | `3205a2e72eba6856f287e85777f4f0401b12e4cb` | `af9d422b63220ec2457fcc860d2f9da185f62c7d` |
| [Admit affordable records in input order](ordered-admission.patch) | `3550a2f119f84ff11f57a4898053a337ef10d460` (#204), `fec3bc865a429a39130bfd8bbd13b31ab07857d4` (#239) | `50b2c6b728352aab49841a701e0ccdb8f6a4ed6c` | `fc26f8fa0b99cb9a9934d6f9b5f630d6a72ff727` |

If a commit is missing locally, use `git fetch origin <SHA>` before cherry-picking it. In PowerShell, quote `'HEAD^{tree}'`. The [unchanged-hash check](snapshot-persistence-test.patch) applies after the DIRECT snapshot candidate. Run `cargo test -p victory-gpu --features diagnostics --lib unchanged_hash_does_not_repair -- --test-threads=1 --nocapture`.

Prepared with the help of Codex 6.2 Astra Max.
