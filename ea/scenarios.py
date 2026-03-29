"""
ea/scenarios.py

Seven scenario definitions and the run_scenario() orchestrator.

Each scenario is a dict with:
  - display metadata (name, hw_condition, description, biology_explanation)
  - config  (passed directly to Population)

run_scenario(key) returns a ScenarioResult dataclass ready to be pickled
and loaded by the Streamlit app.
"""

from dataclasses import dataclass, field
from ea.population import Population, GenerationSnapshot
from ea.core import decode_genome

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    key: str
    name: str
    hw_condition: str
    description: str
    biology_explanation: str
    best_final_color: tuple[int, int, int]
    best_final_fitness: float
    generations: list[GenerationSnapshot]
    config: dict


# ---------------------------------------------------------------------------
# Base config (Normal Evolution)
# ---------------------------------------------------------------------------

_BASE_CONFIG = {
    "population_size":    100,
    "mutation_rate":      0.02,     # 2 % per bit
    "crossover_rate":     0.80,
    "selection":          "tournament",
    "elitism":            2,
    "equal_reproduction": False,
    "migration":          True,
    "migration_interval": 25,
    "migration_count":    5,
    "generations":        150,
}


def _cfg(**overrides) -> dict:
    """Return a copy of the base config with overrides applied."""
    cfg = dict(_BASE_CONFIG)
    cfg.update(overrides)
    return cfg


