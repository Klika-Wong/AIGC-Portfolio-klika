# 私人数字人 · Live2D 展示与 Agent 接入（开发版）

本模块**仅供项目所有者的本地研发与验证**。目前可以显示从原始人设图导出的透明人物、接收 HTTP/WebSocket 消息、检查面部分层；**还没有真实的 Live2D Cubism 模型**，不能称作已完成的动画绑定。

## 1. 本地启动

在已克隆的私人仓库内：

```powershell
cd "AIGC/项目-01-角色视觉资产/Live2D-开发中/05-Agent接入"
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

浏览器访问 `http://127.0.0.1:8765/`（角色展示）、`/review`（24 个全身分区）或 `/face-review`（13 个面部候选层）。所有图片来自此私人仓库的本地副本，不自动成为开放发布素材。

现有测试只证明部分路由、消息、素材读取和页面能正常工作。模拟眼球移动/图片上下漂移不等于完成 Live2D Rig。

## 2. 数据流与安全边界

| 组件 | 实际行为 | 风险控制 |
| --- | --- | --- |
| 原始图片及 PNG/ORA | 本机服务读取本地仓库目录 | 防止暴露公网上的文件路由；仅监听 loopback |
| `POST /api/events` | 本机代理发送角色答复、情绪和可选 `aside` | **当前没有认证**；同机其他进程可能调用 |
| `WebSocket /ws` | 发送角色显示事件；有同源检查 | 同源检查不是用户账户认证 |
| DeepSeek API | **可选**，配置 Key 后将对话文本发送到第三方服务 | 由所有者明确开启并核对隐私/费用政策 |
| Web Live2D 播放器 | 仅当检测到模型入口文件时，尝试从公共 CDN 获取 PixiJS 与 pixi-live2d-display | 当前不适合宣称“严格离线”；发行前改为本地固定依赖并核查许可 |
| 官方 Cubism Core | 需用户依许可证自行取得并安装 | 仓库当前不捆绑专有 Core，切勿无授权再分发 |

**Private GitHub 仓库 ≠ 本地离线应用。** 本地不录音，也不意味着允许将私人聊天或源图直接发送云模型做测试。接入外部 API 前应明确使用方式和隐私条件。

## 3. 向现有私人助手发布事件

下面的本机事件接口仅是 UI 桥接；主 LLM 或外部行为模型可自行决定是否生成轻吐槽字段。

```python
import requests
event = {
  "type": "assistant.reply",
  "reply": "资料已经整理好了。",
  "aside": None,
  "context_safety": "normal",
  "expression": "neutral",
  "audio_level": 0
}
requests.post("http://127.0.0.1:8765/api/events", json=event, timeout=3).raise_for_status()
```

正式情境下 `aside` 默认 `null`，由上游模型在语境确实合适且非隐私/严肃话题时提供简短的表演文本；不能公开模型内部推理、系统提示、私人资料或 API Key。服务端保留长度和场景验证，**尚不等于全面安全过滤**。

## 4. 可选云对话

若要用已有 DeepSeek 适配器进行实验，**仅在拥有相关服务协议和隐私接受条件后**，于当前 PowerShell 会话设置：

```powershell
$env:DEEPSEEK_API_KEY = "<本人私下设置，不填入 Git>"
$env:DEEPSEEK_MODEL = "<在当前服务商文档中确认的可用模型 ID>"
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

未配置 Key 时本地人物/事件演示仍可使用；配置后会将提交给 `/api/chat` 的输入内容发往 `https://api.deepseek.com/chat/completions`，可能产生费用。**当前未完成真实付费 API 端到端验收**，模型 ID 和 JSON 返回能力要以服务商现行文档为准。

## 5. 日后接入真正 Cubism 模型

先把面部、头发、衣服精修成可以绑定的 PSD，使用 Cubism Editor 制作 ArtMesh、Deformer、参数关键形和物理；然后将按正式导出路径保存的 `.model3.json`、`.moc3`、贴图与表情/动作完整放入本目录 `model/`。

按许可从官方 SDK 安装 `vendor/live2dcubismcore.min.js`。适配器与 Pixi 等库的许可、远程脚本、本地部署与发布条件需另查；**自动发现 .model3.json 只能表示文件存在，不能保证渲染成功或取得再分发授权**。

特别注意：私人研发可先验证技术能力；**公开应用、SDK 分发、可扩展的数字人/avatar 平台可能涉及 Live2D 的额外发表许可或专门审批**。不要按“个人项目就永远免费、可发行”的方式推断。参见 [官方 SDK License](https://www.live2d.com/en/sdk/license/)。

## 6. 发布前须补齐

- [ ] 独立于私有仓库的访问鉴权、网络边界和日志脱敏。
- [ ] 固定并自托管所有可合法分发的第三方 JS；加入 CSP/供应链核验。
- [ ] 确认云 API 数据使用、保存与费用条款；不上传私人人设图片做无必要调用。
- [ ] 原图、参考与派生素材的实际权利核查及去隐私元数据的**发布副本**。
- [ ] 真正完成 Cubism 导出、口型/眼球/物理测试，并确认 SDK 最终发布许可。

合规依据：[私人资产政策](../../../../PRIVATE_ASSETS.md) · [审查记录](../../ASSET_COMPLIANCE_REVIEW.md)。本文件不是软件许可证或法律意见。
