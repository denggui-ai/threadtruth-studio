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

CC BY-SA 源的传播/改编必须保留适用署名、来源、许可链接、改动说明及相同方式共享条件；不能统一改标 CC0。公开展示生成结果前仍需核对实际使用方式和素材义务。本清单不表示来源机构、摄影师或被摄者认可项目。

## 已排除或未选中

- [HANFU in Clothing store 2018 — 彩色琪子](https://commons.wikimedia.org/wiki/File:HANFU_in_Clothing_store_2018.jpg)，CC BY-SA 4.0：许可明确，但玻璃反射文字覆盖衣领与胸口，不适合作为正式形制保真测试源。
- [RIKORISU 2024 — Yumeto](https://commons.wikimedia.org/wiki/File:20240621_RIKORISU,_Shanghai_Shi_Di-Yi_Baihuo_Shangdian.jpg)，CC BY-SA 4.0：中心完整服装是水手服；边缘 Lolita 被裁切或遮挡，不能误标中心服装类别来填覆盖。
- [The Met 157943](https://www.metmuseum.org/art/collection/search/157943)，CC0：已下载但未选中、未完成本轮适用性核图，不能计入已验证来源。

## 待补输入

- `gongbu-user-or-cleared-public`：需同件、可清楚核对的林芝工布真实服饰图及明确许可。[Whistling arrows of Kongpo](https://commons.wikimedia.org/wiki/File:Whistling_arrows_of_Kongpo.jpg) 候选页面的 CC BY 3.0/4.0 记录不一致，且尚未完成服饰细节核图；本轮未下载为正式输入。一般藏袍、其他地区服饰、绘画或生成图不能替代工布实物测试。
- `designated-real-adult`：等待用户本轮明确指定的已授权成年人照片及可用朝向。公开服饰照片的摄影许可不自动成为被摄者身份复用授权；旧私图也不能自动复用。该输入只进入私有证据，不发布在本目录。

素材缺口只阻止依赖它的真实请求，其他准备及已具备输入的验证仍可继续。补齐后先记录原图与权利信息、核图并冻结新哈希，再解除相应 blocker；不能追溯性地把旧 `not-run` 改为已运行。
