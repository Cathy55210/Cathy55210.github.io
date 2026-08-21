# Nacréa by Cathy — site & boutique

Site statique (GitHub Pages) avec catalogue géré depuis le navigateur.

## Comment ça marche

```
data/products.json          ← le catalogue (la seule source de vérité)
admin/index.html            ← le gestionnaire : Cathy ajoute/modifie ses créations
scripts/generate_site.py    ← génère creation/*.html, boutique.html, sitemap.xml
.github/workflows/rebuild.yml ← régénère automatiquement à chaque changement du catalogue
```

1. Cathy ouvre `/admin/`, se connecte avec **identifiant + mot de passe**. Le mot de
   passe déverrouille dans le navigateur un jeton GitHub chiffré (`admin/auth.json`,
   AES-256-GCM, clé PBKDF2-SHA256 600 000 itérations) — elle ne voit jamais le jeton.
2. Elle remplit le formulaire (photos comprises, compressées automatiquement en WebP
   dans le navigateur) ; le gestionnaire pousse photos et `data/products.json` dans
   ce dépôt via l'API GitHub.
3. La GitHub Action régénère les fiches produit, la boutique et le sitemap.
4. GitHub Pages redéploie. En ligne en ~2 minutes.

## Commandes locales

```bash
python3 scripts/generate_site.py     # régénérer les pages
python3 -m http.server 4177          # prévisualiser sur http://localhost:4177
```

Ne jamais éditer à la main : `creation/*.html`, `boutique.html`, `sitemap.xml` (générés).
Config client (nom, domaine, collections, occasions) : `scripts/config_nacrea.json`.

## Gestion des accès du gestionnaire

- Connexion : identifiant + mot de passe (transmis à la cliente hors repo).
- Changer le mot de passe ou le jeton sous-jacent : `python3 scripts/set_admin_password.py`
  (nécessite `gh` connecté au compte propriétaire), puis committer `admin/auth.json`.
- `admin/auth.json` est un coffre chiffré : sa présence dans le repo public est voulue.
  Le mot de passe, lui, ne doit JAMAIS apparaître dans le repo.

## À venir (chantiers suivants)

- Vraie page d'accueil (hero, collections, occasions, sur-mesure, storytelling)
- Pages sur-mesure, notre-univers, FAQ, contact, légales (mentions, CGV, confidentialité)
- Boutons Stripe Payment Links par produit (compte Stripe de Cathy, SIRET requis)
- GTM + bandeau cookies si analytics souhaité, pages villes SEO, blog
