#!/usr/bin/env python3
"""Build the public architecture overview. No images, private inputs or dependencies."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W, H = 2400, 1900
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
'<title id="title">ThreadTruth Studio 裁光：底层逻辑与关键流程</title>',
'<desc id="desc">七个分区展示用户入口、由 Codex Agent 执行的 Skill 核心、两个可选生图入口、交付、私人数据、本地及人工质量控制和八条用户旅程。以 beta.12 为基线；实现不等于全面验证。</desc>',
'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#244c73"/></marker></defs>',
'<style>text{font-family:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif;fill:#17334e} .title{font-weight:700} .muted{fill:#496177}</style>',
'<rect width="2400" height="1900" fill="#f7fafc"/>']
colors = {'green':('#087d64','#eaf7f1'), 'blue':('#176bb0','#eaf3fb'), 'purple':('#6540a2','#f2edfb'), 'orange':('#a75315','#fff3e8'), 'pink':('#a63363','#fbeef4')}

def rect(x,y,w,h,fill='#fff',stroke='#d9e4ec',radius=12):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

def txt(x,y,text,size=22,bold=False,color=None,maxwidth=None):
    klass='title' if bold else ''
    maxwidth = maxwidth or (W-x-40)
    style=f' style="fill:{color}"' if color else ''
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" data-maxwidth="{maxwidth}" class="{klass}"{style}>{escape(text)}</text>')

def lines(x,y,items,size=22,gap=36,color=None,maxwidth=None):
    for i,item in enumerate(items): txt(x,y+i*gap,item,size,color=color,maxwidth=maxwidth)

def panel(x,y,w,h,title,tone):
    ink,bg=colors[tone]
    rect(x,y,w,h,bg,ink)
    txt(x+22,y+43,title,29,True,ink,maxwidth=w-44)

def card(x,y,w,h,title,items,tone='blue',size=22,gap=34):
    ink,_=colors[tone]
    rect(x,y,w,h)
    txt(x+18,y+34,title,25,True,ink,maxwidth=w-36)
    lines(x+18,y+72,items,size,gap,maxwidth=w-36)

def arrow(points,label=None,lx=None,ly=None):
    p=' '.join(f'{x},{y}' for x,y in points)
    parts.append(f'<polyline points="{p}" fill="none" stroke="#244c73" stroke-width="3" marker-end="url(#arrow)"/>')
    if label: txt(lx,ly,label,18,True)

# Header and product goals.
txt(40,65,'ThreadTruth Studio | 裁光',53,True)
txt(40,110,'底层逻辑与关键流程  ·  beta.12 现状图',30,True)
txt(40,147,'真实服饰事实 → 受约束的拍摄方案 → 逐张生成与验收 → 对应规格交付',23)
rect(1350,28,1010,125,'#eaf3fb')
for i,(a,b) in enumerate([('商品真实','不编造不可见细节'),('摄影质感','风格服务于商品'),('人物可延续','确认后携带参考包'),('交付可核对','原文件与分项验收')]):
    txt(1375+i*246,72,a,26,True)
    txt(1375+i*246,115,b,20)

# 1: users.
panel(40,180,400,640,'1. 用户层 · 入口与意图','green')
card(60,245,360,132,'自然语言 + 真实素材',['“帮我生成一组穿搭图”','商品实拍 / 可选人物参考'],'green')
card(60,391,360,157,'选择或委托推荐',['人物、风格、用途与画布','单张 / 整组 / 预览 / 提示词','已有明确授权沿用'],'green')
card(60,562,360,234,'不同意图，不同出口',['咨询、识别、推荐：不生图','只要提示词：不生图','先测一张 / 六张独立图','改已有图 / 新品沿用人物','隐式发现尚未全面验证'],'green',21,32)

# 2: core; explicit executor, rules are not daemons.
panel(510,180,890,640,'2. Skill 核心 · Codex Agent 读取规则并执行','blue')
card(532,245,846,102,'SKILL.md · 总控规则',['规则决定读什么、何时调用、何时暂停；不是独立调度服务。'],'blue',22)
card(532,362,270,176,'识别与流程',['recognition.md','flow-gates.md','商品事实 / 意图 / 授权'],'blue',20,32)
card(820,362,270,176,'事实与人物约束',['safety-core.md','model-selection.md','已有身份 ≠ 严格锁脸'],'blue',20,32)
card(1108,362,270,176,'提示词编排',['prompt-build.md','只取受约束视觉字段','当前商品始终是事实源'],'blue',20,32)
card(532,553,540,162,'拍摄规划与风格选择',['style-router.md · 24 风格包','modes-scenes.md · 棚拍 / 场景 / 混合','真人 / 不露脸 / 平铺 / 挂拍 / 人台'],'blue',21,31)
card(1090,553,288,162,'验收字段独立',['qa_extra 先按事实过滤','仅进入质量验收','不进入生成提示词'],'orange',20,31)
rect(532,732,846,63,'#dcecf9')
txt(550,773,'先形成一份具体方案；确认对象明确后执行，不反复让用户填表。',22,True)

# 3: generation is optional and native is default.
panel(1450,180,380,640,'3. 生图执行 · 可选入口','purple')
card(1470,245,340,221,'Codex 原生 · 默认',['宿主内置 image_gen','单张 / 六图 / 方向预览','图片额度与授权分别核对','不外接第三方 API'],'purple',22,36)
card(1470,483,340,237,'ChatGPT 网页 · 显式选择',['宿主浏览器或人工转交','上传与提交需适用授权','现有适配：单张 / 六张','网页预览未列为已适配','不会自动切换入口兜底'],'purple',21,32)
txt(1470,773,'返回原文件，再进入逐张 QA',22,True)

# 4: outputs; distinguish technical complete vs release.
panel(1880,180,480,1045,'4. 输出与交付','green')
card(1902,245,436,211,'按所选规格交付',['仅提示词：文字，0 次生图','方向预览：1 张六宫格，非成片','单张测试：1 张，满意后收尾','整组：6 张独立图，串行生成'],'green',22,36)
card(1902,475,436,195,'三个判断，分别成立',['技术 QA：能否继续生成','人物确认：用户接受实际首张','商业放行：交付条件全部满足','本地 complete 不等于 image-ready'],'green',21,34)
card(1902,689,436,303,'image-ready · 整组放行条件',['当前商品硬事实人工核对','逐张比例、像素与批次基线合规','商品 / 人物 / 动作视觉 QA 通过','应有图片完整，硬失败已关闭','用户源图核对与 AI 标识义务完成','预览和单张不冒充六张整组'],'green',22,36)
card(1902,1010,436,190,'用于图片素材交付',['电商主图 / 社媒封面 / 详情素材','品牌展示；不自动生成整页排版','不保证平台审核、转化或销售效果'],'green',21,34)

# 5: resources.
panel(40,875,870,350,'5. 数据与资源 · 本地记录，私人素材不进公开仓库','blue')
card(60,942,267,257,'规则与配置',['references/ · 方法规则','references/styles/ · 风格包','scripts/ · 本地助手','.codex-plugin/plugin.json','agents/openai.yaml','仅发现，不授予调用权限'],'blue',17,31)
card(343,942,267,257,'私人任务与参考包',['版本化任务 / 图片 / 历史','保留原请求与累计次数','人物包由用户指定读取','新品使用新品实拍','不自动继承旧商品 / 授权','不承诺跨聊天自动记忆'],'pink',19,31)
card(626,942,264,257,'本地工具职责',['web-task.py：两入口账本','model-reference.py：人物包','image-spec-check.py：尺寸','wardrobe-edit.cjs：局部编辑','不点击网页，不调用生图','固定姿势需手工边界'],'blue',17,31)

# 6: QA.
panel(960,875,870,350,'6. 质量控制 · 机器文件检查 + Agent 视觉核对 + 用户确认','orange')
card(980,942,267,257,'文件与元数据',['原文件可读取且完整','每张尺寸符合目标','首张建立像素基线','后续保持同组尺寸','重复文件 / 张数 / 顺序','脚本或宿主等价检查'],'orange',20,31)
card(1263,942,267,257,'Agent 视觉 QA',['对照当前商品实拍','结构、细节、配饰、构图','人物、动作与风格表现','qa_extra 只作核对项','不能用元数据替代目测','失败先停后续编号'],'orange',20,31)
card(1546,942,264,257,'用户实际确认',['人像首张需接受当前人','非人像跳过身份项','商品硬事实由用户核对','满意不覆盖硬错误','已授权整组消费剩余额度','新增重试需明确授权'],'orange',19,31)

# Dependencies in gutters, no implied direct release from generation.
arrow([(440,335),(510,335)])
arrow([(440,615),(510,615)])
arrow([(1400,485),(1450,485)])
arrow([(1640,820),(1640,875)])
arrow([(1830,1090),(1880,1090)])
arrow([(900,820),(900,848),(620,848),(620,875)])
arrow([(910,1060),(960,1060)])

# 7: eight user journeys, boxes explicitly identify pauses.
panel(40,1280,2320,508,'7. 关键流程 · 根据用户意图进入；不是每次都跑完整流程','pink')
flows=[
('A. 咨询 / 推荐','不生图',['描述需求 / 可选参考','分析与推荐方向','给出一个具体建议','需要时展开备选','文字交付并结束'],'不消耗图片额度'),
('B. 识别 / 分析','不生图',['读取当前商品实拍','识别可见服饰事实','未知细节标不确定','给出分析与建议','素材不足请求补图'],'不编造背面或细节'),
('C. 仅提示词','不生图',['确认用途与方案','商品 / 人物约束过滤','编排编号提示词','交付提示词与负面词','不自动提交生成'],'qa_extra 不进入提示词'),
('D. 单张测试','动作 2 · 一次',['明确方案与生成授权','生成并取得原文件','尺寸 + 商品 / 人物 QA','展示图并接受反馈','满意即完成单张'],'失败暂停；重试需授权'),
('E. 六张独立图','动作 1 · 串行',['确认方案与最多六次授权','首张：尺寸 + 视觉 QA','人像：用户接受实际人物','按剩余额度逐张检查续生','六张齐后核整组放行'],'首张失败，不继续后五张'),
('F. 修改已有图','明确修改范围',['指定要改的任务与图片','确认改什么、保留什么','依适用授权执行编辑','重新检查受影响项目','保留旧图与新版记录'],'不自动覆盖原确认锚点'),
('G. 新品 / 换场景','沿用已确认人物',['指定原始人物参考包','读取新品事实与保留条件','明确新任务和生成授权','新首张再次分项核对','更新记录并按规格交付'],'不继承旧商品或旧授权'),
('H. 异常恢复','不盲目重发',['未知结果：先恢复原请求','下载失败：恢复同一原图','终态失败：保留凭据 / 字节','核实终态 + 显式恢复协议','获新授权后才新增重试'],'保留历史与已用次数'),
]
for i,(title,sub,steps,note) in enumerate(flows):
    x=60+i*288
    rect(x,1346,270,420,'#fff','#e7cbd8')
    txt(x+14,1380,title,24,True,colors['pink'][0])
    txt(x+14,1412,sub,18)
    for j,step in enumerate(steps):
        yy=1435+j*53
        rect(x+14,yy,242,38,'#f0f6fb','#d4e3ee',6)
        txt(x+23,yy+26,step,17,maxwidth=224)
        if j<4 and not (i==7 and j<2): arrow([(x+135,yy+38),(x+135,yy+51)])
    txt(x+14,1738,note,17,True,colors['pink'][0],maxwidth=242)

# Footnotes tie evidence to capability inventory without invented maturity numbers.
txt(40,1834,'现状边界：24 风格已实现且有历史样例；人物复用仅有受限实图证据。严格真人还原、自由姿势一致性与部分商品细节仍未解决。',24,True)
txt(40,1873,'基线 beta.12 · 2026-10-07   |   实现 / 实际验证 / 未解决项分开盘点：docs/CAPABILITY-STATUS.md   |   github.com/denggui-ai/threadtruth-studio',22)
parts.append('</svg>')
(ROOT/'docs/assets/architecture-overview.svg').write_text('\n'.join(parts)+'\n',encoding='utf-8')
print('Built docs/assets/architecture-overview.svg (2400 × 1900)')
