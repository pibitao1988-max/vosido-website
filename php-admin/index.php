<?php
/**
 * VOSIDO 图片后台 —— 登录 / 替换首图与产品图 / 修改密码
 *
 * 设计要点：替换图片时直接覆盖同名文件（hero.jpg、产品-01.jpg …），
 * 因此静态站无需重新生成，刷新页面即可看到新图。
 */
session_start();
require_once __DIR__ . '/config.php';

/* ---------- 工具函数 ---------- */
function h($s)
{
    return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');
}
function logged_in()
{
    return !empty($_SESSION['vosido_admin']);
}
function hash_file_path()
{
    return __DIR__ . '/data/admin.hash';
}
function current_pass_sha()
{
    $f = hash_file_path();
    if (is_file($f)) {
        $v = trim((string)@file_get_contents($f));
        if ($v !== '') {
            return $v;
        }
    }
    return ADMIN_PASS_SHA256;
}
function csrf_token()
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = function_exists('random_bytes')
            ? bin2hex(random_bytes(16))
            : sha1(uniqid('', true));
    }
    return $_SESSION['csrf'];
}
function check_csrf()
{
    return !empty($_POST['csrf']) && !empty($_SESSION['csrf'])
        && hash_equals($_SESSION['csrf'], $_POST['csrf']);
}
function slot_target($rel)
{
    return __DIR__ . '/' . $rel;
}
function do_upload($key, &$msg)
{
    $slots = $GLOBALS['SLOTS'];
    if (!isset($slots[$key])) {
        $msg = '无效的图片位';
        return false;
    }
    if (empty($_FILES['img']) || $_FILES['img']['error'] !== UPLOAD_ERR_OK) {
        $code = isset($_FILES['img']) ? $_FILES['img']['error'] : 'no-file';
        $msg = '上传失败（错误码 ' . $code . '）。若文件较大，请压缩到 5MB 以内。';
        return false;
    }
    $f = $_FILES['img'];
    if ($f['size'] > $GLOBALS['MAX_SIZE']) {
        $msg = '文件太大（' . round($f['size'] / 1048576, 1) . 'MB），请压缩到 5MB 以内。';
        return false;
    }
    $ext = strtolower(pathinfo($f['name'], PATHINFO_EXTENSION));
    if (!in_array($ext, $GLOBALS['ALLOW_EXT'])) {
        $msg = '只支持 ' . implode(' / ', $GLOBALS['ALLOW_EXT']) . ' 格式。';
        return false;
    }
    $info = @getimagesize($f['tmp_name']);
    if ($info === false) {
        $msg = '这不是有效的图片文件。';
        return false;
    }

    $target = slot_target($slots[$key]['rel']);
    $dir = dirname($target);
    if (!is_dir($dir)) {
        $msg = '目录不存在：' . $dir;
        return false;
    }
    if (!is_writable($dir)) {
        $msg = '目录不可写，请把「' . $dir . '」权限改为 755（或 777）后重试。';
        return false;
    }

    $tExt = strtolower(pathinfo($target, PATHINFO_EXTENSION));
    $ok = false;
    // 优先用 GD 统一转成目标格式，避免「PNG 内容 + .jpg 后缀」这类兼容问题
    if (function_exists('imagecreatefromstring')) {
        $data = @file_get_contents($f['tmp_name']);
        $im = @imagecreatefromstring($data);
        if ($im !== false) {
            if ($tExt === 'png') {
                $ok = @imagepng($im, $target);
            } else {
                $ok = @imagejpeg($im, $target, 88);
            }
            imagedestroy($im);
        }
    }
    if (!$ok) {
        $ok = @move_uploaded_file($f['tmp_name'], $target);
    }
    if (!$ok) {
        $msg = '保存失败，请检查目录权限。';
        return false;
    }
    @chmod($target, 0644);
    $msg = '已更新：' . $slots[$key]['label'];
    return true;
}

/* ---------- 动作处理 ---------- */
$msg = '';
$err = '';

if (isset($_GET['action']) && $_GET['action'] === 'logout') {
    $_SESSION = array();
    session_destroy();
    header('Location: index.php');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = isset($_POST['action']) ? $_POST['action'] : '';

    if ($action === 'login') {
        $u = isset($_POST['user']) ? trim($_POST['user']) : '';
        $p = isset($_POST['pass']) ? (string)$_POST['pass'] : '';
        if ($u === ADMIN_USER && hash_equals(current_pass_sha(), hash('sha256', $p))) {
            $_SESSION['vosido_admin'] = 1;
            session_regenerate_id(true);
            $msg = '登录成功。';
        } else {
            $err = '用户名或密码不正确。';
        }
    } elseif ($action === 'upload') {
        if (!logged_in()) {
            $err = '请先登录。';
        } elseif (!check_csrf()) {
            $err = '会话已过期，请刷新页面重试。';
        } else {
            $key = isset($_POST['slot']) ? $_POST['slot'] : '';
            if (do_upload($key, $m)) {
                $msg = $m;
            } else {
                $err = $m;
            }
        }
    } elseif ($action === 'changepass') {
        if (!logged_in()) {
            $err = '请先登录。';
        } elseif (!check_csrf()) {
            $err = '会话已过期，请刷新页面重试。';
        } else {
            $old = isset($_POST['old']) ? (string)$_POST['old'] : '';
            $new = isset($_POST['new']) ? (string)$_POST['new'] : '';
            if (!hash_equals(current_pass_sha(), hash('sha256', $old))) {
                $err = '当前密码不正确。';
            } elseif (strlen($new) < 6) {
                $err = '新密码至少 6 位。';
            } else {
                $dir = __DIR__ . '/data';
                if (!is_dir($dir) && !@mkdir($dir, 0755, true)) {
                    $err = '无法创建 data 目录，请手动创建并给写权限：' . $dir;
                } else {
                    $ok = @file_put_contents(
                        hash_file_path(),
                        hash('sha256', $new)
                    );
                    if ($ok === false) {
                        $err = '写入失败，请把「' . $dir . '」设为可写（755/777）。';
                    } else {
                        $msg = '密码已修改，下次请用新密码登录。';
                    }
                }
            }
        }
    }
}

