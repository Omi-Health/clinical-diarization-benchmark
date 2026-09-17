"""Verify the frozen audio, or explicitly check LFS pointers in a lightweight clone."""
import argparse
import hashlib
import json
import re
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root, allow_lfs_pointers=False):
    manifest = json.loads((root / "data/manifest.json").read_text())
    audio_count = pointer_count = 0
    for row in manifest["recordings"]:
        path = root / "data/raw_audio" / (row["case"] + "_conversation.wav")
        if not path.is_file():
            raise ValueError(f"Missing {path.name}; run git lfs pull")
        with path.open("rb") as handle:
            prefix = handle.read(200)
        if prefix.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
            if not allow_lfs_pointers:
                raise ValueError(f"{path.name} is an LFS pointer; run git lfs pull")
            pointer = path.read_text()
            oid = re.search(r"^oid sha256:([0-9a-f]{64})$", pointer, re.M)
            size = re.search(r"^size ([0-9]+)$", pointer, re.M)
            # The frozen inputs have a 44-byte WAV header and PCM16 mono samples.
            expected_size = 44 + round(row["audio_duration_s"] * row["sample_rate_hz"]) * row["channels"] * 2
            if not oid or oid.group(1) != row["audio_sha256"] or not size or int(size.group(1)) != expected_size:
                raise ValueError(f"LFS pointer mismatch: {path.name}")
            pointer_count += 1
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != row["audio_sha256"]:
            raise ValueError(f"Audio hash mismatch: {path.name}")
        with wave.open(str(path)) as wav:
            actual_format = (wav.getframerate(), wav.getnchannels(), wav.getsampwidth())
            expected_format = (row["sample_rate_hz"], row["channels"], 2)
            if actual_format != expected_format:
                raise ValueError(f"WAV format mismatch: {path.name}")
            if abs(wav.getnframes() / wav.getframerate() - row["audio_duration_s"]) > 1e-6:
                raise ValueError(f"Audio duration mismatch: {path.name}")
        audio_count += 1
    return audio_count, pointer_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-lfs-pointers", action="store_true",
                        help="Validate pointer hash/size without claiming audio bytes were downloaded")
    args = parser.parse_args()
    audio_count, pointer_count = verify(ROOT, args.allow_lfs_pointers)
    print(f"Verified {audio_count} WAV files and {pointer_count} LFS pointers (pointer contents only).")
