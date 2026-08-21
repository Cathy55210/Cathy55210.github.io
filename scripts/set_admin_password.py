#!/usr/bin/env python3
"""Rotation des accès du gestionnaire /admin/ (outil Digital Dreamsbox, usage local).

Regénère admin/auth.json : un coffre AES-256-GCM contenant le jeton GitHub,
déverrouillé dans le navigateur par identifiant + mot de passe
(clé dérivée PBKDF2-SHA256, 600 000 itérations).

Usage :
  python3 scripts/set_admin_password.py            # nouveau mot de passe généré
  python3 scripts/set_admin_password.py "MonMdp"   # mot de passe imposé

Le jeton est lu via `gh auth token -u Cathy55210` (jamais écrit en clair).
Après exécution : committer admin/auth.json, transmettre le mot de passe
à la cliente par un canal sûr. Ne JAMAIS committer le mot de passe.
"""
import base64
import hashlib
import json
import os
import secrets
import subprocess
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER = "cathy"
OWNER = "Cathy55210"
REPO = "Cathy55210.github.io"
ITERATIONS = 600_000


def main():
    token = subprocess.run(["gh", "auth", "token", "-u", OWNER],
                           capture_output=True, text=True).stdout.strip()
    if not token.startswith(("gho_", "ghp_", "github_pat_")):
        sys.exit(f"Jeton introuvable : connectez d'abord gh au compte {OWNER} (gh auth login).")

    if len(sys.argv) > 1:
        mdp = sys.argv[1]
    else:
        alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
        brut = "".join(secrets.choice(alphabet) for _ in range(16))
        mdp = "-".join(brut[i:i + 4] for i in range(0, 16, 4))

    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    cle = hashlib.pbkdf2_hmac("sha256", f"{USER}:{mdp}".encode(), salt, ITERATIONS, dklen=32)
    secret = json.dumps({"token": token, "owner": OWNER, "repo": REPO}).encode()
    chiffre = AESGCM(cle).encrypt(iv, secret, None)

    blob = {
        "v": 1, "kdf": "PBKDF2-SHA256", "iter": ITERATIONS, "cipher": "AES-256-GCM",
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "data": base64.b64encode(chiffre).decode(),
    }
    out = os.path.join(ROOT, "admin", "auth.json")
    with open(out, "w") as f:
        json.dump(blob, f, indent=2)

    # Auto-test symétrique avant de conclure
    verif = AESGCM(hashlib.pbkdf2_hmac("sha256", f"{USER}:{mdp}".encode(), salt, ITERATIONS, dklen=32))
    assert json.loads(verif.decrypt(iv, chiffre, None))["owner"] == OWNER

    print(f"admin/auth.json régénéré.\nIdentifiant : {USER}\nMot de passe : {mdp}")
    print("→ committer admin/auth.json, transmettre le mot de passe par canal sûr.")


if __name__ == "__main__":
    main()
