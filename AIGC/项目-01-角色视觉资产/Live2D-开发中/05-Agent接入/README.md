# Klika 原创数字人 · Agent 接入模块

> **现在可以运行本地预览并接收 AI 消息**。当前展示的是从原始角色图提取的透明静态人物；只有把 Cubism Editor 正式导出的模型放入 `model/` 并配好运行库后，才会切换为真实 Live2D 模型。不要误报已完成绑定。

## 1. 本地立即运行

在仓库克隆后的 `05-Agent接入/` 文件夹中打开命令行：

```bash
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8765
```

打开 `http://127.0.0.1:8765/`。界面会使用同仓库自动生成的 `04-资产生成/output/00_subject_cutout.png`，展示角色并连接本地 WebSocket。

界面的按钮可演示普通回复和带气泡的回复。按钮是**人为演示**；正式运行时只有 Agent 自己决定给出非空 `aside` 才会出现气泡。

## 2. 给私人 AI 助手接入

Agent 每条有效输出后，将结果发送到本机 HTTP 入口：

```python
import requests
payload = {
  "type": "assistant.reply",
  "reply": "我已经把项目整理好了。",
  "aside": None,  # 由模型自主决定，默认为 None
  "expression": "neutral",
  "context_safety": "normal",
  "audio_level": 0.0
}
requests.post("http://127.0.0.1:8765/api/events", json=payload, timeout=3).raise_for_status()
```

如果模型认为适合轻吐槽，可自选短句：

```json
{"type":"assistant.reply","reply":"已经完成了。","aside":{"text":"这一版总算顺眼了。","expression":"tease_smile"},"context_safety":"normal"}
```

不要把大模型的隐藏思维链、系统提示或用户私人资料作为 aside；它是人物**表演性文本**。后端会按长度与安全级别过滤，前端还有主动关闭开关。复杂的内容审核应在 Agent 一侧完成。

发声口型预留：按时间节奏发送 `{"type":"avatar.audio_level","audio_level":0.45}`，有真实 Cubism 模型后尝试写入 `ParamMouthOpenY`。最终应按 TTS 音素/音频幅度同步并在具体 Cubism 模型上校准。

## 3. 将来真正装入 Cubism 模型

完成美术补绘、PSD 拆层与 Cubism Editor 的 Mesh/Deformer/Physics/Expression 后，将 **从 Editor 正式导出的整套模型目录**复制到：

```05-Agent接入/model/
  character.model3.json
  model.moc3
  textures/...
  expressions/...
  motions/...
  physics3.json  (若导出)
```

资源路径必须与 `.model3.json` 中的相对引用一致；`model.moc3` 等名称仅是举例。

还需从官方 Cubism SDK 取得并按许可放置 `05-Agent接入/vendor/live2dcubismcore.min.js`。本项目不捆绑 Live2D 专有运行库。网页需要访问 PixiJS 6 和 pixi-live2d-display（当前 CDN 引入）；生产应锁定版本并自行托管所需文件。有关插件与 Cubism Core 的使用见 https://github.com/guansss/pixi-live2d-display 。

接口 `GET /api/status` 能区分 `reference_preview` 和 `cubism`。注意状态 `cubism` 只表示存在入口文件，网页要真正加载成功才能显示模型。

## 4. 边界与安全

- **仅监听本机回环地址** `127.0.0.1`；不允许直接暴露公网，公网部署要增加鉴权、TLS、限流等。
- 禁止把 API Key、私人记忆或用户聊天内容作为模型资源公开上传。
- 此包不修改原始人设；提取过程由 `04-资产生成/build_cutouts.py` 重复生成。
- 暂无正经 `.moc3`：静态预览和预留口型参数不等于现有模型已经能张嘴。
