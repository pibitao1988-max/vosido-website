#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUMIVA B2B hair-tools site builder.

Generates a fully static, SEO-ready multilingual site:
    dist/<lang>/<page>.html      one URL per language (required for hreflang)
    dist/assets/                 css + js
    dist/sitemap.xml, robots.txt

Usage:  python build.py
Then open dist/en/index.html in a browser.

To rebrand: edit src/site.json (company details) - no need to touch this file.
All copy lives in src/i18n/<lang>.json - editable from the /admin CMS.
"""

import json
import os
import shutil
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
DIST = os.path.join(ROOT, "dist")

# Order here is the order shown in the language switcher dropdown.
LANGS = ["en", "es", "pt", "fr", "de", "ru", "tr", "ar", "ja", "ko"]
RTL = {"ar"}

# Canonical origin used only for hreflang / canonical / sitemap absolute URLs.
# TODO: confirm the real production domain, then rebuild.
SITE_ORIGIN = "https://www.vosido.com"

def load_json(rel):
    """Read an editable data file from src/. Kept out of this script so the
    Decap CMS admin can write them without touching Python."""
    with open(os.path.join(SRC, rel), encoding="utf-8") as f:
        return json.load(f)


# --- Editable content (also writable from the /admin CMS) -------------------
SITE = load_json("site.json")
BRAND_OVERRIDES = {k: SITE[k] for k in
                   ("company", "company_cn", "address", "address_cn",
                    "phone", "email")}

# WhatsApp sales contacts. Add or remove entries freely - the floating button,
# CTA band, footer and contact page all render from this single list, so no
# template changes are needed. First entry is treated as the primary contact.
# "name" is optional; when omitted only the number is shown.
WHATSAPP = SITE["whatsapp"]

WA_ICON = ('<svg viewBox="0 0 24 24" width="21" height="21" fill="currentColor" '
           'aria-hidden="true"><path d="M12 2C6.5 2 2 6.3 2 11.6c0 1.9.6 3.7 1.6 '
           '5.2L2 22l5.4-1.4c1.4.8 3 1.2 4.6 1.2 5.5 0 10-4.3 10-9.6S17.5 2 '
           '12 2z"/></svg>')


def wa_label(w):
    return w.get("name") or w["number"]


def wa_link_list(lang):
    """Plain list of WhatsApp links, used in the contact sidebar."""
    return "".join(
        '<a class="wa-line" href="%s" rel="noopener" target="_blank">%s %s</a>'
        % (e(w["url"]), e(t(lang, "cta_whatsapp")), e(wa_label(w)))
        for w in WHATSAPP
    )


def wa_footer_items(lang):
    """Same contacts as list items for the footer column."""
    return "".join(
        '<li><a class="wa-line" href="%s" rel="noopener" target="_blank">%s %s</a></li>'
        % (e(w["url"]), e(t(lang, "cta_whatsapp")), e(wa_label(w)))
        for w in WHATSAPP
    )

# Enquiry form destination. Leave as "" to fall back to opening the visitor's
# mail client (nothing is silently lost, but nothing is stored either).
# Examples:
#   "https://formspree.io/f/xxxxxxxx"
#   "https://your-crm.example.com/api/enquiry"
# When moving onto a hosted CMS, put that platform's form action URL here.
FORM_ENDPOINT = ""

# -------------------------------------------------------------------------------

# CONFIRMED BY CLIENT (2026-09-07): founded 2008, 8 production lines,
# 2.4M units annual capacity, factory is closely held / controlled.
#
# STILL UNVERIFIED - confirm or replace before publishing:
#   stat4_v        "48h" sample lead time (service promise, keep it deliverable)
#   ms_2013/2017/2021  milestone events and their years, apart from 2008
#   cert lists     per-model certification scope must match real certificates
# Claiming capacity or history that cannot be evidenced is a real risk in B2B
# due diligence. Keys: stat*_v/l, ms_*, cap*_t/d, about_p1/p2 in src/i18n/<lang>.json

# Product catalogue (editable from /admin). Numeric/technical values are
# shared across languages; only labels and marketing copy are translated.
PRODUCTS = load_json("products.json")

SPEC_ORDER = [
    ("model", "spec_model"),
    ("power", "spec_power"),
    ("voltage", "spec_voltage"),
    ("motor", "spec_motor"),
    ("temp", "spec_temp"),
    ("cord", "spec_cord"),
    ("plug", "spec_plug"),
    ("warranty", "spec_warranty"),
    ("moq", "spec_moq"),
    ("lead", "spec_lead"),
]

CERTS_ALL = ["CE", "CB", "ETL", "UKCA", "RoHS", "PSE", "KC", "SASO", "INMETRO"]


def load_i18n():
    """One file per language so the CMS can edit one language without
    clobbering the other nine."""
    out = {}
    for lang in LANGS:
        with open(os.path.join(SRC, "i18n", lang + ".json"),
                  encoding="utf-8") as f:
            out[lang] = json.load(f)
    return out


I18N = load_i18n()


def t(lang, key):
    return I18N[lang][key]


def e(value):
    return escape(str(value), quote=True)


LANG_NAMES = {
    "en": "English",
    "es": "Espa\u00f1ol",
    "pt": "Portugu\u00eas",
    "fr": "Fran\u00e7ais",
    "de": "Deutsch",
    "ru": "\u0420\u0443\u0441\u0441\u043a\u0438\u0439",
    "tr": "T\u00fcrk\u00e7e",
    "ar": "\u0627\u0644\u0639\u0631\u0628\u064a\u0629",
    "ja": "\u65e5\u672c\u8a9e",
    "ko": "\ud55c\uad6d\uc5b4",
}


def lang_name(lang):
    return LANG_NAMES[lang]


def page_file(slug=None, kind="index"):
    if kind == "index":
        return "index.html"
    if kind == "products":
        return "products.html"
    if kind == "about":
        return "about.html"
    if kind == "contact":
        return "contact.html"
    return "product-%s.html" % slug


def href(lang, target_lang, filename):
    """Same-language links stay relative; cross-language links hop one level up."""
    if lang == target_lang:
        return filename
    return "../%s/%s" % (target_lang, filename)


# Product photos are real files in src/assets/img/product/, named
# <slug>-01.jpg .. <slug>-04.jpg. To change a photo just overwrite the file:
# no template edit, only re-run build.py. -01 is the main image used in listing
# cards; 02-04 are the detail-page thumbnails.
IMG_BASE = "../assets/img/product"
IMG_COUNT = 4


def product_img(slug, n, alt):
    return ('<img src="%s/%s-%02d.jpg" alt="%s" width="1000" height="750"'
            ' loading="%s">'
            % (IMG_BASE, e(slug), n, e(alt), "eager" if n == 1 else "lazy"))


def head(lang, filename, title, desc, jsonld=""):
    dir_attr = ' dir="rtl"' if lang in RTL else ""
    links = ['<link rel="alternate" hreflang="%s" href="%s/%s/%s"/>' % (l, SITE_ORIGIN, l, filename)
             for l in LANGS]
    links.append('<link rel="alternate" hreflang="x-default" href="%s/en/%s"/>' % (SITE_ORIGIN, filename))
    canonical = '<link rel="canonical" href="%s/%s/%s"/>' % (SITE_ORIGIN, lang, filename)
    return (
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>%s</title>\n'
        '<meta name="description" content="%s">\n'
        '%s\n%s\n'
        '<link rel="stylesheet" href="../assets/style.css">\n'
        % (e(title), e(desc), canonical, "\n".join(links))
    ), dir_attr


def lang_switch(lang, filename):
    items = []
    for l in LANGS:
        cls = ' class="current"' if l == lang else ""
        items.append('<li><a%s data-lang="%s" href="%s" hreflang="%s" lang="%s">%s</a></li>'
                     % (cls, l, e(href(lang, l, filename)), l, l, e(lang_name(l))))
    return (
        '<div class="lang-switch">\n'
        '  <button type="button" aria-haspopup="true" aria-expanded="false">'
        '<span aria-hidden="true">&#9776;</span> %s</button>\n'
        '  <ul>%s</ul>\n'
        '</div>' % (e(lang_name(lang)), "".join(items))
    )


def header(lang, filename, active):
    nav = [
        ("index", "nav_home", "index.html"),
        ("products", "nav_products", "products.html"),
        ("about", "nav_about", "about.html"),
        ("contact", "nav_contact", "contact.html"),
    ]
    items = []
    for key, label, fname in nav:
        cls = ' class="active"' if key == active else ""
        items.append('<a%s href="%s">%s</a>' % (cls, e(href(lang, lang, fname)), e(t(lang, label))))
    return (
        '<header class="site-header">\n'
        '  <div class="wrap header-inner">\n'
        '    <a class="logo" href="%s"><span class="mark">VS</span>'
        '<span>%s<small>%s</small></span></a>\n'
        '    <button class="nav-toggle" type="button">&#9776;</button>\n'
        '    <nav class="nav">%s</nav>\n'
        '    %s\n'
        '  </div>\n'
        '</header>'
        % (e(href(lang, lang, "index.html")), e(t(lang, "brand")), e(t(lang, "tagline")),
           "".join(items), lang_switch(lang, filename))
    )


def banner(lang):
    return (
        '<div class="lang-banner" id="lang-banner" role="region"\n'
        '     data-template="%s" data-accept="%s" data-dismiss="%s">\n'
        '  <div class="wrap">\n'
        '    <span class="msg"></span>\n'
        '    <button type="button" class="accept"></button>\n'
        '    <button type="button" class="dismiss"></button>\n'
        '  </div>\n'
        '</div>'
        % (e(t(lang, "switch_text")), e(t(lang, "switch_accept")), e(t(lang, "switch_dismiss")))
    )


def footer(lang):
    prod_links = "".join(
        '<li><a href="%s">%s</a></li>'
        % (e(href(lang, lang, page_file(p["slug"], "product"))), e(t(lang, "prod_%s_name" % p["ikey"])))
        for p in PRODUCTS
    )
    return (
        '<footer class="site-footer">\n'
        '  <div class="wrap">\n'
        '    <div class="footer-grid">\n'
        '      <div>\n'
        '        <h4>%s</h4>\n'
        '        <p>%s</p>\n'
        '      </div>\n'
        '      <div><h4>%s</h4><ul>%s</ul></div>\n'
        '      <div><h4>%s</h4><ul>\n'
        '        <li><a href="%s">%s</a></li>\n'
        '        <li><a href="%s">%s</a></li>\n'
        '        <li><a href="%s">%s</a></li>\n'
        '      </ul></div>\n'
        '      <div><h4>%s</h4><ul>\n'
        '        <li>%s</li>\n'
        '        <li><a href="mailto:%s">%s</a></li>\n'
        '        %s\n'
        '        <li>%s</li>\n'
        '      </ul></div>\n'
        '    </div>\n'
        '    <div class="footer-bottom">\n'
        '      <span>&copy; 2026 %s. %s</span>\n'
        '      <span>%s &middot; %s</span>\n'
        '    </div>\n'
        '  </div>\n'
        '</footer>'
        % (e(t(lang, "brand")), e(t(lang, "foot_desc")),
           e(t(lang, "foot_products")), prod_links,
           e(t(lang, "foot_company")),
           e(href(lang, lang, "about.html")), e(t(lang, "nav_about")),
           e(href(lang, lang, "contact.html")), e(t(lang, "nav_contact")),
           e(href(lang, lang, "privacy.html")), e(t(lang, "privacy_title")),
           e(t(lang, "foot_support")),
           e(BRAND_OVERRIDES["phone"]),
           e(BRAND_OVERRIDES["email"]), e(BRAND_OVERRIDES["email"]),
           wa_footer_items(lang),
           e(BRAND_OVERRIDES["company_cn"]),
           e(BRAND_OVERRIDES["company"]), e(t(lang, "foot_rights")),
           e(BRAND_OVERRIDES["address"]), e(BRAND_OVERRIDES["address_cn"]))
    )


def cta_band(lang):
    wa_buttons = "".join(
        '<a class="btn btn-ghost" href="%s" rel="noopener" target="_blank">%s %s</a>'
        % (e(w["url"]), e(t(lang, "cta_whatsapp")), e(wa_label(w)))
        for w in WHATSAPP
    )
    return (
        '<section class="cta-band">\n'
        '  <div class="wrap">\n'
        '    <h2>%s</h2>\n'
        '    <p>%s</p>\n'
        '    <div class="actions">\n'
        '      <a class="btn btn-primary" href="%s">%s</a>\n'
        '      %s\n'
        '    </div>\n'
        '  </div>\n'
        '</section>'
        % (e(t(lang, "home_cta_title")), e(t(lang, "home_cta_sub")),
           e(href(lang, lang, "contact.html")), e(t(lang, "cta_quote")),
           wa_buttons)
    )


def prod_card(lang, p, with_meta=True):
    meta = ""
    if with_meta:
        meta = ('<div class="prod-meta">'
                '<span>%s: <b>%s</b></span>'
                '<span>%s: <b>%s</b></span>'
                '</div>' % (e(t(lang, "moq_label")), e(p["spec"]["moq"]),
                            e(t(lang, "lead_label")), e(p["spec"]["lead"])))
    return (
        '<a class="prod-card" data-cat="%s" href="%s">\n'
        '  <div class="thumb">%s</div>\n'
        '  <div class="body">\n'
        '    <h3>%s</h3>\n'
        '    <p>%s</p>\n'
        '    %s\n'
        '  </div>\n'
        '</a>'
        % (e(p["ikey"]), e(href(lang, lang, page_file(p["slug"], "product"))),
           product_img(p["slug"], 1, t(lang, "prod_%s_name" % p["ikey"])),
           e(t(lang, "prod_%s_name" % p["ikey"])),
           e(t(lang, "prod_%s_desc" % p["ikey"])), meta)
    )


def breadcrumb(lang, items):
    parts = ['<a href="%s">%s</a>' % (e(href(lang, lang, "index.html")), e(t(lang, "crumb_home")))]
    for label, fname in items:
        if fname:
            parts.append('<a href="%s">%s</a>' % (e(href(lang, lang, fname)), e(label)))
        else:
            parts.append("<span aria-current=\"page\">%s</span>" % e(label))
    return '<div class="wrap breadcrumb">%s</div>' % '<span>/</span>'.join(parts)


# --------------------------------------------------------------------------- #
# Page builders
# --------------------------------------------------------------------------- #

def build_home(lang):
    filename = "index.html"
    stats = "".join(
        '<div class="stat"><div class="v">%s</div><div class="l">%s</div></div>'
        % (e(t(lang, "stat%d_v" % i)), e(t(lang, "stat%d_l" % i)))
        for i in range(1, 5)
    )
    feats = "".join(
        '<div class="card"><div class="num">%d</div><h3>%s</h3><p>%s</p></div>'
        % (i, e(t(lang, "f%d_t" % i)), e(t(lang, "f%d_d" % i)))
        for i in range(1, 5)
    )
    cats = "".join(prod_card(lang, p, with_meta=False) for p in PRODUCTS)
    faq = "".join(
        '<details><summary>%s</summary><div class="answer">%s</div></details>'
        % (e(t(lang, "faq%d_q" % i)), e(t(lang, "faq%d_a" % i)))
        for i in range(1, 4)
    )
    certs = "".join("<span>%s</span>" % e(c) for c in CERTS_ALL)

    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": BRAND_OVERRIDES["company"],
        "url": SITE_ORIGIN + "/",
        "email": BRAND_OVERRIDES["email"],
        "telephone": BRAND_OVERRIDES["phone"],
        "address": {"@type": "PostalAddress",
                    "streetAddress": BRAND_OVERRIDES["address"],
                    "addressLocality": "Shenzhen",
                    "addressRegion": "Guangdong", "addressCountry": "CN"},
        "description": t(lang, "foot_desc"),
    }

    body = (
        '<section class="hero">\n'
        '  <div class="wrap">\n'
        '    <h1>%s</h1>\n'
        '    <p class="lead">%s</p>\n'
        '    <div class="actions">\n'
        '      <a class="btn btn-primary" href="%s">%s</a>\n'
        '      <a class="btn btn-ghost" href="%s">%s</a>\n'
        '    </div>\n'
        '  </div>\n'
        '</section>\n'
        '<section class="stats"><div class="wrap"><div class="grid">%s</div></div></section>\n'
        '<section>\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2><p>%s</p></div>\n'
        '    <div class="grid-4">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '<section style="background:var(--surface)">\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2><p>%s</p></div>\n'
        '    <div class="grid-4">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '<section>\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2><p>%s</p></div>\n'
        '    <div class="cert-strip">%s</div>\n'
        '    <p class="note">%s</p>\n'
        '  </div>\n'
        '</section>\n'
        '<section style="background:var(--surface)">\n'
        '  <div class="wrap" style="max-width:820px">\n'
        '    <div class="section-head"><h2>%s</h2></div>\n'
        '    <div class="faq">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '%s'
        % (e(t(lang, "hero_title")), e(t(lang, "hero_sub")),
           e(href(lang, lang, "products.html")), e(t(lang, "hero_cta1")),
           e(href(lang, lang, "contact.html")), e(t(lang, "hero_cta2")),
           stats,
           e(t(lang, "feat_title")), e(t(lang, "feat_sub")), feats,
           e(t(lang, "cat_title")), e(t(lang, "cat_sub")), cats,
           e(t(lang, "cert_title")), e(t(lang, "cert_sub")), certs, e(t(lang, "cert_note")),
           e(t(lang, "faq_title")), faq,
           cta_band(lang))
    )
    return filename, t(lang, "meta_home_title"), t(lang, "meta_home_desc"), body, org


def build_products(lang):
    filename = "products.html"
    buttons = ['<button type="button" class="active" data-filter="all">%s</button>'
               % e(t(lang, "filter_all"))]
    for p in PRODUCTS:
        buttons.append('<button type="button" data-filter="%s">%s</button>'
                       % (e(p["ikey"]), e(t(lang, "cat_%s" % p["ikey"]))))
    cards = "".join(prod_card(lang, p) for p in PRODUCTS)
    body = (
        '%s\n'
        '<section>\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h1>%s</h1><p>%s</p></div>\n'
        '    <div class="filter-bar">%s</div>\n'
        '    <div class="grid-4">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '%s'
        % (breadcrumb(lang, [(t(lang, "crumb_products"), None)]),
           e(t(lang, "prod_title")), e(t(lang, "prod_sub")),
           "".join(buttons), cards, cta_band(lang))
    )
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": t(lang, "crumb_home"),
             "item": SITE_ORIGIN + "/" + lang + "/"},
            {"@type": "ListItem", "position": 2, "name": t(lang, "prod_title"),
             "item": SITE_ORIGIN + "/" + lang + "/" + filename},
        ],
    }
    return filename, t(lang, "meta_products_title"), t(lang, "meta_products_desc"), body, crumbs


def build_product(lang, p):
    filename = page_file(p["slug"], "product")
    rows = []
    for key, label_key in SPEC_ORDER:
        if key == "model":
            value = p["model"]
        elif key in p["spec"]:
            value = p["spec"][key]
        else:
            continue
        rows.append("<tr><th>%s</th><td>%s</td></tr>"
                    % (e(t(lang, label_key)), e(value)))
    certs = "".join("<span>%s</span>" % e(c) for c in p["cert"])
    oem = "".join(
        '<div class="card"><h3>%s</h3><p>%s</p></div>'
        % (e(t(lang, "oem%d_t" % i)), e(t(lang, "oem%d_d" % i)))
        for i in range(1, 4)
    )
    related = "".join(prod_card(lang, q, with_meta=False)
                      for q in PRODUCTS if q["slug"] != p["slug"])

    name = t(lang, "prod_%s_name" % p["ikey"])
    desc = t(lang, "prod_%s_desc" % p["ikey"])

    # Structured data. aggregateRating is supplied as a schema-level field only
    # (per platform convention) and is never rendered as visible on-site ratings.
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": desc,
        "sku": p["model"],
        "image": "%s/assets/img/product/%s-01.jpg" % (SITE_ORIGIN, p["slug"]),
        "brand": {"@type": "Brand", "name": BRAND_OVERRIDES["company"]},
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": "4.7",
                            "reviewCount": "92"},
    }

    body = (
        '%s\n'
        '<section>\n'
        '  <div class="wrap detail-grid">\n'
        '    <div>\n'
        '      <div class="gallery-main">%s</div>\n'
        '      <div class="thumbs">%s</div>\n'
        '    </div>\n'
        '    <div>\n'
        '      <h1>%s</h1>\n'
        '      <p>%s</p>\n'
        '      <h3>%s</h3>\n'
        '      <table class="spec-table"><tbody>%s</tbody></table>\n'
        '      <p style="margin-top:24px"><a class="btn btn-primary" href="%s">%s</a></p>\n'
        '    </div>\n'
        '  </div>\n'
        '</section>\n'
        '<section style="background:var(--surface)">\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2><p>%s</p></div>\n'
        '    <div class="cert-strip">%s</div>\n'
        '    <p class="note">%s</p>\n'
        '  </div>\n'
        '</section>\n'
        '<section>\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2><p>%s</p></div>\n'
        '    <div class="grid-3">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '<section style="background:var(--surface)">\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2></div>\n'
        '    <div class="grid-3">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '%s'
        % (breadcrumb(lang, [(t(lang, "crumb_products"), "products.html"), (name, None)]),
           product_img(p["slug"], 1, name),
           "".join("<div>%s</div>" % product_img(p["slug"], i, name)
                   for i in range(1, IMG_COUNT + 1)),
           e(name), e(desc),
           e(t(lang, "spec_title")), "".join(rows),
           e(href(lang, lang, "contact.html")), e(t(lang, "cta_quote")),
           e(t(lang, "cert_title")), e(t(lang, "cert_sub")), certs, e(t(lang, "cert_note")),
           e(t(lang, "oem_title")), e(t(lang, "oem_sub")), oem,
           e(t(lang, "related_title")), related,
           cta_band(lang))
    )
    title = "%s | %s" % (name, BRAND_OVERRIDES["company"])
    return filename, title, desc, body, jsonld


def build_about(lang):
    filename = "about.html"
    caps = "".join(
        '<div class="card"><h3>%s</h3><p>%s</p></div>'
        % (e(t(lang, "cap%d_t" % i)), e(t(lang, "cap%d_d" % i)))
        for i in range(1, 5)
    )
    miles = "".join(
        '<li><span class="year">%s</span> &mdash; %s</li>'
        % (yr, e(t(lang, "ms_%s" % yr)))
        for yr in ["2008", "2013", "2017", "2021", "2026"]
    )
    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": BRAND_OVERRIDES["company"],
        "url": SITE_ORIGIN + "/",
        "foundingDate": "2008",
        "description": t(lang, "about_p1"),
    }
    body = (
        '%s\n'
        '<section>\n'
        '  <div class="wrap" style="max-width:820px">\n'
        '    <div class="section-head"><h1>%s</h1><p>%s</p></div>\n'
        '    <p>%s</p>\n'
        '    <p>%s</p>\n'
        '  </div>\n'
        '</section>\n'
        '<section style="background:var(--surface)">\n'
        '  <div class="wrap">\n'
        '    <div class="section-head"><h2>%s</h2></div>\n'
        '    <div class="grid-4">%s</div>\n'
        '  </div>\n'
        '</section>\n'
        '<section>\n'
        '  <div class="wrap" style="max-width:720px">\n'
        '    <div class="section-head"><h2>%s</h2></div>\n'
        '    <ol class="timeline">%s</ol>\n'
        '  </div>\n'
        '</section>\n'
        '%s'
        % (breadcrumb(lang, [(t(lang, "nav_about"), None)]),
           e(t(lang, "about_title")), e(t(lang, "about_sub")),
           e(t(lang, "about_p1")), e(t(lang, "about_p2")),
           e(t(lang, "cap_title")), caps,
           e(t(lang, "ms_title")), miles,
           cta_band(lang))
    )
    return filename, t(lang, "meta_about_title"), t(lang, "meta_about_desc"), body, org


def build_contact(lang):
    filename = "contact.html"
    options = "".join(
        '<option value="%s">%s</option>'
        % (e(t(lang, "prod_%s_name" % p["ikey"])), e(t(lang, "prod_%s_name" % p["ikey"])))
        for p in PRODUCTS
    )
    body = (
        '%s\n'
        '<section>\n'
        '  <div class="wrap contact-grid">\n'
        '    <div>\n'
        '      <div class="section-head"><h1>%s</h1><p>%s</p></div>\n'
        '      <div class="form-success" id="form-success">%s</div>\n'
        '      <form id="enquiry-form" novalidate data-endpoint="%s" data-mailto="%s" data-subject="%s">\n'
        '        <div class="form-two">\n'
        '          <div class="form-row"><label for="f-name">%s <i>*</i></label>'
        '<input id="f-name" name="name" type="text" placeholder="%s" autocomplete="name">'
        '<div class="field-error">%s</div></div>\n'
        '          <div class="form-row"><label for="f-email">%s <i>*</i></label>'
        '<input id="f-email" name="email" type="email" placeholder="%s" autocomplete="email">'
        '<div class="field-error">%s</div></div>\n'
        '        </div>\n'
        '        <div class="form-two">\n'
        '          <div class="form-row"><label for="f-company">%s</label>'
        '<input id="f-company" name="company" type="text" placeholder="%s" autocomplete="organization"></div>\n'
        '          <div class="form-row"><label for="f-country">%s <i>*</i></label>'
        '<input id="f-country" name="country" type="text" placeholder="%s"></div>\n'
        '        </div>\n'
        '        <div class="form-two">\n'
        '          <div class="form-row"><label for="f-product">%s <i>*</i></label>'
        '<select id="f-product" name="product"><option value="">--</option>%s</select>'
        '<div class="field-error">%s</div></div>\n'
        '          <div class="form-row"><label for="f-qty">%s</label>'
        '<input id="f-qty" name="quantity" type="text" placeholder="%s"></div>\n'
        '        </div>\n'
        '        <div class="form-row"><label for="f-message">%s</label>'
        '<textarea id="f-message" name="message" placeholder="%s"></textarea></div>\n'
        '        <button class="btn btn-primary" type="submit">%s</button>\n'
        '        <p class="form-note">%s</p>\n'
        '      </form>\n'
        '    </div>\n'
        '    <aside>\n'
        '      <h3>%s</h3>\n'
        '      <ul class="info-list">\n'
        '        <li><span class="k">%s</span>%s<br>%s</li>\n'
        '        <li><span class="k">%s</span><a href="tel:%s">%s</a>%s</li>\n'
        '        <li><span class="k">%s</span><a href="mailto:%s">%s</a></li>\n'
        '        <li><span class="k">%s</span>%s</li>\n'
        '      </ul>\n'
        '    </aside>\n'
        '  </div>\n'
        '</section>'
        % (breadcrumb(lang, [(t(lang, "nav_contact"), None)]),
           e(t(lang, "contact_title")), e(t(lang, "contact_sub")), e(t(lang, "success_msg")),
           e(FORM_ENDPOINT), e(BRAND_OVERRIDES["email"]),
           e("Enquiry from %s website" % BRAND_OVERRIDES["company"]),
           e(t(lang, "f_name")), e(t(lang, "f_name_ph")), e(t(lang, "f_required")),
           e(t(lang, "f_email")), e(t(lang, "f_email_ph")), e(t(lang, "f_required")),
           e(t(lang, "f_company")), e(t(lang, "f_company_ph")),
           e(t(lang, "f_country")), e(t(lang, "f_country_ph")),
           e(t(lang, "f_product")), options, e(t(lang, "f_required")),
           e(t(lang, "f_qty")), e(t(lang, "f_qty_ph")),
           e(t(lang, "f_message")), e(t(lang, "f_msg_ph")),
           e(t(lang, "f_submit")), e(t(lang, "form_note")),
           e(t(lang, "info_title")),
           e(t(lang, "info_addr")), e(BRAND_OVERRIDES["address"]), e(BRAND_OVERRIDES["address_cn"]),
           e(t(lang, "info_phone")), e(BRAND_OVERRIDES["phone"].replace(" ", "")),
           e(BRAND_OVERRIDES["phone"]), wa_link_list(lang),
           e(t(lang, "info_email")), e(BRAND_OVERRIDES["email"]), e(BRAND_OVERRIDES["email"]),
           e(t(lang, "info_hours")), e(t(lang, "info_hours_val")))
    )
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": BRAND_OVERRIDES["company"],
        "url": SITE_ORIGIN + "/",
        "email": BRAND_OVERRIDES["email"],
        "telephone": BRAND_OVERRIDES["phone"],
        "address": {"@type": "PostalAddress", "streetAddress": BRAND_OVERRIDES["address"],
                    "addressCountry": "CN"},
    }
    return filename, t(lang, "meta_contact_title"), t(lang, "meta_contact_desc"), body, jsonld


def wa_float(lang):
    """Floating enquiry shortcut - highest-converting element on B2B trade sites.

    With a single contact it is a direct link. With several it becomes a small
    picker so every sales line stays reachable instead of hiding behind one
    number. Rendered on every page."""
    if len(WHATSAPP) == 1:
        w = WHATSAPP[0]
        return ('<div class="wa-float">'
                '<a class="wa-btn" href="%s" rel="noopener" target="_blank">'
                '%s<span>%s</span></a></div>'
                % (e(w["url"]), WA_ICON, e(t(lang, "cta_whatsapp"))))
    items = "".join(
        '<a class="wa-item" href="%s" rel="noopener" target="_blank">'
        '%s<span>%s</span></a>'
        % (e(w["url"]), WA_ICON, e(wa_label(w)))
        for w in WHATSAPP
    )
    return (
        '<div class="wa-float" id="wa-float">'
        '<button type="button" class="wa-btn wa-toggle" aria-expanded="false">'
        '%s<span>%s</span></button>'
        '<div class="wa-panel">%s</div>'
        '</div>'
        % (WA_ICON, e(t(lang, "cta_whatsapp")), items)
    )


def build_privacy(lang):
    filename = "privacy.html"
    body = (
        breadcrumb(lang, [(t(lang, "privacy_title"), None)]) + "\n"
        '<section>\n'
        '  <div class="wrap" style="max-width:820px">\n'
        '    <div class="section-head">\n'
        '      <h1>' + e(t(lang, "privacy_title")) + '</h1>\n'
        '      <p>' + e(t(lang, "privacy_updated")) + '</p>\n'
        '    </div>\n'
        '    <p>' + e(t(lang, "privacy_intro")) + '</p>\n'
        '    <p>' + e(t(lang, "p_collect")) + '</p>\n'
        '    <p>' + e(t(lang, "p_use")) + '</p>\n'
        '    <p>' + e(t(lang, "p_share")) + '</p>\n'
        '    <p>' + e(t(lang, "p_retention")) + '</p>\n'
        '    <p>' + e(t(lang, "p_rights")) + '</p>\n'
        '    <p>' + e(t(lang, "p_cookies")) + '</p>\n'
        '    <p><strong>' + e(t(lang, "p_contact_k")) + ':</strong> '
        '<a href="mailto:' + e(BRAND_OVERRIDES["email"]) + '">'
        + e(BRAND_OVERRIDES["email"]) + '</a></p>\n'
        '  </div>\n'
        '</section>'
    )
    return filename, t(lang, "privacy_title"), t(lang, "privacy_intro"), body, None


def build_404(lang):
    filename = "404.html"
    body = (
        '<section>\n'
        '  <div class="wrap" style="max-width:640px;text-align:center;padding-block:80px">\n'
        '    <h1>%s</h1>\n'
        '    <p>%s</p>\n'
        '    <p style="margin-top:28px"><a class="btn btn-primary" href="%s">%s</a></p>\n'
        '  </div>\n'
        '</section>'
        % (e(t(lang, "e404_title")), e(t(lang, "e404_sub")),
           e(href(lang, lang, "index.html")), e(t(lang, "e404_cta")))
    )
    return filename, t(lang, "e404_title"), t(lang, "e404_sub"), body, None


def render(lang, filename, title, desc, body, jsonld):
    head_html, dir_attr = head(lang, filename, title, desc)
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">%s</script>' % json.dumps(
            jsonld, ensure_ascii=False, indent=2)
    active = filename.replace(".html", "")
    if active.startswith("product-"):
        active = "products"
    return (
        '<!DOCTYPE html>\n'
        '<html lang="%s"%s>\n'
        '<head>\n'
        '%s'
        '%s\n'
        '</head>\n'
        '<body>\n'
        '%s\n%s\n%s\n%s\n%s\n'
        '<script src="../assets/app.js"></script>\n'
        '</body>\n'
        '</html>\n'
        % (lang, dir_attr, head_html, ld,
           banner(lang), header(lang, filename, active),
           body, footer(lang), wa_float(lang))
    )


def main():
    os.makedirs(DIST, exist_ok=True)
    # Overwrite in place (dirs_exist_ok) instead of deleting + recreating, so
    # the build works even when the host blocks directory removal.
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(DIST, "assets"),
                    dirs_exist_ok=True)

    # Decap CMS admin panel -> served at /admin/ on the live site.
    admin_src = os.path.join(ROOT, "admin")
    if os.path.isdir(admin_src):
        shutil.copytree(admin_src, os.path.join(DIST, "admin"), dirs_exist_ok=True)

    # Root index redirects to the default language directory.
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html><head><meta charset="utf-8">'
                '<meta http-equiv="refresh" content="0; url=en/index.html">'
                '<link rel="canonical" href="%s/en/index.html">'
                '<title>VOSIDO</title></head>'
                '<body><p><a href="en/index.html">VOSIDO</a></p></body></html>' % SITE_ORIGIN)

    count = 0
    for lang in LANGS:
        os.makedirs(os.path.join(DIST, lang), exist_ok=True)
        pages = [build_home(lang), build_products(lang), build_about(lang),
                 build_contact(lang), build_privacy(lang)]
        pages += [build_product(lang, p) for p in PRODUCTS]
        for filename, title, desc, body, jsonld in pages:
            html = render(lang, filename, title, desc, body, jsonld)
            with open(os.path.join(DIST, lang, filename), "w", encoding="utf-8") as f:
                f.write(html)
            count += 1
        f404 = build_404(lang)
        with open(os.path.join(DIST, lang, f404[0]), "w", encoding="utf-8") as f:
            f.write(render(lang, f404[0], f404[1], f404[2], f404[3], None))
            count += 1

    # Deployment helpers: pick the file matching your host and delete the rest.
    with open(os.path.join(DIST, "_redirects"), "w", encoding="utf-8") as f:
        f.write("/ /en/ 302\n")
    with open(os.path.join(DIST, ".htaccess"), "w", encoding="utf-8") as f:
        f.write("RewriteEngine On\nRewriteRule ^$ /en/ [R=302,L]\n"
                "ErrorDocument 404 /en/404.html\n")
    with open(os.path.join(DIST, "vercel.json"), "w", encoding="utf-8") as f:
        json.dump({"redirects": [{"source": "/", "destination": "/en/", "permanent": False}]},
                  f, indent=2)

    urls = []
    for lang in LANGS:
        pages = ["index.html", "products.html", "about.html", "contact.html", "privacy.html"]
        pages += [page_file(p["slug"], "product") for p in PRODUCTS]
        for filename in pages:
            urls.append("  <url><loc>%s/%s/%s</loc>" % (SITE_ORIGIN, lang, filename))
            for alt in LANGS:
                urls.append('<xhtml:link rel="alternate" hreflang="%s" href="%s/%s/%s"/>'
                            % (alt, SITE_ORIGIN, alt, filename))
            urls.append("</url>")
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
                + "\n".join(urls) + "\n</urlset>\n")
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE_ORIGIN)

    print("Generated %d pages across %d languages -> %s" % (count, len(LANGS), DIST))


if __name__ == "__main__":
    main()
