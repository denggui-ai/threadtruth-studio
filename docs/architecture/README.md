# 用户架构图的维护

`build_overview.py`中的分区、文字与连线是图的源；它生成`../assets/architecture-overview.svg`。`render_overview.cjs`从同一SVG导出PNG，并检查文字边界。图只是已有职责与流程的说明，不改运行时规则。

在仓库根运行：

```sh
python3 docs/architecture/build_overview.py
cdp-bridge.sh
node docs/architecture/render_overview.cjs
cdp-bridge.sh --stop
```

PNG导出需开发环境已有Playwright（必要时设置`NODE_PATH`）及支持中文的系统字体，不是用户运行插件的依赖。只连接9344专用Chrome，新建页面并在完成后关闭，不读取其他页面或登录资料。字体不同可能改变字宽；越界时先修图源，再重新生成。

检查生成前后的SVG是否一致，目测PNG的分区/连线/文字，核对[能力状态](../CAPABILITY-STATUS.md)及链接，再同时提交脚本、SVG和PNG。图不使用生图模型绘制或识别文字，不引入用户私人素材。
