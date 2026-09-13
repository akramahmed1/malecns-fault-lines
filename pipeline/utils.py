"""Shared helpers for the pipeline: config, hashing, seeds, logging, JSON output."""
import hashlib
import json
import logging
import os
import platform

import numpy as np
import yaml


def load_config(path):
    """Load config.yaml."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def config_hash(cfg):
    """SHA256 over the canonical JSON form of the config. Logged every run."""
    canonical = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def make_rng(seed):
    """Seeded numpy generator. One stream per pipeline stage (see config seeds)."""
    return np.random.default_rng(int(seed))


def setup_logger(outdir, filename="run.log"):
    """Log to both run.log and stdout."""
    os.makedirs(outdir, exist_ok=True)
    logger = logging.getLogger("faultlines")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler(os.path.join(outdir, filename))
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def to_jsonable(obj):
    """Convert numpy types to plain Python for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(to_jsonable(obj), f, indent=2)


def sha256_file(path, chunksize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunksize), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions():
    versions = {"python": platform.python_version()}
    for mod in ["igraph", "numpy", "scipy", "pandas", "yaml"]:
        try:
            m = __import__(mod)
            versions[mod] = getattr(m, "__version__", "unknown")
        except ImportError:
            versions[mod] = "not-installed"
    return versions
