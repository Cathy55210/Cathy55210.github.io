#!/usr/bin/env python3
"""Générateur du site Nacréa by Cathy.

Lit scripts/config_nacrea.json + data/products.json et génère :
  - creation/<slug>.html  (une fiche par produit, même template pour toutes)
  - boutique.html         (grille filtrable par collection et occasion)
  - sitemap.xml

Lancé en local (python3 scripts/generate_site.py) ou par la GitHub Action
.github/workflows/rebuild.yml à chaque modification du catalogue.
Les fichiers générés ne doivent jamais être édités à la main.
"""
import html
import json
import os
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "scripts", "config_nacrea.json"), encoding="utf-8") as f:
    CFG = json.load(f)
with open(os.path.join(ROOT, "data", "products.json"), encoding="utf-8") as f:
    CATALOG = json.load(f)

PRODUITS = CATALOG["produits"]
DOMAINE = CFG["domaine"].rstrip("/")
MARQUE = CFG["marque"]

e = html.escape


def head(titre, description, path, og_image, og_type="website"):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
  <title>{e(titre)} · {e(MARQUE)}</title>
  <meta name="description" content="{e(description)}">
  <link rel="canonical" href="{DOMAINE}{path}">
  <meta property="og:title" content="{e(titre)}">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:image" content="{DOMAINE}/{og_image}">
  <meta property="og:url" content="{DOMAINE}{path}">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="{e(MARQUE)}">
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <link rel="icon" href="/assets/favicon-32-nc.png">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="preload" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Great+Vibes&family=Manrope:wght@400;500;600;700&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Great+Vibes&family=Manrope:wght@400;500;600;700&display=swap"></noscript>
  <link rel="stylesheet" href="/assets/styles.css">
  <script src="/assets/main.js" defer></script>"""


def header_nav():
    return f"""<header class="site-header">
  <nav class="nav-l" aria-label="Navigation principale">
    <a href="/boutique.html">Boutique</a>
    <a href="/boutique.html?collection=bouquets-satin">Bouquets</a>
    <a href="/boutique.html?collection=bougies-fondants">Bougies</a>
  </nav>
  <a href="/" class="logo-link" aria-label="{e(MARQUE)} — accueil">
    <img src="/assets/logo-header.webp" alt="{e(MARQUE)}" width="98" height="100">
  </a>
  <nav class="nav-r" aria-label="Navigation secondaire">
    <a href="/idees-cadeaux.html">Idées cadeaux</a>
    <a href="/sur-mesure.html">Sur-mesure</a>
  </nav>
</header>"""


def footer_html():
    reseaux = ""
    for cle, label in (("instagram", "Instagram"), ("tiktok", "TikTok"), ("facebook", "Facebook")):
        if CFG.get(cle):
            reseaux += f'<a href="{e(CFG[cle])}" target="_blank" rel="noopener">{label}</a>'
    return f"""<footer class="site-footer">
  <p class="footer-baseline">Des fleurs qui ne fanent jamais. Des attentions qui restent.</p>
  <nav aria-label="Liens de bas de page">
    <a href="/boutique.html">Boutique</a>
    <a href="/idees-cadeaux.html">Idées cadeaux</a>
    <a href="/sur-mesure.html">Sur-mesure</a>
    {reseaux}
  </nav>
  <p class="footer-lieu">{e(CFG["baseline"])} · {e(CFG["ville"])} ({e(CFG["departement"])})</p>
  <div class="footer-credit">
    <a href="https://digitaldreamsbox.com" target="_blank" rel="noopener">Site réalisé par <strong>Digital Dreamsbox</strong></a>
  </div>
