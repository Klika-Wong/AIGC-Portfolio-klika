# 项目 01 / Live2D 私人资产合规审查

审查日期：2026-10-25。核对依据：GitHub Private 状态、当前主分支目录树、人物设定/提示词、生成脚本、质量 manifest、接入代码与 Actions 配置。

> 内部风险评估，非法律鉴定或权属证明。未检查的创作账户记录、全部仓库历史和未提交的原素材不在本次证据范围。

## 审查结论

| 范围 | 可核验状态 | 未决事项 |
| --- | --- | --- |
| 仓库访问 | **GitHub Private** | 其他协作者、连接器、Actions 设置应另查 |
| 开放授权 | 当前目录树**未发现 LICENSE** | 没有显式公开授权；不能证明任一第三方元素由此获得许可 |
| 原始角色 | 人物档案、源图和长期提示词存在 | 每件原图的生成平台、输入参考及权利链待核实 |
| `image*.png` 等辅助参考 | 文件实际存在 | 文件名不能证明拍摄者或生成者，禁止直接纳入公开素材包 |
| 派生分层 | 生成脚本与人设源图链接可追踪 | 上游原图许可不明时，派生层也不能自动对外授权 |
| Cubism | 尚无正式 `.moc3` / `.model3.json` | PSD 精修、Rig、物理与导出均未完成 |
| GitHub Actions | 曾上传 30 天保留的 PNG/ORA artifacts，且运行在 GitHub 托管环境 | 旧 artifacts 的实际剩余期、历史记录及访问范围需要另查 |
| 网络依赖 | DeepSeek 可选、Cubism 加载路径引用公共 CDN | 数据发送与 JS 运行安全需要单独审批 |
| 外部许可 | Live2D、Pixi、生成平台条款独立存在 | 发布前确认最新对应用途及可能的 Expandable Application 条款 |

## 源图质量 ≠ 权属审查

- 现有 `04_quality_audit.json`：24 个候选区域、253,877 个多层重叠像素、68 个头发 Alpha 修补像素。
- `07-面部结构/output/manifest.json`：13 个面部候选/参考层、中立表情像素平均误差 0.785/255。
- 这些能支持“有来源一致的分层实验”，**不能**支持“已独占版权、可直接出售模型、已做完 Cubism Rig”的表述。

## 来源和权利链的缺口

用户明确称人物为自主 AI 创作。仓库文字能确认设定、约束和修图工作；还没有逐张原图的创建日志、当时平台条款、外部参考来源、授权凭据和人类补绘记录。`doubao_seedream_...jpg` 文件名只能作为线索，不足以证明生成服务的完整许可内容。

当图片涉及外部人物、商标、服装照片或第三方视觉参考时，应记录权利状态。**缺证据 = 待核实；既不等于已经违规，也不等于已经获得公开授权。**

## 优先处理

1. 保持所有源图和 prompt 不变，按 [资产登记](ASSET_REGISTER.md) 为核心图片补齐创建工具、时间、来源和权利证明。
2. 不再把 GitHub Private 简化描述为“只有本机持有”。GitHub CI、备份与连接器同样属于数据处理链。
3. 不默认运行向远程系统复制素材的工作流；对仓库外展示和模型商用单独做授权审核。
4. 将应用的本机 WebSocket/HTTP、可选 DeepSeek API、公共 CDN 等网络行为明确列入产品隐私文档。
5. 仅在正规分层补绘、绑定、SDK 许可核实以后发布 Live2D 运行模型。

## 此次无法判定

图像潜在相似性、可见水印、所有 EXIF/GPS 元数据是否已经清理、原始生成账户和所有法域下的著作权归属，均未取得足够证据。需人工检查或运行本仓库提供的**不打印元数据值**的私有审计脚本。

官方参考：[Live2D SDK Release License](https://www.live2d.com/en/sdk/license/)、[GitHub Actions Access/Retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)。
