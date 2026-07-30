#!/usr/bin/env python3
"""Reçoit le coffre déchiffré (JSON) sur stdin et dépose chaque fichier à sa place.
Appelé par `ingeny-creds pull` :  sops -d vault | INGENY_ROOT=.. HOMEDIR=.. python _deploy.py
Séparé dans un fichier pour éviter le conflit stdin (programme vs données)."""
import json, os, sys

v = json.load(sys.stdin)
root = os.environ["INGENY_ROOT"]
home = os.environ.get("HOMEDIR") or os.path.expanduser("~")

def put(base, rel, content):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:  # newline="" = préserve les LF (pas de CRLF Windows)
        f.write(content)
    try: os.chmod(p, 0o600)
    except OSError: pass
    print("  ->", os.path.join(base, rel))

for rel, c in v.get("repo", {}).items():
    put(root, rel, c)
for rel, c in v.get("home", {}).items():
    put(home, rel, c)
print("Coffre déposé.")