</footer>"""


def footer():
    return "\n" + footer_html() + "\n</body>\n</html>"


def bouton_commande(p):
    prix = f"{p['prix']} €"
    if p["statut"] == "epuise":
        return '<span class="btn btn-off" aria-disabled="true">Épuisé pour le moment</span>'
    if p.get("stripe_url"):
        return (f'<a class="btn btn-primary" href="{e(p["stripe_url"])}" rel="noopener">'
                f'Commander · {prix}</a>')
    insta = e(CFG["instagram"])
    return (f'<a class="btn btn-primary" href="{insta}" target="_blank" rel="noopener">'
            f'Commander par message · {prix}</a>')


def schema_product(p):
    availability = {
        "disponible": "https://schema.org/InStock",
        "sur-commande": "https://schema.org/InStock",
        "epuise": "https://schema.org/OutOfStock",
    }[p["statut"]]
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["nom"],
        "description": p["accroche"],
        "image": [f"{DOMAINE}/{ph}" for ph in p["photos"]],
        "brand": {"@type": "Brand", "name": MARQUE},
        "offers": {
            "@type": "Offer",
            "url": f"{DOMAINE}/creation/{p['slug']}.html",
            "priceCurrency": "EUR",
            "price": str(p["prix"]),
            "availability": availability,
        },
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False) + "</script>")


def carte(p):
    statut = ""
    if p["statut"] == "epuise":
        statut = '<span class="badge badge-off">Épuisé</span>'
    elif p["statut"] == "sur-commande":
        statut = '<span class="badge">Sur commande</span>'
    try:
        recent = (date.today() - date.fromisoformat(p.get("ajoute_le", "2000-01-01"))).days <= 30
    except ValueError:
        recent = False
    if recent and p["statut"] != "epuise":
        statut += '<span class="badge badge-neuf">Nouveau</span>'
    occ = " ".join(p["occasions"])
    perso = '<p class="carte-perso">✦ Personnalisable</p>' if p.get("personnalisable") else ""
    cat = CFG["collections"].get(p["collection"], p["collection"])
    return f"""
    <a class="carte-produit" href="/creation/{p['slug']}.html"
       data-collection="{p['collection']}" data-occasions="{occ}">
      <div class="carte-img"><img src="/{e(p['photos'][0])}" alt="{e(p['nom'])}" loading="lazy" width="600" height="600">{statut}</div>
      <h3>{e(p['nom'])}</h3>
      <p class="carte-cat">{e(cat)}</p>
      <p class="carte-prix">{p['prix']} €</p>
      {perso}
    </a>"""


ENTRETIEN_FLORAL = ("Dépoussiérez délicatement de temps en temps, conservez la création à l'abri "
                    "de l'humidité et évitez une exposition prolongée au soleil direct : elle gardera "
                    "ses couleurs et son volume très longtemps.")
SECURITE_BOUGIE = ("Ne laissez jamais une bougie allumée sans surveillance. Placez-la sur une surface "
                   "stable et résistante à la chaleur, hors de portée des enfants et des animaux, "
                   "et ne la laissez pas brûler jusqu'au fond du contenant.")


def section_details(p):
    """Bloc « Dans les détails » : affiché uniquement si des données existent."""
    lignes = ""
    if p.get("dimensions"):
        lignes += f"<div><dt>Dimensions</dt><dd>{e(p['dimensions'])}</dd></div>"
    if p.get("matieres"):
        lignes += f"<div><dt>Matières</dt><dd>{e(p['matieres'])}</dd></div>"
    if not lignes:
        return ""
    return f"""
  <section class="produit-bloc">
    <h2>Dans les détails</h2>
    <dl class="details-dl">{lignes}</dl>
    <p class="note-variation">Chaque pièce étant faite main, les dimensions peuvent légèrement varier d'une création à l'autre.</p>
  </section>"""


def section_entretien(p):
    if p.get("entretien"):
        titre, texte = "Pour en profiter longtemps", p["entretien"]
    elif p["collection"] == "bougies-fondants":
        titre, texte = "Conseils d'utilisation", SECURITE_BOUGIE
    elif p["collection"] in ("bouquets-satin", "fleurs-chenille", "coffrets"):
        titre, texte = "Pour en profiter longtemps", ENTRETIEN_FLORAL
    else:
        return ""
    return f"""
  <section class="produit-bloc">
    <h2>{e(titre)}</h2>
    <p>{e(texte)}</p>
  </section>"""


def page_produit(p):
    autres = [q for q in PRODUITS if q["slug"] != p["slug"] and q["collection"] == p["collection"]]
    if len(autres) < 2:
        autres += [q for q in PRODUITS if q["slug"] != p["slug"] and q not in autres]
    cross = "".join(carte(q) for q in autres[:2])

    thumbs = ""
    if len(p["photos"]) > 1:
        imgs = "".join(
            f'<button class="thumb" data-src="/{e(ph)}"><img src="/{e(ph)}" alt="" loading="lazy" width="120" height="120"></button>'
            for ph in p["photos"])
        thumbs = f'<div class="galerie-thumbs">{imgs}</div>'

    perso = ""
    if p.get("personnalisable"):
        perso = ('<a class="btn btn-ghost" href="/sur-mesure.html">Personnaliser cette création</a>'
                 '<p class="perso-note">Couleurs, texte, occasion : cette création peut être adaptée '
                 'à la personne qui la recevra.</p>')

    paragraphs = "".join(f"<p>{e(par)}</p>" for par in p["description"].split("\n\n"))

    labels_occ = ", ".join(CFG["occasions"].get(o, o) for o in p["occasions"])
    cat_label = CFG["collections"].get(p["collection"], p["collection"])
    delai = ""
    if p.get("delai"):
        delai = f'<p class="delai-note">Fabrication : {e(p["delai"])}</p>'

    return f"""{head(p['nom'], p['accroche'], f"/creation/{p['slug']}.html", p['photos'][0], "product")}
  {schema_product(p)}
