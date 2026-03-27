"""
ea/core.py

Pure algorithmic primitives for the peppered moth evolutionary algorithm.
No classes, no Streamlit imports — just functions.

Genome: 24-bit list of 0s and 1s.
  Bits  0–7  → Red channel   (0–255)
  Bits  8–15 → Green channel (0–255)
  Bits 16–23 → Blue channel  (0–255)

Bark color target: dark gray (40, 40, 40).
Moths that match this color survive best.
"""

import random
import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GENOME_LENGTH = 24
BARK_COLOR = (40, 40, 40)          # The tree bark moths must match
MAX_COLOR_DIST = math.sqrt(3 * 255 ** 2)   # Maximum possible RGB distance


# ---------------------------------------------------------------------------
# Genome encoding / decoding
# ---------------------------------------------------------------------------

def random_genome() -> list[int]:
    """Return a random 24-bit genome."""
    return [random.randint(0, 1) for _ in range(GENOME_LENGTH)]


def decode_genome(genome: list[int]) -> tuple[int, int, int]:
    """
    Convert a 24-bit genome to an RGB colour tuple.
    First 8 bits → R, next 8 → G, last 8 → B.
    """
    r = _bits_to_int(genome[0:8])
    g = _bits_to_int(genome[8:16])
    b = _bits_to_int(genome[16:24])
    return (r, g, b)


def _bits_to_int(bits: list[int]) -> int:
    """Convert a list of 8 bits (MSB first) to an integer 0–255."""
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


# ---------------------------------------------------------------------------
# Fitness
# ---------------------------------------------------------------------------

def fitness(genome: list[int]) -> float:
    """
    Fitness = how well the moth's colour matches the bark.
    Returns a value in [0, 1] where 1.0 is a perfect match.
    """
    color = decode_genome(genome)
    dist = color_distance(color, BARK_COLOR)
    return 1.0 - (dist / MAX_COLOR_DIST)


def color_distance(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    """Euclidean distance between two RGB colours."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def tournament_select(
    population: list[list[int]],
    fitnesses: list[float],
    k: int = 3,
) -> list[int]:
    """
    Tournament selection: pick k individuals at random, return the fittest.
    Does NOT modify the population.
    """
    indices = random.sample(range(len(population)), k)
    best_idx = max(indices, key=lambda i: fitnesses[i])
    return population[best_idx]


def random_select(
    population: list[list[int]],
    fitnesses: list[float],   # unused — kept for uniform call signature
) -> list[int]:
    """
    Random selection: pick any individual with equal probability.
    Used for the 'random mating' and 'equal reproduction' scenarios.
    """
    return random.choice(population)


# ---------------------------------------------------------------------------
# Crossover
# ---------------------------------------------------------------------------

def single_point_crossover(
    parent1: list[int],
    parent2: list[int],
    rate: float = 0.80,
) -> tuple[list[int], list[int]]:
    """
    Single-point crossover at a random position.
    If crossover does not occur (prob 1-rate), children are copies of parents.
    """
    if random.random() < rate:
        point = random.randint(1, GENOME_LENGTH - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    return list(parent1), list(parent2)


# ---------------------------------------------------------------------------
# Mutation
# ---------------------------------------------------------------------------

def mutate(genome: list[int], rate: float) -> list[int]:
    """
    Bit-flip mutation: each bit is flipped independently with probability rate.
    rate=0.0 → no mutation ever.
    """
    return [bit ^ 1 if random.random() < rate else bit for bit in genome]


# ---------------------------------------------------------------------------
# Diversity metric
# ---------------------------------------------------------------------------

def population_diversity(colors: list[tuple[int, int, int]]) -> float:
    """
    Average standard deviation of R, G, B values across the population.
    Higher = more colour variety in the population.
    """
    if len(colors) < 2:
        return 0.0
    r_vals = [c[0] for c in colors]
    g_vals = [c[1] for c in colors]
    b_vals = [c[2] for c in colors]
    return (_std(r_vals) + _std(g_vals) + _std(b_vals)) / 3.0


def _std(values: list[float]) -> float:
    """Population standard deviation."""
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return math.sqrt(variance)
