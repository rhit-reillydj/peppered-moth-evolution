"""
ea/population.py

Population class — manages one generation and steps forward to the next.
All behaviour is driven by the scenario config dict so the same class
handles all six experimental conditions without subclassing.

Config keys (all scenarios share this schema):
    population_size   : int   — number of individuals
    mutation_rate     : float — per-bit flip probability
    crossover_rate    : float — probability crossover occurs for a pair
    selection         : str   — "tournament" | "random"
    elitism           : int   — how many top individuals survive unchanged
    equal_reproduction: bool  — if True, ignore fitness for survival entirely
    migration         : bool  — whether new random moths fly in
    migration_interval: int   — every N generations, inject migrants
    migration_count   : int   — how many random moths to inject
    generations       : int   — total generations to run (used by runner)
"""

from dataclasses import dataclass, field
from ea.core import (
    random_genome,
    decode_genome,
    fitness,
    population_diversity,
    tournament_select,
    random_select,
    single_point_crossover,
    mutate,
)


# ---------------------------------------------------------------------------
# Data snapshot (one per generation, stored by the runner)
# ---------------------------------------------------------------------------

@dataclass
class GenerationSnapshot:
    generation: int
    max_fitness: float
    avg_fitness: float
    min_fitness: float
    diversity: float
    best_color: tuple[int, int, int]
    population_colors: list[tuple[int, int, int]]  # all individuals this gen


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------

class Population:
    def __init__(self, config: dict):
        self.config = config
        self.generation = 0

        # Initialise with random genomes
        size = config["population_size"]
        self.individuals: list[list[int]] = [random_genome() for _ in range(size)]

        # Compute initial state
        self._refresh()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh(self):
        """Recompute colours and fitnesses after any change to individuals."""
        self.colors: list[tuple[int, int, int]] = [
            decode_genome(g) for g in self.individuals
        ]
        self.fitnesses: list[float] = [fitness(g) for g in self.individuals]

    def _select_parent(self) -> list[int]:
        """Return one parent genome using the configured selection strategy."""
        if self.config["selection"] == "tournament":
            return tournament_select(self.individuals, self.fitnesses, k=3)
        else:
            return random_select(self.individuals, self.fitnesses)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def best(self) -> list[int]:
        """Genome of the most-fit individual in the current generation."""
        return self.individuals[self.fitnesses.index(max(self.fitnesses))]

    def snapshot(self) -> GenerationSnapshot:
        """Freeze the current generation state into a snapshot."""
        return GenerationSnapshot(
            generation=self.generation,
            max_fitness=max(self.fitnesses),
            avg_fitness=sum(self.fitnesses) / len(self.fitnesses),
            min_fitness=min(self.fitnesses),
            diversity=population_diversity(self.colors),
            best_color=decode_genome(self.best),
            population_colors=list(self.colors),
        )

    def step(self):
        """
        Advance one generation.

        Flow:
          1. Apply elitism (carry top N unchanged) — skipped for equal_reproduction
          2. Fill the rest of the new population via selection + crossover + mutation
          3. Optionally inject migrants
          4. Refresh colours and fitnesses
        """
        cfg = self.config
        size = cfg["population_size"]
        new_pop: list[list[int]] = []

        # --- Elitism ---------------------------------------------------
        elitism_count = 0 if cfg.get("equal_reproduction", False) else cfg["elitism"]
        if elitism_count > 0:
            sorted_by_fitness = sorted(
                range(size), key=lambda i: self.fitnesses[i], reverse=True
            )
            for idx in sorted_by_fitness[:elitism_count]:
                new_pop.append(list(self.individuals[idx]))

        # --- Generate offspring ----------------------------------------
        while len(new_pop) < size:
            parent1 = self._select_parent()
            parent2 = self._select_parent()
            child1, child2 = single_point_crossover(
                parent1, parent2, rate=cfg["crossover_rate"]
            )
            child1 = mutate(child1, cfg["mutation_rate"])
            child2 = mutate(child2, cfg["mutation_rate"])
            new_pop.append(child1)
            if len(new_pop) < size:
                new_pop.append(child2)

        self.individuals = new_pop[:size]
        self.generation += 1

        # --- Migration -------------------------------------------------
        if cfg.get("migration", False):
            interval = cfg["migration_interval"]
            count = cfg["migration_count"]
            if self.generation % interval == 0:
                self._inject_migrants(count)

        self._refresh()

    def _inject_migrants(self, count: int):
        """
        Replace the `count` least-fit individuals with random immigrants.
        Simulates gene flow from an outside population.
        """
        # Find the worst individuals (by current fitness, pre-migration refresh)
        sorted_worst = sorted(
            range(len(self.individuals)),
            key=lambda i: self.fitnesses[i],
        )
        for idx in sorted_worst[:count]:
            self.individuals[idx] = random_genome()