</head>
<body>
<!-- Page générée automatiquement par scripts/generate_site.py — ne pas éditer à la main -->
{header_nav()}
<main class="page-produit">
  <nav class="fil" aria-label="Fil d'Ariane"><a href="/">Accueil</a> › <a href="/boutique.html">Boutique</a> › <a href="/boutique.html?collection={p['collection']}">{e(cat_label)}</a> › <span>{e(p['nom'])}</span></nav>
  <div class="produit-grille">
    <section class="galerie">
      <img id="galerie-main" src="/{e(p['photos'][0])}" alt="{e(p['nom'])}" width="900" height="900">
      {thumbs}
    </section>
    <section class="infos">
      <p class="cat-label">{e(cat_label)}</p>
      <h1>{e(p['nom'])}</h1>
      <p class="prix">{p['prix']} €</p>
      <p class="accroche">{e(p['accroche'])}</p>
      <div class="achat-ctas">
        {bouton_commande(p)}
        {perso}
      </div>
      {delai}
      <ul class="reassurance">
        <li>Fait main à l'atelier, à {e(CFG['ville'])}</li>
        <li>Envoi soigné partout en France, ou remise en main propre</li>
        <li>Une création qui se garde, sans entretien</li>
      </ul>
    </section>
  </div>
  <section class="produit-description">
    <h2>Une attention faite pour rester</h2>
    {paragraphs}
    <p class="occasions-tags">Idéal pour : {e(labels_occ)}.</p>
  </section>
  {section_details(p)}
  {section_entretien(p)}
  <section class="produit-bloc atelier-fiche">
    <h2>Créée par Cathy</h2>
    <p>Chaque création Nacréa est préparée avec attention par Cathy, à Vigneulles-lès-Hattonchâtel, des premières associations de couleurs jusqu'aux derniers détails. Il n'en existe pas deux identiques.</p>
    <p><a href="/sur-mesure.html">Envie d'une version à vos couleurs ? Décrivez votre idée.</a></p>
  </section>
  <section class="cross-sell">
    <h2>Pour compléter votre attention</h2>
    <div class="grille-produits">{cross}</div>
  </section>
  <div class="sticky-buy">
    <span class="sb-prix">{p['prix']} €</span>
    {bouton_commande(p)}
  </div>
</main>
{footer()}""".replace("</body>\n</html>", """
<script>
document.querySelectorAll('.thumb').forEach(function(b){
  b.addEventListener('click', function(){
    document.getElementById('galerie-main').src = b.dataset.src;
  });
});
</script>
</body>
</html>""")


def page_boutique():
    chips_col = "".join(
        f'<button class="chip" data-filtre-collection="{k}">{e(v)}</button>'
        for k, v in CFG["collections"].items())
    chips_occ = "".join(
        f'<button class="chip chip-occ" data-filtre-occasion="{k}">{e(v)}</button>'
        for k, v in CFG["occasions"].items())
    cartes = "".join(carte(p) for p in PRODUITS)
    return f"""{head("La boutique", "Bouquets en satin, fleurs en fil chenille, bougies en cire de soja et coffrets cadeaux faits main. Des créations qui ne fanent pas.", "/boutique.html", "assets/logo-web.webp")}
</head>
<body>
<!-- Page générée automatiquement par scripts/generate_site.py — ne pas éditer à la main -->
{header_nav()}
<main class="page-boutique">
  <h1>La boutique</h1>
  <p class="intro">Chaque création est faite à la main par Cathy. Les couleurs peuvent être adaptées : <a href="/sur-mesure.html">imaginez la vôtre</a>.</p>
  <p class="filtre-label">L'occasion</p>
  <div class="filtres" role="group" aria-label="Filtrer par occasion">
    {chips_occ}
  </div>
  <p class="filtre-label">Le type de création</p>
  <div class="filtres filtres-occ" role="group" aria-label="Filtrer par type de création">
    <button class="chip chip-active" data-filtre-collection="">Tout</button>
    {chips_col}
  </div>
  <div class="grille-produits" id="grille">{cartes}</div>
  <p class="vide" id="vide" hidden>Aucune création ne correspond à ces filtres pour le moment. <a href="/sur-mesure.html">Demandez-la en sur-mesure !</a></p>
