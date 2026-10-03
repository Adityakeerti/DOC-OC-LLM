"""
analyze_layers.py — Transformer Layer Redundancy Profiling for Gemma-4-E2B.

Computes cosine similarity and representation distance across all 35 transformer
blocks to identify computational dead weight for layer pruning (ShortGPT algorithm).
"""

import gguf
import numpy as np
from pathlib import Path

MODEL_PATH = "/home/aditya/AI/models/Gemma-4-E2B/gemma-4-E2B_q4_0-it.gguf"


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two flat byte/numeric arrays."""
    a_f = a.astype(np.float32)
    b_f = b.astype(np.float32)
    norm_a = np.linalg.norm(a_f)
    norm_b = np.linalg.norm(b_f)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_f, b_f) / (norm_a * norm_b))


def analyze_model_layers():
    print(f"Loading GGUF metadata from: {MODEL_PATH}")
    reader = gguf.GGUFReader(MODEL_PATH)

    # Group tensors by block index
    blocks = {}
    for t in reader.tensors:
        if t.name.startswith("blk."):
            parts = t.name.split(".")
            b_idx = int(parts[1])
            sub_name = ".".join(parts[2:])
            blocks.setdefault(b_idx, {})[sub_name] = t

    total_blocks = len(blocks)
    print(f"Found {total_blocks} transformer blocks in architecture.")

    # Target key structural tensors for similarity analysis
    key_tensors = [
        "attn_output.weight",
        "attn_q.weight",
        "ffn_down.weight",
        "attn_norm.weight",
        "post_attention_norm.weight"
    ]

    similarities = []

    print("\n" + "=" * 70)
    print(f"{'Block Pair':<15} | {'Cosine Sim':<12} | {'Angular Distance (rad)':<22} | {'Redundancy'}")
    print("=" * 70)

    for i in range(total_blocks - 1):
        pair_sims = []
        for k in key_tensors:
            if k in blocks[i] and k in blocks[i + 1]:
                t1 = blocks[i][k]
                t2 = blocks[i + 1][k]
                # Compare raw byte representations directly
                raw1 = np.frombuffer(t1.data, dtype=np.uint8)
                raw2 = np.frombuffer(t2.data, dtype=np.uint8)
                if raw1.shape == raw2.shape:
                    pair_sims.append(cosine_sim(raw1, raw2))

        avg_sim = float(np.mean(pair_sims)) if pair_sims else 0.0
        # Angular distance: d = (1/pi) * arccos(sim)
        clamped_sim = max(-1.0, min(1.0, avg_sim))
        ang_dist = float(np.arccos(clamped_sim) / np.pi)
        redundancy = "HIGH" if avg_sim > 0.85 else ("MEDIUM" if avg_sim > 0.70 else "LOW")

        similarities.append({
            "block": i,
            "next_block": i + 1,
            "cosine_sim": avg_sim,
            "angular_distance": ang_dist,
            "redundancy": redundancy
        })

        print(f"Block {i:2d} -> {i+1:2d}    | {avg_sim:.4f}       | {ang_dist:.4f}                 | {redundancy}")

    print("=" * 70)

    # Sort by highest cosine similarity (most redundant)
    sorted_pairs = sorted(similarities, key=lambda x: x["cosine_sim"], reverse=True)

    print("\n🏆 Top 8 Most Redundant Consecutive Block Pairs:")
    for rank, p in enumerate(sorted_pairs[:8], 1):
        print(f"  {rank}. Block {p['block']} & {p['next_block']}: Sim = {p['cosine_sim']:.4f} (Angular Dist = {p['angular_distance']:.4f})")

    # Recommend a contiguous window of 4 middle layers to prune (layers 12 to 24)
    middle_candidates = [p for p in similarities if 10 <= p["block"] <= 26]
    best_candidate = max(middle_candidates, key=lambda x: x["cosine_sim"])
    rec_start = max(10, best_candidate["block"] - 1)
    rec_end = rec_start + 4

    print(f"\n💡 Pruning Recommendation:")
    print(f"   Target middle layer range: Blocks [{rec_start} to {rec_end - 1}] (4 blocks total)")
    print(f"   Reduces architecture from 35 layers -> 31 layers.")
    print(f"   Expected parameter / compute reduction: ~11.4%")


if __name__ == "__main__":
    analyze_model_layers()
