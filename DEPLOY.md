# 部署与 Decap CMS 后台使用说明（VOSIDO 外贸站）

本站是**纯静态站**：`build.py` 读取 `src/` 下的 JSON 数据，生成 `dist/` 下的 100 个 HTML 页面。
Decap CMS 只负责编辑这些 JSON 数据文件，保存后由托管平台重新运行 `build.py` 重新生成页面。

---

## 一、上线前必须改的 3 处

1. **真实域名** `build.py` 顶部的 `SITE_ORIGIN = "https://www.vosido.com"`
   改成你的正式域名。它影响 hreflang / canonical / sitemap 里的绝对地址。改完重跑 `python build.py`。
2. **产品实拍图** 替换 `src/assets/img/product/*.jpg`（当前是占位图）。
3. **询盘表单** `build.py` 的 `FORM_ENDPOINT`（留空时回退为邮件 mailto）。如用 Formspree，填入其 endpoint。

---

## 二、推到 GitHub

```bash
git init
git add .
git commit -m "VOSIDO multilingual B2B site"
git remote add origin <你的仓库地址>
git push -u origin main
```

> 注意：`admin/config.yml` 里的 `branch: main` 要与你的默认分支一致。

---

## 三、A 方案：Netlify（Decap 后台最省事）

1. Netlify 导入上面的 GitHub 仓库。
2. Build command：`python build.py`，Publish directory：`dist`（已写入 `netlify.toml`，会自动识别）。
3. 后台开启：Site settings → **Identity** → Enable Identity。
4. Identity → **Services** → Git Gateway → Enable。
5. 访问 `https://<你的站>/admin/`，用 Netlify Identity 注册的账号登录即可编辑。
6. 在 `admin/` 后台修改站点信息 / 产品 / 翻译 → 保存 → Git Gateway 自动提交 → Netlify 自动重新构建。

---

## 四、B 方案：Vercel（改用 GitHub OAuth 后台）

`vercel.json` 已配置好 `buildCommand` 和 `outputDirectory`。但 `git-gateway` 是 Netlify 专属，
用 Vercel 时需要把后台换成 GitHub OAuth：

1. 在 GitHub 注册一个 **OAuth App**（Settings → Developer settings → OAuth Apps）：
   - Homepage / Callback：`https://api.netlify.com/...` 不适用；用 Vercel 时回调填 `https://<你的域>/callback`。
2. 把 `admin/config.yml` 改成：

   ```yaml
   backend:
     name: github
     repo: <你的用户名>/<仓库名>
     branch: main
     base_url: https://<你的域>
     auth_endpoint: /api/auth
   ```

3. 需要自建一个 OAuth 代理（如 `netlify/gotrue` 或 `decap-cms-oauth-provider`）。
   一般中小团队直接用 Netlify 方案更省事。

---

## 五、本地预览 / 本地后台（可选）

```bash
# 1) 起一个静态服务器看站
python -m http.server 8000 --directory dist

# 2) 本地试 Decap（需另开一个终端跑官方本地鉴权服务）
npx decap-server     # 访问 http://localhost:8080/admin/
```
`admin/config.yml` 里的 `local_backend: true` 即为本地模式开关。

---

## 六、后台能改什么

| 集合 | 文件 | 说明 |
|------|------|------|
| 站点与联系 | `src/site.json` | 公司名、中英文地址、电话、邮箱、多个 WhatsApp 号 |
| 产品 | `src/products.json` | 4 款产品的型号、参数、认证列表（增删产品也会自动反映在站点） |
| 翻译文案 | `src/i18n/*.json` | 10 种语言各 162 个文案字符串，可逐条修正 |

所有改动保存即写入仓库并触发重新构建，无需碰 `build.py` 或 HTML。