</main>
{footer()}""".replace("</body>\n</html>", """
<script>
(function(){
  var col = "", occ = "";
  var cartes = Array.from(document.querySelectorAll('#grille .carte-produit'));
  // Filtres pré-appliqués depuis l'URL (liens des sections Occasions / Collections de l'accueil)
  var params = new URLSearchParams(location.search);
  if (params.get('collection')) col = params.get('collection');
  if (params.get('occasion')) occ = params.get('occasion');
  function applique(){
    var visibles = 0;
    cartes.forEach(function(c){
      var okCol = !col || c.dataset.collection === col;
      var okOcc = !occ || (' '+c.dataset.occasions+' ').indexOf(' '+occ+' ') !== -1;
      var ok = okCol && okOcc;
      c.hidden = !ok;
      if (ok) visibles++;
    });
    document.getElementById('vide').hidden = visibles !== 0;
  }
  document.querySelectorAll('[data-filtre-collection]').forEach(function(b){
    b.addEventListener('click', function(){
      col = b.dataset.filtreCollection;
      document.querySelectorAll('[data-filtre-collection]').forEach(function(x){x.classList.remove('chip-active');});
      b.classList.add('chip-active');
      applique();
    });
  });
  document.querySelectorAll('[data-filtre-occasion]').forEach(function(b){
    b.addEventListener('click', function(){
      var v = b.dataset.filtreOccasion;
      occ = (occ === v) ? "" : v;
      document.querySelectorAll('[data-filtre-occasion]').forEach(function(x){x.classList.remove('chip-active');});
      if (occ) b.classList.add('chip-active');
      applique();
    });
  });
  if (col) {
    var bc = document.querySelector('[data-filtre-collection="'+col+'"]');
    if (bc) { document.querySelectorAll('[data-filtre-collection]').forEach(function(x){x.classList.remove('chip-active');}); bc.classList.add('chip-active'); }
  }
  if (occ) {
    var bo = document.querySelector('[data-filtre-occasion="'+occ+'"]');
    if (bo) bo.classList.add('chip-active');
  }
  if (col || occ) applique();
})();
</script>
</body>
</html>""")


def sitemap():
    urls = [f"{DOMAINE}/", f"{DOMAINE}/boutique.html", f"{DOMAINE}/sur-mesure.html",
            f"{DOMAINE}/idees-cadeaux.html"]
    urls += [f"{DOMAINE}/creation/{p['slug']}.html" for p in PRODUITS]
    entries = "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n'


def inject_manual_pages():
    """Injecte les blocs générés (nav, footer, coups de cœur) dans les pages
    écrites à la main, entre marqueurs GEN — idempotent."""
    import re
    coups = [p for p in PRODUITS if p.get("coup_de_coeur") and p["statut"] != "epuise"][:4]
    blocs = {
        "NAV": header_nav(),
        "FOOTER": footer_html(),
        "COUPS-DE-COEUR": '<div class="grille-produits">' + "".join(carte(p) for p in coups) + "</div>",
    }
    for page in ("index.html", "sur-mesure.html", "404.html", "idees-cadeaux.html", "merci-commande.html"):
        path = os.path.join(ROOT, page)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f_:
            html_page = f_.read()
        for nom, contenu in blocs.items():
            motif = re.compile(f"(<!-- GEN:{nom} -->).*?(<!-- /GEN:{nom} -->)", re.DOTALL)
            html_page = motif.sub(lambda m: m.group(1) + "\n" + contenu + "\n" + m.group(2), html_page)
        with open(path, "w", encoding="utf-8") as f_:
            f_.write(html_page)
        print(f"injecté : {page}")


def main():
    os.makedirs(os.path.join(ROOT, "creation"), exist_ok=True)

    # Purge des fiches obsolètes (produit supprimé du catalogue)
    slugs = {p["slug"] for p in PRODUITS}
    for f_ in os.listdir(os.path.join(ROOT, "creation")):
        if f_.endswith(".html") and f_[:-5] not in slugs:
            os.remove(os.path.join(ROOT, "creation", f_))
            print(f"supprimé : creation/{f_}")

    for p in PRODUITS:
        path = os.path.join(ROOT, "creation", f"{p['slug']}.html")
        with open(path, "w", encoding="utf-8") as f_:
            f_.write(page_produit(p))
        print(f"généré : creation/{p['slug']}.html")

    with open(os.path.join(ROOT, "boutique.html"), "w", encoding="utf-8") as f_:
        f_.write(page_boutique())
    print("généré : boutique.html")

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f_:
        f_.write(sitemap())
    print("généré : sitemap.xml")

    inject_manual_pages()

    print(f"\n{len(PRODUITS)} produit(s) · OK")


if __name__ == "__main__":
    sys.exit(main())
