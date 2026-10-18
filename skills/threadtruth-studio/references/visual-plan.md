# 统一视觉方案

在识别真实服饰并确定方向后读取本文件。用途、服饰保护、摄影/场景/媒介共同形成一份可审阅方案；不向用户要求填写内部JSON。先用两三句说明人物来源、所选方向、拍法、数量及影响结果的缺项，沿用已有明确授权。

## 按需读取与准备

1. 从`visual-library/index.json`定位入口，读取对应卡片。原24入口读取其pack与所选摄影基准；文化资料只读所选条目。完整知识库用于查询，不整库灌入提示词。
2. 固定当前真实SKU、源图可见范围和少数关键结构。`garment.description/keep`仅写可核对事实；来源哈希绑定实际商品附件。未知背面不能用文化知识、同类照片或AI图片补齐。
3. 确定表达用途：`product-display`商品展示、`styled-editorial`穿搭编辑、`art-campaign`艺术广告。摄影为默认；选择服饰插画才使用`illustration`及明确的简化边界，不自动把真实商品当虚构设计。
4. 入口提供摄影默认，具体到本次环境、光源方向、构图和色彩关系。逐张差异写在`shots`；真实姿势/头向/景别仍由shot_plan或real_face_plan负责，场景不得偷偷强加坐姿、快走或拉伸。
5. 比较建立多个独立方案；融合保留一个primary和明确supporting及fusion_note。既有原人物条件优先，卡片的模特气质不变成人物身份或未知身体事实。

## 冻结接口

schema2新任务可携带顶层`visual_plan` v1及其哈希，启用prompt contract 2。核心内容：

- `objective`、`output_medium`、`output_form`（human/faceless/flat-lay/hanger/mannequin，与当前任务一致）；
- `style.primary`与`style.supporting`的`id/version/sha256/snapshot`，冻结来源卡全文；
- `garment.description/keep/source_sha256s`、允许的`styling`；
- `photography.scene/lighting/composition/palette`、`art.direction/techniques/limits`、限定范围的`negatives`；
- `shots`按实际slot和pose冻结逐张场景、光线及构图；文化服饰可另有冻结的`culture_profile`。

来源快照哈希证明文本一致，不能证明资料真实或生成效果。私人原图与客户资料只进入私人任务目录，不写回共享风格卡或运行库。

`scripts/visual_library.py`读取入口并准备方案；`scripts/visual_plan.py`校验和渲染；`scripts/web-task.py`负责原生/网页统一任务、冻结和导出。新v2编号人物/不露脸任务还必须给出实际shot_plan，不能只传视觉编号当姿势；自定义单张、人物检查、修正编辑按原专门路径。非人像多张需在shots写清逐张构图与源图支持，不能复制六遍同一场景冒充完整方案。纯结构方案可不再手写prompts；同时提供时必须与统一编译结果一致，不在正文另贴一套旧风格描述。只要提示词时只运行本地编译/导出，不登记图片成功、不调用生成工具。

## 修改、承接和恢复

预览修改只更新用户指定部分，保留未要求改动的商品、人物、动作与视觉条件。候选方案、实际渲染图、用户接受、调用授权分别记录；未经渲染的新方案不能冒充已接受方向。方向确认后，单张或六张任务承接已接受方案，预览像素不当成片或人物依据。

续图与恢复使用任务里冻结的plan；索引或卡片升级不改旧任务。无visual_plan的旧任务继续按原契约恢复；要采用新方案须显式准备新版本，不静默升级或重写历史请求。输出、修订与未知请求保留累计次数，先查询未知请求再决定是否需要新的授权调用。

## 分项验收与交付

按commercial-qa分别检查商品、人物、动作和视觉表现。艺术媒介的已约定简化不等于照片保真；仍须保留服装关键形制、比例和纹样关系，不用“艺术化”豁免事实错误。图片、提示词和复用信息应指向同一冻结版本；能力说明明确实际样片范围、失败和待核项。没有实图不能说效果提升，单张通过不能说整个方向普遍通过。
