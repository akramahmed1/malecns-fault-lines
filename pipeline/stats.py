"""Statistics: bootstrap confidence intervals, permutation tests,
effect sizes, and Benjamini-Hochberg FDR control."""
import numpy as np


def bootstrap_ci(values, n_boot=1000, alpha=0.05, seed=0, stat=np.mean):
    """Percentile bootstrap CI for a summary statistic (default: the mean)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(values, dtype=float)
    boots = [stat(rng.choice(x, size=len(x), replace=True)) for _ in range(n_boot)]
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return {
        "stat": float(stat(x)),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "n_boot": int(n_boot),
        "alpha": float(alpha),
    }


def permutation_test(observed, null_values, alternative="greater"):
    """One-sided permutation p-value with the standard +1 correction.

    alternative="greater": is the observed value unusually large vs the null?
    With no null values the test is infeasible and p_value is None.
    """
    null_values = np.asarray(null_values, dtype=float)
    if len(null_values) == 0:
        return {
            "observed": float(observed),
            "p_value": None,
            "n_null": 0,
            "null_mean": None,
            "null_sd": None,
            "note": "infeasible: no null values supplied",
        }
    if alternative == "greater":
        extreme = np.sum(null_values >= observed)
    elif alternative == "less":
        extreme = np.sum(null_values <= observed)
    else:
        raise ValueError("alternative must be greater or less")
    p = (extreme + 1) / (len(null_values) + 1)
    return {
        "observed": float(observed),
        "p_value": float(p),
        "n_null": int(len(null_values)),
        "null_mean": float(np.mean(null_values)),
        "null_sd": float(np.std(null_values, ddof=1)) if len(null_values) > 1 else 0.0,
    }


def cohens_d(x, y):
    """Standardized mean difference between samples x and y.

    A single observation (the deterministic targeted lesion) is standardized
    against the control sample SD. Empty samples give cohens_d None.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    nx, ny = len(x), len(y)
    if nx == 0 or ny == 0:
        return {"cohens_d": None, "mean_x": float(np.mean(x)) if nx else None,
                "mean_y": float(np.mean(y)) if ny else None,
                "note": "infeasible: empty sample"}
    vx = float(np.var(x, ddof=1)) if nx >= 2 else 0.0
    vy = float(np.var(y, ddof=1)) if ny >= 2 else 0.0
    denom = nx + ny - 2
    if denom > 0 and (nx >= 2 or ny >= 2):
        pooled = np.sqrt(((nx - 1) * vx + (ny - 1) * vy) / denom)
    else:
        pooled = 0.0
    d = (float(np.mean(x)) - float(np.mean(y))) / pooled if pooled > 0 else 0.0
    return {"cohens_d": float(d), "mean_x": float(np.mean(x)),
            "mean_y": float(np.mean(y))}


def benjamini_hochberg(p_values, alpha=0.05):
    """BH-FDR. Returns the reject mask and adjusted p-values in original order."""
    p = np.asarray(p_values, dtype=float)
    n = len(p)
    order = np.argsort(p, kind="stable")
    ranked = p[order]
    thresholds = (np.arange(1, n + 1) / n) * alpha
    below = ranked <= thresholds
    k_max = int(np.max(np.where(below)[0]) + 1) if np.any(below) else 0
    reject = np.zeros(n, dtype=bool)
    if k_max:
        reject[order[:k_max]] = True
    adj = np.minimum.accumulate((ranked * n / np.arange(1, n + 1))[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    p_adj = np.empty(n)
    p_adj[order] = adj
    return {"reject": reject.tolist(), "p_adjusted": p_adj.tolist(),
            "alpha": float(alpha), "n_tests": int(n),
            "n_rejected": int(np.sum(reject))}
