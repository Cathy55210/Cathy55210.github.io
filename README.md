# Nacréa by Cathy — site & boutique

Site statique (GitHub Pages) avec catalogue géré depuis le navigateur.

## Comment ça marche

```
data/products.json          ← le catalogue (la seule source de vérité)
admin/index.html            ← le gestionnaire : Cathy ajoute/modifie ses créations
scripts/generate_site.py    ← génère creation/*.html, boutique.html, sitemap.xml
.github/workflows/rebuild.yml ← régénère automatiquement à chaque changement du catalogue
```

1. Cathy ouvre `nacreabycathy.fr/admin/`, remplit le formulaire (photos comprises,
   compressées automatiquement en WebP dans le navigateur).
2. Le gestionnaire pousse les photos et `data/products.json` dans ce dépôt via
   l'API GitHub (jeton d'accès limité à ce dépôt, stocké uniquement sur son appareil).
3. La GitHub Action régénère les fiches produit, la boutique et le sitemap.
4. GitHub Pages redéploie. En ligne en ~2 minutes.

## Commandes locales

```bash
python3 scripts/generate_site.py     # régénérer les pages
python3 -m http.server 4177          # prévisualiser sur http://localhost:4177
```

Ne jamais éditer à la main : `creation/*.html`, `boutique.html`, `sitemap.xml` (générés).
Config client (nom, domaine, collections, occasions) : `scripts/config_nacrea.json`.

## Mise en service du gestionnaire (à faire une fois, avec le compte de Cathy)

1. GitHub → Settings → Developer settings → Fine-grained personal access tokens →
   Generate new token : accès **à ce dépôt uniquement**, permission **Contents : Read and write**,
   expiration 1 an.
2. Ouvrir `/admin/` → ⚙︎ Connexion → renseigner compte, dépôt, jeton.
3. Le jeton reste dans le navigateur de Cathy (localStorage). Ne jamais le committer.

## À venir (chantiers suivants)

- Vraie page d'accueil (hero, collections, occasions, sur-mesure, storytelling)
- Pages sur-mesure, notre-univers, FAQ, contact, légales (mentions, CGV, confidentialité)
- Boutons Stripe Payment Links par produit (compte Stripe de Cathy, SIRET requis)
- GTM + bandeau cookies si analytics souhaité, pages villes SEO, blog
