# ingeny-secrets — coffre à secrets centralisé (SOPS + age)

**Un seul endroit** pour tous les secrets de la factory (clés GCloud, R2, mentor,
proxy labs…). On change un compte **ici**, toutes les machines re-tirent. Le repo
ne contient que du **chiffré** (`secrets.enc.json`) — illisible sans la clé age.

> ⚠️ **Repo PRIVÉ.** Même chiffré, il ne se rend jamais public.

---

## Comment ça marche (en 1 image)

```
secrets.enc.json  (chiffré, dans ce repo)
        │   ingeny-creds pull   (déchiffre avec TA clé age locale)
        ▼
 les vrais fichiers déposés à leur place :
   tools/illustrations/gcloud-sa*.json   (dans le dépôt ingeny)
   video-factory/pipeline/.env
   backend/.env
```

- **age** = le cadenas (clé privée locale = seul secret bootstrap, jamais dans git).
- **sops** = le coffre qui range et (dé)chiffre.

---

## Installer sur une NOUVELLE machine (5 min)

1. **Outils** :
   - Windows : `winget install FiloSottile.age` puis `winget install SecretsOPerationS.SOPS`
   - Linux (VM) : `apt-get install age` ; sops = binaire depuis github.com/getsops/sops/releases
2. **La clé age** (le seul secret à transporter, par USB / canal privé — **jamais par git**) :
   dépose-la dans `~/.config/sops/age/keys.txt`, puis `chmod 600`.
   *(Nouvelle machine sans clé ? Elle ne peut rien déchiffrer — c'est voulu.)*
3. **Cloner ce repo** puis récupérer les secrets :
   ```bash
   git clone git@github.com:sorotech2305/ingeny-secrets.git
   cd ingeny-secrets
   # racine du dépôt ingeny sur CETTE machine :
   INGENY_ROOT=/c/PosteDev/sources/ingeny ./ingeny-creds pull      # Windows
   # sur la VM : INGENY_ROOT=/opt/ingeny/repo ./ingeny-creds pull
   ```

C'est tout : les `.env` et clés `.json` sont déposés au bon endroit.

---

## Usage quotidien

| Commande | Effet |
|---|---|
| `./ingeny-creds pull` | git pull + déchiffre + dépose tous les fichiers |
| `./ingeny-creds edit` | ouvre le coffre en clair, rechiffre à la sauvegarde, **commit + push** |
| `./ingeny-creds list` | liste les chemins gérés (sans les valeurs) |

### Changer un compte (ex. crédits GCloud épuisés → nouvelle clé)
```bash
./ingeny-creds edit      # remplace la valeur de tools/illustrations/gcloud-sa.json, sauvegarde
# → committé + poussé automatiquement. Les autres machines : ./ingeny-creds pull
```
**Un seul endroit à changer, toute la flotte suit.**

---

## Contenu du coffre

- `tools/illustrations/gcloud-sa.json` → GCloud **503520** (compte app actuel)
- `tools/illustrations/gcloud-sa.WORKER-ingeny-503918.json` → GCloud **503918** (workers)
- `tools/illustrations/gcloud-sa.OLD-*.bak` → anciens comptes (501714, circular-ally)
- `video-factory/pipeline/.env` → R2, Kimi, Qwen, n8n
- `backend/.env` → mentor (LLM), Gemini, R2, SECRET_KEY

**À ajouter (séparément) :**
- **Jetons d'agents** Claude/Codex (`~/.claude/.credentials.json`, `~/.codex/auth.json`) —
  volatils, ajoutés à la main via `ingeny-creds edit` (clés `home`).
- **Proxy labs** (FAL_KEY, OPENROUTER_API_KEY, BRAVE_API_KEY, PROXY_API_KEY) —
  à rapatrier de la VM QA `/opt/jupyterhub/.env`.

---

## Sécurité

- **La clé age privée** (`~/.config/sops/age/keys.txt`) = le trésor. Jamais dans git,
  `chmod 600`. Qui l'a, ouvre le coffre.
- Le repo ne contient **que du chiffré**. En clair, jamais (`.gitignore` verrouille).
- **Perte / compromission d'une machine** : regénère une clé age, re-chiffre le coffre
  pour la nouvelle clé (`sops rotate` / `updatekeys`), et fais tourner les comptes exposés.
