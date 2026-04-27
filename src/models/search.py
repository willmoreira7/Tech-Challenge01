import random
from itertools import product


def random_search(config: dict, n_trials: int = 10, seed: int = 42) -> list[dict]:
    """Sample random hyperparameter combinations from the search space.

    Args:
        config: full config dict (must contain a "search_space" key).
        n_trials: how many random combinations to sample.
        seed: random seed for reproducibility.

    Returns:
        List of dicts, each with keys: learning_rate, batch_size,
        hidden_dims, dropout, epochs.
    """
    rng = random.Random(seed)
    space = config["search_space"]

    all_combos = list(product(
        space["learning_rate"],
        space["batch_size"],
        space["hidden_dims"],
        space["dropout"],
        space["epochs"],
    ))

    samples = rng.sample(all_combos, min(n_trials, len(all_combos)))

    return [
        {
            "learning_rate": lr,
            "batch_size": bs,
            "hidden_dims": hd,
            "dropout": dp,
            "epochs": ep,
        }
        for lr, bs, hd, dp, ep in samples
    ]
