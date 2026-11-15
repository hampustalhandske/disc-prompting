"""`disc-fetch`: download GloVe 840B 300d and CLIP ViT-B-32 (OpenAI weights) into `data/`.

GloVe is streamed from the Stanford zip and cut after the first 200,000 lines, so the 2 GB
archive is never stored. Only lowercase alphabetic words are kept, in file order, as
`glove/words.txt` plus `glove/vectors.npy` (float32, one 300-d row per word). CLIP goes to
`clip/` as the open_clip cache. A model already present is skipped.
"""

import argparse
import struct
import urllib.request
import zlib
from pathlib import Path

import numpy as np

from disc_mirror.graders.svg import CLIP_MODEL, clip_weights

GLOVE_URL = "https://downloads.cs.stanford.edu/nlp/data/glove.840B.300d.zip"
GLOVE_LINES = 200_000
DIM = 300


def _zip_lines(url: str):
    """Yield text lines of the first (deflated) member of a remote zip, streaming."""
    with urllib.request.urlopen(url, timeout=60) as resp:
        header = resp.read(30)
        if header[:4] != b"PK\x03\x04":
            raise SystemExit(f"{url} is not a zip file")
        if struct.unpack("<H", header[8:10])[0] != 8:
            raise SystemExit(f"{url}: first zip member is not deflate-compressed")
        name_len, extra_len = struct.unpack("<HH", header[26:30])
        resp.read(name_len + extra_len)
        inflate = zlib.decompressobj(-zlib.MAX_WBITS)
        tail = b""
        while chunk := resp.read(1 << 20):
            *lines, tail = (tail + inflate.decompress(chunk)).split(b"\n")
            for line in lines:
                yield line.decode("utf-8", errors="replace")


def fetch_glove(directory: Path) -> None:
    """Write `words.txt` and `vectors.npy` under `directory` unless both exist."""
    words_path, vectors_path = directory / "words.txt", directory / "vectors.npy"
    if words_path.exists() and vectors_path.exists():
        print(f"glove already at {directory}")
        return
    directory.mkdir(parents=True, exist_ok=True)
    words: list[str] = []
    rows: list[np.ndarray] = []
    seen: set[str] = set()
    for n, line in enumerate(_zip_lines(GLOVE_URL)):
        if n >= GLOVE_LINES:
            break
        word, *values = line.rstrip().split(" ")
        if word.isalpha() and word.islower() and word not in seen and len(values) == DIM:
            seen.add(word)
            words.append(word)
            rows.append(np.asarray(values, dtype=np.float32))
    words_path.write_text("\n".join(words) + "\n")
    np.save(vectors_path, np.stack(rows))
    print(f"glove: {len(words)} words to {directory}")


def fetch_clip(directory: Path) -> None:
    """Download the CLIP OpenAI weights into `directory` unless they are fully there."""
    if clip_weights(directory):
        print(f"clip already at {directory}")
        return
    import open_clip

    open_clip.create_model_and_transforms(CLIP_MODEL, pretrained="openai", cache_dir=str(directory))
    print(f"clip: ViT-B-32 to {directory}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="disc-fetch", description="`disc-fetch` command line.")
    ap.add_argument("--data", type=Path, default=Path("data"), help="target directory")
    args = ap.parse_args(argv)
    fetch_glove(args.data / "glove")
    fetch_clip(args.data / "clip")
