#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate admin/config.yml for Decap CMS.

Why generate instead of hand-writing:
  - i18n/*.json has 162 string keys per language. Hand-typing them into
    config.yml is error-prone and silently drifts from the data files.
  - This script reads the real en.json keyset and emits a matching object
    widget for every language, so the CMS form and the data never disagree.

Run:  python tools/gen_cms_config.py
Writes: admin/config.yml
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
ADMIN = os.path.join(ROOT, "admin")
LANGS = ["en", "es", "pt", "fr", "de", "ru", "tr", "ar", "ja", "ko"]
LANG_NAMES = {
    "en": "English", "es": "Español", "pt": "Português", "fr": "Français",
    "de": "Deutsch", "ru": "Русский", "tr": "Türkçe", "ar": "العربية",
    "ja": "日本語", "ko": "한국어",
}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


en = load(os.path.join(SRC, "i18n", "en.json"))
keys = list(en.keys())

# i18n object fields (one string field per translation key)
i18n_fields = "\n".join(
    '              - {name: %s, label: "%s", widget: string}' % (k, k)
    for k in keys
)

# 10 per-language file entries
i18n_files = ""
for lg in LANGS:
    i18n_files += (
        "      - name: i18n-%s\n"
        "        label: \"%s\"\n"
        "        file: \"src/i18n/%s.json\"\n"
        "        fields:\n"
        "          - name: \"\"\n"
        "            label: \"文案 (所有字符串)\"\n"
        "            widget: object\n"
        "            fields:\n"
        "%s\n"
    ) % (lg, LANG_NAMES[lg], lg, i18n_fields)

config = """# Decap CMS configuration
# Docs: https://decapcms.org/docs/configuration-options/
#
# IMPORTANT - this site is BUILT from data, not hand-written HTML.
# Decap edits the JSON files under src/. After any save, your host must run
#   python build.py
# to regenerate dist/ (see DEPLOY.md / netlify.toml).
#
# Backend: git-gateway works out of the box on Netlify (Enable Identity +
# Git Gateway). On Vercel/GitHub Pages, switch to the `github` backend and
# register a GitHub OAuth app - see DEPLOY.md.

backend:
  name: git-gateway
  branch: main

# Lets you log into /admin on a local dev server for testing.
local_backend: true

# Product images uploaded in the CMS land here; build.py copies them to dist/.
media_folder: "src/assets/img/product"
public_folder: "/assets/img/product"

collections:
  # ---- 1. Company & contact (editable daily) --------------------------------
  - name: site
    label: "站点与联系"
    files:
      - name: site-config
        label: "公司与联系方式"
        file: "src/site.json"
        fields:
          - {name: company, label: "公司英文名", widget: string}
          - {name: company_cn, label: "公司中文名", widget: string}
          - {name: address, label: "英文地址", widget: string}
          - {name: address_cn, label: "中文地址", widget: string}
          - {name: phone, label: "电话", widget: string}
          - {name: email, label: "邮箱", widget: string}
          - name: whatsapp
            label: "WhatsApp 销售号"
            widget: list
            summary: "{{fields.number}}"
            field:
              - {name: number, label: "号码", widget: string}
              - {name: url, label: "WhatsApp 链接 (https://wa.me/...)", widget: string}

  # ---- 2. Products (specs, certs, models) -----------------------------------
  - name: products
    label: "产品"
    files:
      - name: products
        label: "全部产品"
        file: "src/products.json"
        fields:
          - name: ""
            label: "产品列表"
            widget: list
            summary: "{{fields.model}} — {{fields.slug}}"
            field:
              - {name: slug, label: "Slug (URL 标识)", widget: string}
              - {name: ikey, label: "ikey (内部键)", widget: string}
              - {name: model, label: "型号", widget: string}
              - name: spec
                label: "参数"
                widget: object
                collapsed: true
                field:
                  - {name: power, label: "功率", widget: string}
                  - {name: voltage, label: "电压", widget: string}
                  - {name: motor, label: "电机", widget: string, required: false}
                  - {name: temp, label: "温度", widget: string}
                  - {name: cord, label: "线长", widget: string}
                  - {name: plug, label: "插头", widget: string}
                  - {name: warranty, label: "保修", widget: string}
                  - {name: moq, label: "起订量", widget: string}
                  - {name: lead, label: "交期", widget: string}
              - name: cert
                label: "认证"
                widget: list
                summary: "{{fields.cert}}"
                field:
                  - {name: cert, label: "认证代号", widget: string}

  # ---- 3. Translations (one object per language) ----------------------------
  - name: i18n
    label: "翻译文案"
    files:
%s
""" % i18n_files

os.makedirs(ADMIN, exist_ok=True)
out = os.path.join(ADMIN, "config.yml")
with open(out, "w", encoding="utf-8") as f:
    f.write(config)
print("wrote", out, "(%d bytes)" % len(config))
print("i18n keys per language:", len(keys))
