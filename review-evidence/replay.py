"""Reproduce one pinned synthetic GPU check in a new Windows checkout."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

UPSTREAM = "https://github.com/fxceless/victory-fork.git"
FORK = "https://github.com/Pin0d1/victory-fork.git"
HERE = Path(__file__).resolve().parent
CASES = {
    "main": (UPSTREAM, "310c6eb6c16822ab95076aad61fce19bba86bb98", "gpu-validation",
             ["audit_render_indirect", "copied_arguments_replace_a_prefetched_record"]),
    "view-heap": (FORK, "9576cc278a6ebad457641235698506a548847c5a", "gpu-validation",
                  ["audit_render_indirect", "shader_view_limit_fits_the_reported_heap"]),
    "indirect-window": (FORK, "845fc43e2c536d121b7f34df902e3395c4d7fe2d", "gpu-validation",
                        ["copied_arguments_replace_a_prefetched_record",
                         "indirect_window_ends_at_a_copy_or_unknown_writer"]),
    "pr71": (UPSTREAM, "c57c9b09a7fd74c366392c373ceb61ca99e8c18a", "pr71",
             ["unchanged_hash_does_not_repair_a_mismatched_readback"]),
    "pr191": (UPSTREAM, "1582757f123f5e49f46ca33fc96c782182c3599f", "pr191",
              ["value_wait_after_an_overwrite_does_not_observe_the_earlier_match"]),
    "pr191-physical": (UPSTREAM, "1582757f123f5e49f46ca33fc96c782182c3599f", "pr191-physical",
                       ["a_late_store_blocks_copying_only_the_overlapping_bytes_of_another_view"]),
    "pr220": (UPSTREAM, "f8733949f1d317e79a66365cd4036eb76cb9930b", "pr220",
              ["ordered_budget_rejects_a_record_without_consuming_the_remainder"]),
    "pr555": (FORK, "b63010881edd8d98e2eef0754bf38e474b0ce35b", None,
              ["actual_shadow_readbacks_follow_each_alias",
               "both_alias_consumers_observe_a_write",
               "kernel_destination_stays_writable_until_a_synchronous_read_returns"]),
}

def dxc():
    explicit = os.environ.get("VICTORY_PC_DXC") or shutil.which("dxc")
    if explicit:
        return Path(explicit)
    kits = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10/bin"
    return max(kits.glob("*/x64/dxc.exe"), key=lambda p: tuple(map(int, p.parents[1].name.split("."))))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("directory", type=Path, help="A new directory for this checkout")
    parser.add_argument("--warp", action="store_true", help="Select the Windows software adapter")
    args = parser.parse_args()
    root = args.directory.resolve()
    if root.exists():
        parser.error("Choose a new directory so the source revision and Cargo artifacts are unambiguous.")
    remote, sha, patch, tests = CASES[args.case]
    subprocess.run(["git", "clone", "--no-checkout", remote, str(root)], check=True)
    def git(*cmd):
        subprocess.run(["git", "-C", str(root), *cmd], check=True)
    git("fetch", "--no-tags", "origin", sha)
    git("checkout", "--detach", sha)
    if patch:
        git("apply", "--whitespace=nowarn", str(HERE / "probes" / (patch + ".patch")))
    env = dict(os.environ, CARGO_TARGET_DIR=str(root / "target-replay"))
    if args.warp:
        env["VICTORY_D3D12_WARP"] = "1"
    else:
        env.pop("VICTORY_D3D12_WARP", None)
    if patch == "gpu-validation":
        env.update(VICTORY_D3D12_DEBUG="1", VICTORY_RELAY="2",
                   VICTORY_AUDIT_ADAPTER="WARP" if args.warp else "RTX")
        for entry in ("ms", "ps"):
            output = root / "crates/victory-gpu/src/pipeline" / ("review-" + entry + ".bin")
            subprocess.run([str(dxc()), "-T", entry + "_6_5", "-E", entry, "-Fo", str(output),
                            str(HERE / "probes/mesh.hlsl")], check=True)
    failures = 0
    for test in tests:
        if patch == "gpu-validation":
            env["VICTORY_INDIRECT_WINDOW"] = "1" if test.startswith("copied_arguments") else "0"
        result = subprocess.run(["cargo", "test", "--locked", "-p", "victory-gpu", "--features",
                                 "diagnostics", "--lib", test, "--", "--test-threads=1", "--nocapture"],
                                cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = result.stdout.decode("utf-8", "replace")
        print(text, end="", flush=True)
        log = root / (test + ".log")
        log.write_bytes(result.stdout)
        if result.returncode or "1 passed" not in text:
            failures += 1
        if patch == "gpu-validation":
            adapter = "software=true" if args.warp else "software=false"
            if adapter not in text or "synchronized_queue=1 full_state_tracking=1" not in text:
                failures += 1
            if re.search(r"VALIDATION_MESSAGE id=\d+ severity=[01]\b", text):
                failures += 1
    return int(bool(failures))

if __name__ == "__main__":
    raise SystemExit(main())
