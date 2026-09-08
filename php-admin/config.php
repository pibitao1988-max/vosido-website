<?php
/**
 * VOSIDO 图片后台 - 配置文件
 *
 * 部署：整个 php-admin/ 目录会被 build.py 拷到 dist/admin/，
 *       随静态站一起上传到你的空间，访问 http://你的域名/admin/ 即可。
 *
 * 要求：PHP 7.0+；assets/img 及 assets/img/product 目录需要有写入权限（755/775/777 视主机而定）。
 */

/** 后台登录用户名 */
define('ADMIN_USER', 'admin');

/**
 * 初始密码的 sha256（只存哈希，不存明文）
 * 明文由部署者单独保管；登录后请立即在后台「修改密码」改成自己的密码。
 * 修改后会写入 data/admin.hash，该文件优先于此处的值。
 */
define('ADMIN_PASS_SHA256', '7a930e18f887138b3efe32b151b3438d6c9f506f7bb23a5c6fdc6f922b739adf');

/**
 * 可管理的图片位（slot）
 * key   => 表单字段名（只能用字母数字和下划线）
 * label => 后台显示名称
 * file  => 相对本文件(admin/)的图片绝对路径片段
 */
$GLOBALS['SLOTS'] = array();

// 1) 首图
$GLOBALS['SLOTS']['hero'] = array(
    'label' => '首图 (Hero)',
    'rel'   => '../assets/img/hero.jpg',
    'tip'   => '首页顶部大图，建议 1600×900 或同比例；任意尺寸会被自动裁成 16:9。',
);

// 2) 产品图（4 款 × 4 张）
$products = array(
    'hair-dryer'          => '吹风机 LV-HD01',
    'curling-iron'        => '卷发器 LV-CI02',
    'hair-straightener'   => '直发器 LV-ST03',
    'straightening-brush' => '直发梳 LV-SB04',
);
foreach ($products as $slug => $name) {
    for ($i = 1; $i <= 4; $i++) {
        $key = $slug . '_0' . $i;
        $GLOBALS['SLOTS'][$key] = array(
            'label' => $name . ' - 第 ' . $i . ' 张',
            'rel'   => '../assets/img/product/' . $slug . '-0' . $i . '.jpg',
            'tip'   => '建议正方形 1:1，如 1000×1000。',
        );
    }
}

/** 允许上传的类型 */
$GLOBALS['ALLOW_EXT'] = array('jpg', 'jpeg', 'png', 'webp');
/** 单张上限（字节） */
$GLOBALS['MAX_SIZE'] = 5 * 1024 * 1024;
