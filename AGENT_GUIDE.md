# AGENT_GUIDE — coffre à secrets ingeny (pour un agent qui prend le relais)

Tu opères une **factory multi-machines** dont les secrets (clés GCloud, R2, mentor,
proxy labs…) sont **centralisés et chiffrés** dans ce repo privé
**`sorotech2305/ingeny-secrets`**. Ce guide te donne tout : le modèle mental, les
commandes, l'installation sur une machine, et les pièges. Lis-le en entier une fois.

---

## 1. TL;DR (ce que tu dois retenir en 30 s)

- **Un seul endroit** contient tous les secrets : le fichier chiffré `secrets.enc.json`.
- Pour **récupérer** les secrets sur une machine : `./ingeny-creds pull`.
- Pour **changer/ajouter** un secret (rotation d'un compte, etc.) : `./ingeny-creds edit`
  → ça rechiffre, committe et pousse. Les autres machines refont `pull`.
- **On change à UN endroit, toute la flotte suit.**

---

## 2. Modèle mental

- **age** = le cadenas. Chaque machine a une **clé age privée** locale
  (`~/.config/sops/age/keys.txt`). C'est le **seul secret bootstrap** : qui l'a,
  ouvre le coffre ; qui ne l'a pas, ne lit rien (le repo n'est que du charabia).
- **SOPS** = le coffre qui range et (dé)chiffre. Il chiffre **les valeurs**, garde
  **les noms de fichiers lisibles**. Sur GitHub tu vois `ENC[...]`, jamais les clés.
- Le repo est **privé ET chiffré** (double protection).

```
secrets.enc.json  (dans ce repo, chiffré)
   │  ./ingeny-creds pull   (déchiffre avec TA clé age locale)
   ▼
 les vrais fichiers déposés à leur place dans le dépôt ingeny :
   tools/illustrations/gcloud-sa*.json
   video-factory/pipeline/.env
   backend/.env
```

---

## 3. Les commandes (`ingeny-creds`)

| Commande | Effet |
|---|---|
| `./ingeny-creds pull` | `git pull` + déchiffre + **dépose chaque fichier à son chemin** |
| `./ingeny-creds edit` | ouvre le coffre en clair (éditeur), rechiffre à la sauvegarde, **commit + push** |
| `./ingeny-creds list` | liste les chemins gérés (sans les valeurs) |

Deux variables d'environnement pilotent le comportement **par machine** :

- `INGENY_ROOT` : racine du dépôt ingeny où déposer les fichiers (varie par machine, voir §6).
- `SOPS_AGE_KEY_FILE` : chemin de la clé age privée (défaut `~/.config/sops/age/keys.txt`).

Exemple concret :
```bash
cd <clone de ingeny-secrets>
INGENY_ROOT=/opt/ingeny/repo ./ingeny-creds pull      # sur une VM
```

---

## 4. Ce qu'il y a dans le coffre (manifeste)

**Fichiers `repo`** (déposés sous `INGENY_ROOT/`) :
- `tools/illustrations/gcloud-sa.json` → GCloud **ingeny-503520** (compte APP actuel : voix Gemini-TTS + images Vertex + STT)
- `tools/illustrations/gcloud-sa.WORKER-ingeny-503918.json` → GCloud **ingeny-503918** (compte WORKERS : VM de rendu)
- `tools/illustrations/gcloud-sa.OLD-ingeny-501714.json.bak` → ancien (épuisé)
- `tools/illustrations/gcloud-sa.OLD-circular-ally-328013.json.bak` → ancien
- `video-factory/pipeline/.env` → R2 (bucket `ingeny-videos`), Kimi, Qwen, n8n
- `backend/.env` → mentor (LLM_API_KEY/BASE_URL), Gemini, R2, SECRET_KEY

**Pas encore dedans (à ajouter via `edit`)** :
- Jetons agents (`~/.claude/.credentials.json`, `~/.codex/auth.json`) — clés `home` (volatils).
- Proxy labs : `FAL_KEY`, `OPENROUTER_API_KEY`, `BRAVE_API_KEY`, `PROXY_API_KEY`
  (à rapatrier de la VM QA Contabo `/opt/jupyterhub/.env`).

---

## 5. Installer sur une NOUVELLE machine

1. **Outils** :
   - **Linux (Dell, VM, Asus)** :
     ```bash
     sudo apt-get update && sudo apt-get install -y age
     # sops (binaire officiel) :
     curl -L https://github.com/getsops/sops/releases/latest/download/sops-v3.13.0.linux.amd64 -o /tmp/sops
     sudo install -m 0755 /tmp/sops /usr/local/bin/sops
     sops --version && age --version
     ```
   - **Windows** : `winget install FiloSottile.age` puis `winget install SecretsOPerationS.SOPS`.
