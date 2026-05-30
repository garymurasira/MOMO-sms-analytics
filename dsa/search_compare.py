"""
dsa/search_compare.py
Compares linear search O(n) vs dictionary lookup O(1) on the transactions dataset.
"""

import json
import time
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "api", "data", "transactions.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.txt")
RUNS = 500


def load_transactions():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# O(n) — scans the list one item at a time until it finds the target ID
def linear_search(transactions, target_id):
    for tx in transactions:
        if tx["id"] == target_id:
            return tx
    return None


# O(1) — builds a dict once, then jumps directly to the key
def build_lookup(transactions):
    return {tx["id"]: tx for tx in transactions}


def benchmark(transactions, lookup_dict, target_id, runs=RUNS):
    # Benchmark linear search
    linear_times = []
    for _ in range(runs):
        start = time.perf_counter()
        linear_search(transactions, target_id)
        linear_times.append(time.perf_counter() - start)

    # Benchmark dictionary lookup
    dict_times = []
    for _ in range(runs):
        start = time.perf_counter()
        lookup_dict[target_id]
        dict_times.append(time.perf_counter() - start)

    return linear_times, dict_times


def format_results(transactions, linear_times, dict_times, target_id, runs):
    total_linear = sum(linear_times)
    total_dict = sum(dict_times)
    avg_linear = total_linear / runs
    avg_dict = total_dict / runs
    speedup = avg_linear / avg_dict if avg_dict > 0 else float("inf")

    lines = [
        "=" * 60,
        "  DSA BENCHMARK: Linear Search vs Dictionary Lookup",
        "=" * 60,
        f"  Dataset size : {len(transactions)} transactions",
        f"  Target ID    : {target_id}",
        f"  Runs         : {runs}",
        "-" * 60,
        f"  {'Method':<25} {'Avg Time (s)':<20} {'Total Time (s)'}",
        "-" * 60,
        f"  {'Linear Search O(n)':<25} {avg_linear:<20.8f} {total_linear:.6f}",
        f"  {'Dictionary Lookup O(1)':<25} {avg_dict:<20.8f} {total_dict:.6f}",
        "-" * 60,
        f"  Dictionary is {speedup:.1f}x faster than linear search",
        "=" * 60,
        "",
        "REFLECTION",
        "-" * 60,
        "Linear search scans every element in the list one by one",
        "until it finds a match. For a dataset of 1,691 records,",
        "this means up to 1,691 comparisons per lookup — O(n).",
        "",
        "Dictionary lookup uses a hash function to compute the",
        "exact memory location of the key directly. No scanning",
        "is needed — the lookup takes constant time regardless",
        "of dataset size — O(1).",
        "",
        "Why dict is faster:",
        "  - Hashing converts the key (id) to a memory address",
        "  - No iteration required — direct access",
        "  - Cost is paid once when building the dict, not per query",
        "",
        "Alternative data structures:",
        "  1. Binary Search (sorted list) — O(log n): sort IDs once,",
        "     then use binary search. Faster than linear, slower than dict.",
        "  2. BST (Binary Search Tree) — O(log n) average: good for",
        "     range queries but more complex to implement.",
        "  3. Hash Table with collision handling — same O(1) average",
        "     as Python dict but allows custom collision strategies",
        "     (chaining, open addressing) for specific use cases.",
        "=" * 60,
    ]
    return "\n".join(lines)


def main():
    print("Loading transactions...")
    transactions = load_transactions()
    lookup_dict = build_lookup(transactions)

    # Search for a transaction near the end of the list (worst case for linear)
    target_id = transactions[-1]["id"]

    print(f"Benchmarking {RUNS} runs each (target ID: {target_id})...")
    linear_times, dict_times = benchmark(transactions, lookup_dict, target_id, RUNS)

    output = format_results(transactions, linear_times, dict_times, target_id, RUNS)
    print(output)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nResults saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
