# 部署与 Decap CMS 后台说明（VOSIDO 外贸站）

本站是**纯静态站**：`build.py` 读取 `src/` 下的 JSON 数据，生成 `dist/` 下的 100 个 HTML 页面。

---

## ✅ 当前已实现（自动完成）

- **GitHub 仓库**：https://github.com/pibitao1988-max/vosido-website （`main` 分支，含全部源码与可编辑 JSON）
- **GitHub Pages 已上线**：https://pibitao1988-max.github.io/vosido-website/
  - 由 `gh-pages` 分支托管（已设为 Pages 源），10 种语言、/admin/ 后台均返回 200
- **CloudStudio 临时预览**（可选保留）：之前已部署，作为备用查看地址

数据全部外置：`src/site.json`、`src/products.json`、`src/i18n/<lang>.json`，Decap CMS 只改这些 JSON。

---

## 一、上线前必须改的 3 处

1. **真实域名**：`build.py` 顶部 `SITE_ORIGIN`（影响 hreflang / canonical / sitemap 绝对地址）。
   目前 GitHub Pages 用的是环境变量注入（CI/部署时设 `SITE_ORIGIN`），本地构建默认回退 `https://www.vosido.com`。
2. **产品实拍图**：替换 `src/assets/img/product/*.jpg`（当前是占位图）。
3. **询盘表单**：`build.py` 的 `FORM_ENDPOINT`（留空时回退为邮件 mailto）。

---

## 二、Decap CMS 在线编辑 —— 二选一

后台文件 `admin/index.html` + `admin/config.yml` 已随站点部署。登录方式二选一：

### 方案 A：Netlify + Git Gateway（推荐，约 2 分钟，免 OAuth App）
1. 用 GitHub 登录 Netlify，导入上面的仓库。
2. Build command：`python build.py`，Publish directory：`dist`（已写入 `netlify.toml`）。
3. Site settings → **Identity** → Enable；Identity → **Services** → Git Gateway → Enable。
4. 访问 `https://<你的 Netlify 域>/admin/` 登录即可改内容，保存自动重跑 `build.py`。
   （`admin/config.yml` 默认 `backend: git-gateway`，此方案开箱即用。）

### 方案 B：留在 GitHub Pages + GitHub OAuth App
1. GitHub → Settings → Developer settings → **OAuth Apps** → New OAuth App：
   - Homepage / Authorization callback URL：`https://pibitao1988-max.github.io/vosido-website/`
2. 把 `admin/config.yml` 的 backend 改为（含你的 Client ID）：
   ```yaml
   backend:
     name: github
     repo: pibitao1988-max/vosido-website
     branch: main
     base_url: https://pibitao1988-max.github.io/vosido-website
     auth_endpoint: /api/auth        # 需自备一个 token 代理（见下）
   ```
3. Decap 的 `github` 后端需要一个小代理来做 code→token 交换（GitHub 已停止支持 implicit 流）。
   可部署官方示例 `decap-cms-oauth-provider` 到任意 Serverless，把 `auth_endpoint`/`token_endpoint` 指向它。
4. 改完 `config.yml` 后本地 `python build.py` 重新生成 `dist/`，按本文「本地推 gh-pages」推送。

> 不想自建代理的话，直接用方案 A（Netlify）最省事。

---

## 三、本地开发 / 改完重新上线

```bash
# 本地预览
python -m http.server 8000 --directory dist

# 改了 src/*.json 或模板后重建
python build.py

# 把最新站点推到 GitHub Pages（gh-pages 分支）
# 步骤：checkout 孤儿分支 gh-pages → 清空 → 拷 dist → 提交 → 推送（见仓库历史提交记录）
git push origin main          # 源码/数据改动
# gh-pages 内容 = build.py 产物，手动或脚本同步即可
```

---

## 四、后台能改什么

| 集合 | 文件 | 说明 |
|------|------|------|
| 站点与联系 | `src/site.json` | 公司名、中英文地址、电话、邮箱、多个 WhatsApp 号 |
| 产品 | `src/products.json` | 4 款产品的型号、参数、认证列表 |
| 翻译文案 | `src/i18n/*.json` | 10 种语言各 162 个文案字符串，可逐条修正 |

所有改动保存即写入仓库并触发重新构建，无需碰 `build.py` 或 HTML。
