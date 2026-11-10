"""Small helpers shared by plan generators."""
from __future__ import annotations


def L(options, aid, default="your selection"):
    for o in options:
        if o["id"] == aid:
            return o["label"]
    return aid or default


def LM(options, ids, default="your selections"):
    if not ids:
        return default
    if isinstance(ids, str):
        ids = [ids]
    return ", ".join(L(options, i) for i in ids)


def opt(i, label, hint=None):
    d = {"id": i, "label": label}
    if hint:
        d["hint"] = hint
    return d


def env_names(slug):
    up = slug.upper()
    return {"secret_env": f"{up}_SECRET", "admin_env": f"{up}_ADMIN_PASSWORD", "db_env": f"{up}_DB"}
