# 裁光中性发布页改版验证

## 交付范围

- 柔白、墨黑、浅灰统一首页、对照页共享样式、Logo 与两张分享封面。
- 首页合并重复段落，保留白马甲六图、源图细节、米色套装三方向和直接展示的全部 24 风格。
- 中文默认，英文切换与偏好记忆；页内大图、完整原图回退、关闭后焦点返回。
- 区分未安装与已安装用户，保留首次识别指令，新增页面链接复制及手动复制回退。
- 不改变原始服饰图片、来源与权利声明、插件运行时或公开图库验证范围；无新增生图、遥测或发布操作。

## 验证结果

- 改版前：42 项相关单元测试通过；完整 216 项测试通过。
- 改版后：完整 216 项单元测试通过。
- 真实 Chromium 浏览器 9 组检查通过：语言与刷新记忆、存储不可用、大图与焦点、两类剪贴板结果、无 JavaScript、历史深链接、对照页搜索/盲看、响应式与图片加载。
- 响应式检查覆盖 1440、1024、768、390、320px 及中英文；无页面横向溢出，所有 24 风格可见。
- `tools/check_showcase.py` 通过：48 个原图链接、48 个 WebP 展示图、12 个授权素材、字体覆盖、封面来源记录及部署文件边界。
- 工作流 YAML 解析与 `git diff --check` 通过；浏览器检查加入 CI 与 Pages 部署前验证。
- 桌面/手机实渲染复核：原图比例、六图套组、不同色彩的风格图片、使用入口及分享封面。

## 重现

使用满足 `requirements-dev.txt` 的 Python 环境；浏览器检查需要 Node.js、Playwright 1.58.2 和 Chromium（CI 会安装开发依赖）。

```sh
python -m unittest discover -s tests
node tests/check_home_ui.cjs
python tools/check_showcase.py --gallery gallery/style24-comparison-20260929 --repo-root .
git diff --check
```

Playwright 位于仓库之外时通过 `NODE_PATH` 指定其父 `node_modules` 目录；可给浏览器脚本添加 `--screenshots <输出目录>` 保存关键视口与完整页面截图。

品牌资源重建顺序：使用原先固定版本且通过哈希验证的字体缓存运行 `tools/brand_assets.py build --source-dir <字体缓存>`；运行 `node tools/render_brand_cards.cjs`；再运行 `tools/brand_assets.py manifest --source-dir <字体缓存>`，最后执行发布资源检查。封面渲染拦截全部浏览器请求并使用本地文件，不调用外部图片服务。

## 验证边界

- 本地 Chromium 的视口检查不等于真实 iPhone/Safari 设备验证。
- 未执行 GitHub 远端 CI、推送、合并或部署。
- 未开展外部服饰用户理解测试，不声称转化率提升。
- 系统 Python 曾因缺少 fontTools 出现 16 个依赖错误；切换到已有项目验证环境后，完整测试通过，无产品失败遗留。