# ---------------------------------------------------------------------------
# Scenario registry
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {

    "normal": {
        "name": "Normal Evolution",
        "hw_condition": "None — all evolutionary forces active",
        "description": (
            "The full evolutionary engine is running. "
            "Moths mutate, only the best-camouflaged breed, "
            "and new moths occasionally migrate in."
        ),
        "biology_explanation": (
            "This is what happens in nature when none of the Hardy-Weinberg "
            "conditions are met. Mutation continuously introduces new colour "
            "variations. Natural selection ruthlessly removes moths that don't "
            "match the bark — predatory birds spot and eat them first. "
            "Occasional migrants bring fresh alleles from other populations. "
            "The result: the population rapidly converges toward the dark "
            "bark colour as evolution drives the moths toward better "
            "camouflage over just a few generations."
        ),
        "config": _cfg(),
    },

    "no_mutation": {
        "name": "No Mutation",
        "hw_condition": "No mutation",
        "description": (
            "Mutation is completely disabled. "
            "No new genetic information can arise — "
            "the population can only work with what it started with."
        ),
        "biology_explanation": (
            "Mutation is evolution's only source of brand-new genetic "
            "information. Without it, no new alleles can appear in the "
            "population — the gene pool is locked to whatever variation "
            "existed at the very start. Selection can still sort existing "
            "variants, so the population improves somewhat early on, but "
            "it quickly runs out of raw material and stalls. If the "
            "initial population happened to lack the right alleles for "
            "dark colouration, the moths are permanently stuck. This "
            "illustrates why mutation is considered a primary driver of "
            "long-term evolutionary change."
        ),
        "config": _cfg(mutation_rate=0.0),
    },

    "small_pool": {
        "name": "Small Gene Pool",
        "hw_condition": "Infinite population size (violated — population is tiny)",
        "description": (
            "The population is shrunk to just 12 individuals. "
            "Random chance now dominates over selection — "
            "this is genetic drift in action."
        ),
        "biology_explanation": (
            "Hardy-Weinberg assumes an infinitely large population where "
            "random sampling errors average out. In a tiny population of "
            "only 12 moths, chance events dominate. A dark moth might be "
            "eaten by a raccoon before it breeds — not because of its "
            "colour, but just bad luck. This random loss of alleles is "
            "called genetic drift. The population may evolve in the "
            "completely wrong direction, or fixate on a colour by pure "
            "chance. The fitness curve looks erratic and unpredictable "
            "compared to the smooth convergence of normal evolution. "
            "This is why small, isolated populations (like endangered "
            "species) are so vulnerable — drift can overwhelm selection."
        ),
        "config": _cfg(population_size=12, elitism=1, migration_count=1),
    },

    "random_mating": {
        "name": "Random Mating",
        "hw_condition": "Random mating (no fitness-based mate preference)",
        "description": (
            "Breeding partners are chosen at random regardless of fitness. "
            "Any moth can mate with any other moth equally. "
            "Offspring still mutate and compete to survive."
        ),
        "biology_explanation": (
            "Hardy-Weinberg assumes completely random mating — no individual "
            "is more likely to find a mate because of its traits. Here, a "
            "well-camouflaged moth has no advantage in attracting a partner; "
            "it mates randomly just like a poorly-camouflaged one. This "
            "removes sexual selection from the equation. Some evolution "
            "still occurs because offspring still face predation (natural "
            "selection at survival stage), but the rate is slower. Without "
            "preferential mating, high-fitness alleles spread through the "
            "population less efficiently. In nature, non-random mating "
            "(like assortative mating or mate-choice) is a powerful "
            "accelerant of evolution."
        ),
        "config": _cfg(selection="random", elitism=0),
    },

    "no_migration": {
        "name": "No Migration",
        "hw_condition": "No gene flow (no migration in or out)",
        "description": (
            "The population is completely isolated — no new moths ever "
            "fly in from outside. The gene pool is closed."
        ),
        "biology_explanation": (
            "Gene flow (migration) is one of evolution's most important "
            "forces — it connects populations and shuffles alleles between "
            "them. In the Normal Evolution run, every 25 generations a "
            "small number of random moths migrate in, bringing fresh colour "
            "alleles the local population might lack. Without migration, "
            "the population must rely entirely on its own mutation to "
            "generate variation. If it gets trapped near a local optimum "
            "early on, no outside rescue arrives. Isolated populations "
            "also tend to lose alleles permanently over time (genetic "
            "erosion). This scenario mirrors what happens to island "
            "species or populations separated by habitat destruction."
        ),
        "config": _cfg(migration=False),
    },

    "equal_reproduction": {
        "name": "Equal Reproduction",
        "hw_condition": "No natural selection (all individuals reproduce equally)",
        "description": (
            "Every moth reproduces with exactly the same probability "
            "regardless of how well-camouflaged it is. "
            "There is no survival advantage to matching the bark."
        ),
        "biology_explanation": (
            "Natural selection is the engine that converts random variation "
            "into directional evolutionary change. Here, we remove it "
            "entirely: poorly-camouflaged moths and perfectly-camouflaged "
            "moths are equally likely to pass on their genes. Without "
            "selection pressure, the population wanders aimlessly — allele "
            "frequencies change only by chance (drift), not by any "
            "consistent push toward better camouflage. The fitness curve "
            "stays flat and the population looks like a random rainbow at "
            "the end, just as it did at the beginning. This powerfully "
            "demonstrates that variation alone is not enough for evolution "
            "— you also need differential survival and reproduction."
        ),
        "config": _cfg(selection="random", elitism=0, equal_reproduction=True),
    },

    "all_conditions": {
        "name": "All HW Conditions Met",
        "hw_condition": "All five conditions enforced simultaneously",
        "description": (
            "Every Hardy-Weinberg condition is enforced at once: "
            "no mutation, no selection, random mating, no migration, "
            "and a small isolated population. "
            "This is the closest we can get to true HW equilibrium."
        ),
        "biology_explanation": (
            "This scenario enforces all five Hardy-Weinberg conditions "
            "simultaneously, stripping away every known driver of "
            "evolutionary change at once. "
            "<br><br>"
            "There is <strong>no mutation</strong> — no new alleles can appear. "
            "Mating is <strong>completely random</strong> — camouflage gives "
            "no advantage in finding a mate. "
            "There is <strong>no natural selection</strong> — poorly-camouflaged "
            "moths survive and reproduce just as well as hidden ones. "
            "The population is <strong>small and isolated</strong> — "
            "no outside moths ever arrive with fresh alleles. "
            "<br><br>"
            "The result is essentially <em>no directional evolution</em>. "
            "The population wanders aimlessly through colour space, pushed "
            "only by random genetic drift in a tiny gene pool. "
            "Final colour is essentially a matter of chance — the population "
            "is no more camouflaged after 150 generations than it was on "
            "day one. Compare this to Normal Evolution to see just how much "
            "work each of those five forces does when they are all active together."
        ),
        "config": _cfg(
            mutation_rate=0.0,         # No mutation
            selection="random",        # Random mating — no fitness preference
            elitism=0,                 # No reproductive advantage for fit individuals
            equal_reproduction=True,   # No natural selection
            migration=False,           # No gene flow
            population_size=12,        # Small gene pool — maximises drift
        ),
    },
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_scenario(key: str) -> ScenarioResult:
    """
    Run one scenario from start to finish and return a ScenarioResult.
    Records a GenerationSnapshot at every generation (including gen 0).
    """
    meta = SCENARIOS[key]
    cfg = meta["config"]

    pop = Population(cfg)
    snapshots: list[GenerationSnapshot] = []

    # Record the initial (random) state
    snapshots.append(pop.snapshot())

    for _ in range(cfg["generations"]):
        pop.step()
        snapshots.append(pop.snapshot())

    best_genome = pop.best
    best_color = decode_genome(best_genome)
    best_fitness = max(pop.fitnesses)

    return ScenarioResult(
        key=key,
        name=meta["name"],
        hw_condition=meta["hw_condition"],
        description=meta["description"],
        biology_explanation=meta["biology_explanation"],
        best_final_color=best_color,
        best_final_fitness=best_fitness,
        generations=snapshots,
        config=cfg,
    )
