# -*- coding: utf-8 -*-
"""Split editable content out of build.py / i18n.json into per-purpose files.

Why: Decap CMS can only edit data files (JSON/YAML), and it writes the WHOLE
file back on save. A single i18n.json holding 10 languages would therefore be
overwritten with just the language being edited. Splitting per language makes
CMS editing safe.

This reads the live constants straight out of build.py (import) instead of
regex-parsing source, so the exported data cannot drift from what is in use.

Produces:
    src/site.json        company info + WhatsApp contacts
    src/products.json    product catalogue
    src/i18n/<lang>.json one file per language

Usage:  python migrate_to_cms.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, ROOT)

import build  # noqa: E402  (module-level code only defines data + functions)


def dump(rel, data):
    path = os.path.join(SRC, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("wrote src/%s" % rel)


# 1. one file per language
for lang, table in build.I18N.items():
    dump("i18n/%s.json" % lang, table)

# 2. company info + whatsapp contacts
b = build.BRAND_OVERRIDES
dump("site.json", {
    "company": b["company"],
    "company_cn": b["company_cn"],
    "address": b["address"],
    "address_cn": b["address_cn"],
    "phone": b["phone"],
    "email": b["email"],
    "whatsapp": build.WHATSAPP,
})

# 3. product catalogue
dump("products.json", build.PRODUCTS)

print("\nsite.json whatsapp :", [w["number"] for w in build.WHATSAPP])
print("products.json      :", [p["slug"] for p in build.PRODUCTS])
print("i18n languages     :", sorted(build.I18N.keys()))