2. **Déposer la clé age** (le seul secret à transporter — **jamais par git**, via scp/USB) :
   ```bash
   mkdir -p ~/.config/sops/age && install -m 600 /chemin/keys.txt ~/.config/sops/age/keys.txt
   ```
   *(Sans cette clé, la machine ne peut rien déchiffrer — c'est voulu.)*
3. **Cloner + récupérer** :
   ```bash
   git clone git@github.com:sorotech2305/ingeny-secrets.git
   cd ingeny-secrets
   INGENY_ROOT=<racine ingeny sur cette machine> ./ingeny-creds pull
   ```

---

## 6. Registre des machines (INGENY_ROOT par machine)

| Machine | Accès | OS | `INGENY_ROOT` |
|---|---|---|---|
| Poste Windows (dev principal) | local | Windows | `/c/PosteDev/sources/ingeny` |
| Dell | `ssh dell` (ProxyJump contabo) | Ubuntu | `/home/soro/projects/llm-training/llm-engineer-academy-main` |
| VM `ingeny-poste-3` | `ssh worker@<IP>` (projet `ingeny-503918`) | Ubuntu 24.04 | `/opt/ingeny/repo` |
| VM `ingeny-poste-2` | via gcloud (projet `ingeny-503520`) | Ubuntu 24.04 | `/opt/ingeny/repo` |
| Asus | `ssh asus` (ou `ssh ai@192.168.1.202`) | Ubuntu | *(à confirmer — mettre le chemin du clone)* |

> ⚠️ **L'IP externe des VM change à chaque `start`** — relire au `describe`
> (cf. `video-factory/infra/RUNBOOK_POSTE_PRODUCTION.md`).

---

## 7. Rotation — changer un compte à UN seul endroit

Exemple : les crédits GCloud `ingeny-503520` sont épuisés, nouveau compte créé.
1. Remplace la nouvelle clé JSON dans le dépôt (elle écrase `tools/illustrations/gcloud-sa.json`).
2. Mets-la dans le coffre :
   ```bash
   ./ingeny-creds edit
   # remplace la valeur de "tools/illustrations/gcloud-sa.json" par le contenu du nouveau JSON, sauvegarde
   ```
   → committé + poussé automatiquement.
3. Sur **chaque autre machine** : `./ingeny-creds pull`. Terminé.

*(Procédure de création d'un nouveau compte GCloud :
`tools/illustrations/TUTO_NOUVEAU_COMPTE_GCLOUD.md` dans le dépôt ingeny.)*

---

## 8. Sécurité — à respecter absolument

- **La clé age privée** (`~/.config/sops/age/keys.txt`) = le trésor. `chmod 600`,
  **jamais** dans git, jamais affichée dans un log. Qui l'a, ouvre tout.
- Le repo ne contient **que du chiffré**. Le `.gitignore` + `.gitattributes`
  interdisent tout clair et forcent LF (pour que le script tourne sur Linux).
- **Compromission d'une machine** : régénère une clé age, re-chiffre le coffre pour
  la nouvelle clé (`sops updatekeys secrets.enc.json` après avoir changé `.sops.yaml`),
  et fais tourner les comptes exposés.

---

## 9. ⚠️ La seule contrainte (importante)

Un agent **dans une session Claude Code** ne peut **pas** lire son **propre jeton**
(`~/.claude/.credentials.json`) pour le mettre dans le coffre : la sécurité de Claude
Code bloque ce motif (indistinguable d'une exfiltration). Conséquences :
- **`pull` fonctionne** pour un agent (opération de tous les jours) — testé, exit 0.
- **`edit`/rotation des secrets d'infra** (GCloud, R2, mentor) fonctionne pour un agent.
- **Seul** l'ajout des jetons d'agents dans le coffre demande un process **non-Claude-Code**
  (ou une main humaine). Ces jetons se rafraîchissant sans cesse, on ne les fige de
  toute façon pas volontiers.

---

## 10. Dépannage

| Symptôme | Cause | Fix |
|---|---|---|
| `clé age absente: …/keys.txt` | pas de clé sur la machine | déposer la clé (§5.2) |
| `sops introuvable` | binaire hors PATH | installer sops (§5) ou l'appeler par chemin complet |
| `JSONDecodeError: line 1 column 1` au `pull` | (ancien bug corrigé) programme lu depuis stdin | déjà réglé — `pull` passe par `_deploy.py` |
| `pull` écrit mais accents bizarres dans un commentaire | le fichier source était déjà en mojibake | cosmétique ; les **valeurs** (ASCII) sont intactes |
| `Repository not found` au `pull`/`push` | accès SSH GitHub manquant | vérifier `ssh -T git@github.com` → `Hi sorotech2305!` |

---

## 11. Fichiers de ce repo

- `secrets.enc.json` — le coffre chiffré (seul fichier de secrets, committable).
- `ingeny-creds` — l'outil (`pull`/`edit`/`list`).
- `_deploy.py` — dépose les fichiers déchiffrés (appelé par `pull`).
- `.sops.yaml` — dit à SOPS pour quelle clé age chiffrer.
- `.gitignore` / `.gitattributes` — verrouillent le clair, forcent LF.
- `README.md` — version courte (onboarding). Ce fichier-ci = version complète pour agent.
