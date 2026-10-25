# Live2D 什么时候需要 Editor，什么时候不需要？

## 结论

**运行时完全不需要打开 Cubism Editor。** 正式导出后的 \`.model3.json\` + \`.moc3\` + texture、motions、exp、physics 可由 Cubism SDK 加载。已经有 FastAPI + 浏览器 UI 和预留 SDK 入口，可以部署在自己的 AI 助手中。

**制作第一次真正的 Cubism 模型仍需要 Rig。** PNG、PSD、ORA 或由代码生成的分区并不包含关键帧、网格、变形器和物理模拟。不能把一堆图片改后缀当成 \`.moc3\`。当前仓库的 24 个透明区域还只是参考层，大量重叠、遮挡区未补绘。

## 已集成在应用中的功能

- 启动 \`05-Agent接入/\` 的本地服务，即可在浏览器展示透明人物（参考预览）。
- \`http://127.0.0.1:8765/review\`：在应用内放大对比原画、透明部件；调整透明度和缩放，不打开 Editor。
- \`http://127.0.0.1:8765/\`：聊天 / 角色显示；可选 AI 生成的轻吐槽 aside。
- \`model/\` 放置 Cubism 导出的完整模型包后，渲染层尝试载入真正模型，正式绑定后再通过实际模型测试。
- 建议后续做成 Electron 桌面应用，直接把这两个页面嵌入主程序，不用额外启动第三方看图软件。

## 后续修改如何避免一遍遍重新绑定

1. **固定原始人设 identity**：以 \`人物设定-1/人设图.png\` 和 \`主要形象.jpg\` 为参考锚点；保留脸型、刘海及衣物。
2. **图层 ID 固定**：同一个部件保持名称、中心点与层级，不随便移动/重命名。
3. **美术只修需要修改的独立 PSD 图层**；尽量不改结构。
4. **在原有 Cubism 工程中重新导入/替换 PSD**，而不是每次新建模型；重新调整确实发生变化的 Mesh 和参数。
5. 导出运行时 \`.moc3\` 后，覆盖 App 的 \`model/\` 包，运行中重新加载模型，不需要每天手动启动 Editor。
6. AI 模型、TTS、气泡文案、UI 样式和接入逻辑的迭代均不需要 Cubism Editor。

## 真正要精细化的项目优先级

**高优先级：** 刘海、后发、侧发独立发束；眼白/上下睑/瞳孔/高光；眉毛；闭合/张开嘴型和口腔内壁；脖子与面部被遮挡区；衣领和两侧外套。

**中优先级：** 饰品独立抠图、右腕珠串、小盒与手机、眼神微动作、呼吸和衣服摆动。

**后置：** 全身走路、复杂手势和表情物理，先完成自然半身说话模型。

## 专业工具的边界

官方 Live2D Cubism 的 PSD 导入可以让部分修改在原有模型中重新导入（见官方 Import PSDs / Re-import PSDs 文档）。
第三方修图软件导出的 PSD 可能和 Cubism 导入要求不完全兼容，尤其位深、混合模式、颜色空间和图层蒙版；正式导入前要检查。
Live2D 官方也提供基于 Photoshop 的素材分割插件（依赖相关许可证和安装条件），可以辅助切图及填充遮挡区；它不等于一键生成完整绑定模型。

参考：
- https://docs.live2d.com/en/cubism-editor-manual/psd-import/
- https://docs.live2d.com/en/cubism-editor-manual/precautions-for-psd-data/
- https://docs.live2d.com/en/cubism-sdk-manual/model-web/
- https://docs.live2d.com/zh-CHS/cubism-editor-manual/material-separation-ps-plugin-download/