/* ---------- 页面 ---------- */
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VOSIDO 图片后台</title>
<style>
  :root{--bg:#0f1218;--card:#171b24;--line:#262c38;--txt:#e8ecf4;--mut:#9aa6bd;--acc:#4f8cff;--ok:#34d399;--bad:#f87171}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.6 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Microsoft YaHei",sans-serif}
  .wrap{max-width:1080px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:var(--mut);font-size:13px;margin-bottom:24px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:16px}
  .msg{background:rgba(52,211,153,.12);border:1px solid rgba(52,211,153,.4);color:var(--ok);padding:10px 14px;border-radius:8px;margin-bottom:16px}
  .err{background:rgba(248,113,113,.12);border:1px solid rgba(248,113,113,.4);color:var(--bad);padding:10px 14px;border-radius:8px;margin-bottom:16px}
  label{display:block;font-size:13px;color:var(--mut);margin:12px 0 6px}
  input[type=text],input[type=password],input[type=file]{width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--line);background:#0d1017;color:var(--txt)}
  input[type=file]{padding:8px}
  button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:14px;cursor:pointer;margin-top:14px}
  button:hover{filter:brightness(1.08)}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
  .slot{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
  .slot h3{margin:0 0 2px;font-size:14px}
  .slot .tip{color:var(--mut);font-size:12px;margin:0 0 10px}
  .thumb{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;background:#0d1017;display:block;margin-bottom:10px;border:1px solid var(--line)}
  .thumb.hero{aspect-ratio:16/9}
  .meta{color:var(--mut);font-size:11px;margin-top:8px;word-break:break-all}
  .bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
  a{color:var(--acc)}
  .logout{color:var(--mut);font-size:13px}
</style>
</head>
<body>
<div class="wrap">
<?php if (!logged_in()): ?>
  <h1>VOSIDO 图片后台</h1>
  <div class="sub">登录后可以更换首图与产品图片</div>
  <?php if ($err): ?><div class="err"><?php echo h($err); ?></div><?php endif; ?>
  <form method="post" class="card" style="max-width:380px">
    <input type="hidden" name="action" value="login">
    <label>用户名</label>
    <input type="text" name="user" autocomplete="username" required>
    <label>密码</label>
    <input type="password" name="pass" autocomplete="current-password" required>
    <button type="submit">登录</button>
  </form>
  <div class="card" style="max-width:380px;color:var(--mut);font-size:13px">
    用户名：<b>admin</b><br>
    初始密码见部署交付说明（不印在页面上，避免泄露）。登录后请立即在「修改密码」中更改。
  </div>
<?php else: ?>
  <div class="bar">
    <div>
      <h1>VOSIDO 图片后台</h1>
      <div class="sub">替换后覆盖同名文件，前台刷新即可生效（无需重新生成网站）</div>
    </div>
    <a class="logout" href="?action=logout">退出登录</a>
  </div>
  <?php if ($msg): ?><div class="msg"><?php echo h($msg); ?></div><?php endif; ?>
  <?php if ($err): ?><div class="err"><?php echo h($err); ?></div><?php endif; ?>

  <div class="card">
    <h1 style="font-size:16px;margin-bottom:10px">更换图片</h1>
    <div class="grid">
      <?php foreach ($GLOBALS['SLOTS'] as $key => $s):
        $target = slot_target($s['rel']);
        $exists = is_file($target);
        $url = '../' . str_replace('../', '', $s['rel']); // 相对 admin/ 的访问 URL
        $v = $exists ? (int)@filemtime($target) : 0;
        $isHero = ($key === 'hero');
      ?>
      <div class="slot">
        <img class="thumb<?php echo $isHero ? ' hero' : ''; ?>"
             src="<?php echo h($url . ($v ? '?t=' . $v : '')); ?>"
             alt="<?php echo h($s['label']); ?>">
        <h3><?php echo h($s['label']); ?></h3>
        <p class="tip"><?php echo h($s['tip']); ?></p>
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="action" value="upload">
          <input type="hidden" name="csrf" value="<?php echo h(csrf_token()); ?>">
          <input type="hidden" name="slot" value="<?php echo h($key); ?>">
          <input type="file" name="img" accept="image/jpeg,image/png,image/webp" required>
          <button type="submit">上传替换</button>
        </form>
        <div class="meta">
          <?php if ($exists): ?>
            <?php echo round(@filesize($target) / 1024); ?> KB ·
            <?php echo date('Y-m-d H:i', $v); ?>
          <?php else: ?>
            文件缺失：<?php echo h($s['rel']); ?>
          <?php endif; ?>
        </div>
      </div>
      <?php endforeach; ?>
    </div>
  </div>

  <div class="card" style="max-width:420px">
    <h1 style="font-size:16px;margin-bottom:10px">修改密码</h1>
    <form method="post">
      <input type="hidden" name="action" value="changepass">
      <input type="hidden" name="csrf" value="<?php echo h(csrf_token()); ?>">
      <label>当前密码</label>
      <input type="password" name="old" required>
      <label>新密码（至少 6 位）</label>
      <input type="password" name="new" required>
      <button type="submit">保存新密码</button>
    </form>
  </div>
<?php endif; ?>
</div>
</body>
</html>
