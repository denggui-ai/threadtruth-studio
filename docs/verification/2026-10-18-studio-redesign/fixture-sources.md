# Fixture sources and limits

这些是本轮真实服饰测试的输入，不是生成结果。图片本体、原始许可元数据及准确哈希保留在私有 `fixtures/`；公开请求矩阵中的 `fixture_bindings` 给出脱敏 ID、源文件名、哈希和适用限制。网页公开可见本身不构成许可。

| Fixture ID | 来源与许可 | 已核图覆盖 | 使用限制 |
| --- | --- | --- | --- |
| `white-puffer-vest` | 项目既有公开主案例 `white-hooded-puffer-vest-korean-cold/rights.json`；CC0（仅在项目有权授予的范围内） | 正面、帽领细节、拉链细节、背面 | 原来源中的背面人物只提供服装证据，不是本轮指定真人 |
| `ai-adult-public` | 同一公开主案例已标记为生成成片的原始 `look-1.jpg`，CC0（同上） | 既有成年 AI 身份、轻微三分之二正面 | 不称本轮生成；身份与其中穿着的白马甲分开；新 SKU 不继承旧服饰 |
| `met-159228` | [The Met：Coat 159228](https://www.metmuseum.org/art/collection/search/159228)，[Open Access](https://www.metmuseum.org/policies/image-resources)，CC0 | 实物正面 | 历史大衣；没有背面图，不推断背面装饰 |
| `met-159518` | [The Met：Child's dress 159518](https://www.metmuseum.org/art/collection/search/159518)，CC0 | 同件正面、背面 | 约1895年儿童棉服，不称现代童装；本轮仅新 AI 儿童 |
| `met-163116` | [The Met：Wedding dress 163116](https://www.metmuseum.org/art/collection/search/163116)，CC0 | 同件正面、背面、袖褶细节 | 约1838年历史婚纱，不自动改为现代婚纱款式 |
| `qipao-henan-2015` | [Cheongsam (Qipao) — Gary Todd](https://commons.wikimedia.org/wiki/File:Cheongsam_(Qipao)_-_16814446292.jpg)，[CC0](https://creativecommons.org/publicdomain/zero/1.0/) | 深蓝长袖旗袍完整正面 | 背景人像不是身份参考；保持立领、可见三枚胸口扣、彩色滚边及提花 |
| `hanfu-daopao-2017` | [Daopao (Ming dynasty style) — LHD](https://commons.wikimedia.org/wiki/File:Daopao_(Ming_dynasty_style).jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 无人物的道袍实物完整正面 | 现代依明制结构制作；不称出土原物，不补不可见内摆、侧褶、背面 |
| `lolita-ijoy-2021` | [Girl in lolita dress at IJOY×CGF — N509FZ](https://commons.wikimedia.org/wiki/File:Girl_in_lolita_dress_at_IJOY%C3%97CGF_(20210501151518).jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | 白色蕾丝羽饰层次服饰的穿着正面 | 只绑定服饰；人物年龄未声明且没有本轮身份复用授权，不能复制脸、发型、年龄或背景人物。用于明确成年新 AI；被头发/手臂/装饰挡住的结构不得虚构 |
| `gongbu-dance-2011` | [公布藏族-锅庄舞蹈-7 — shengjingyoujian](https://commons.wikimedia.org/w/index.php?curid=90950059)，[原 Flickr](https://www.flickr.com/photos/34465632@N04/13072811393/)，[CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/)；Commons 留存通过的 Flickr 许可核验 | 唯一选取中央偏右蓝袖、红腰带、紫裙舞者；无袖长外衣的正面、前片和完整下摆可见 | 仅该节庆／舞蹈服饰的正面测试；不复制人物身份或其他舞者服装。原题“公布”可能指“工布”是依据题名、林芝分类和形制的推断，并非馆藏鉴定；未知背面、成分、精细纹样不作验证结论 |

CC BY-SA 源的传播/改编必须保留适用署名、来源、许可链接、改动说明及相同方式共享条件；不能统一改标 CC0。公开展示生成结果前仍需核对实际使用方式和素材义务。本清单不表示来源机构、摄影师或被摄者认可项目。

## 已排除或未选中

- [HANFU in Clothing store 2018 — 彩色琪子](https://commons.wikimedia.org/wiki/File:HANFU_in_Clothing_store_2018.jpg)，CC BY-SA 4.0：许可明确，但玻璃反射文字覆盖衣领与胸口，不适合作为正式形制保真测试源。
- [RIKORISU 2024 — Yumeto](https://commons.wikimedia.org/wiki/File:20240621_RIKORISU,_Shanghai_Shi_Di-Yi_Baihuo_Shangdian.jpg)，CC BY-SA 4.0：中心完整服装是水手服；边缘 Lolita 被裁切或遮挡，不能误标中心服装类别来填覆盖。
- [The Met 157943](https://www.metmuseum.org/art/collection/search/157943)，CC0：已下载但未选中、未完成本轮适用性核图，不能计入已验证来源。
- [Whistling arrows of Kongpo](https://commons.wikimedia.org/wiki/File:Whistling_arrows_of_Kongpo.jpg)：后来下载并完成核图；弓具遮挡衣服且下部裁切，不适合作为本轮完整服饰保真测试。原许可版本记录差异仍留在私有历史记录，不将其改为已接受素材。

`gongbu-dance-2011` 的限定形制判断参照[国家非遗项目资料](https://www.ihchina.cn/project_details/15263/)及[林芝文旅对节庆服饰与“果秀”的说明](https://wlj.linzhi.gov.cn/lzslyfzwyh/c103820/202412/dc1f000767364c56a4d1f6d80521bb77.shtml)。这些资料支持类型与地域背景，不替该照片作实物鉴定。SR-029、SR-031、SR-033 的私有样片旁分别保留来源、署名、适用 ShareAlike 许可与 AI 改动说明；不将它们统一标为 CC0。

## 待补输入

- `designated-real-adult`：等待用户本轮明确指定的已授权成年人照片及可用朝向。公开服饰照片的摄影许可不自动成为被摄者身份复用授权；旧私图也不能自动复用。该输入只进入私有证据，不发布在本目录。

素材缺口只阻止依赖它的真实请求，其他准备及已具备输入的验证仍可继续。补齐后先记录原图与权利信息、核图并冻结新哈希，再解除相应 blocker；不能追溯性地把旧 `not-run` 改为已运行。
