# Klika 面部精细化拆层 v0.5

本目录是以仓库原始 `人物设定-1/人设图.png` 为唯一像素来源的 Live2D 脸部素材工作区。**不是一张重新生成的新角色插画。**

## 本轮真实生成的文件

位于 `output/`：

- `layers/00_face_underpaint.png`：去除静态五官后的底图（局部肤色填补，只是参考）。
- `layers/20_eye_left_base.png` / `20_eye_right_base.png`：眼睛底部、眼睑参考（原虹膜做局部去除处理）。
- `layers/21_iris_left.png` / `21_iris_right.png`：完全独立、保留原图颜色的双虹膜；图像左右按观看方向命名。
- `layers/11_brow_image_right.png`：可见眉毛源像素；被刘海遮住的另一边只提供参考。
- `layers/30_mouth_neutral.png`：原图中立嘴型。嘴唇上下参考另列，不能直接当全部开闭关键形。
- `layers/40_bangs_front_REFERENCE.png`：继续复用原图提取的刘海候选，不会覆盖原图。
- `01_face_neutral_recomposed.png`：拆层重组结果，对照原图检查脸部偏差。
- `02_facial_parts_editable.ora`：含图层顺序的可编辑文件，Krita/GIMP 等兼容软件可打开。
- `03_identity_reassembly_check.png`：脸部对照图。
- `manifest.json`：来源、边界、面部重组误差、未完成事项。

## 直接检查（无需 Cubism Editor）

启动已有数字人 FastAPI 程序，然后打开：

- `http://127.0.0.1:8765/face-review`：选择面部层，查看透明度、对照原画。
- 选择「独立虹膜注视方向」，使用眼球 X/Y 滑块，可实验性移动源图双虹膜。**这是图层可分离性的证明，不是正式 Cubism 眼球 Rig。**

## 经过自动校验

- 所有透明层都严格保留 `1024 × 1536` 像素坐标空间。
- 来源于原画的分区内 RGB 未替换成人工生成的新脸。
- 面部区域重组平均 RGB 误差通过小于 2/255 的自动门槛；准确数值在 manifest 中。
- OpenRaster 包含所需文件和有效 stack.xml。
- Agent 的面部预览与新图片路由已通过 CI。

## 阻塞真正 Live2D 的美术工作（未伪装完成）

1. 逐发丝精修刘海、侧发与后发的透明边缘；给转头时露出的额头、耳侧和发根补画。
2. 补全遮挡眉毛及上下眼睑，完成睁眼、半闭、闭眼多关键形，独立眼白和完整眼窝。
3. 补画张口、口腔内壁、牙齿、舌头、嘴角和完整嘴型形变。
4. 分开脖颈、下巴、躯干、左右肩膀，补转头和呼吸时的遮挡。
5. 原先 24 个全身候选 PNG 仍有重叠和交叉，需要进一步精确抠图与补绘。
6. 经审图的 PSD 导入 Cubism Editor，完成 ArtMesh、变形器、关键帧、物理、表情并正式导出 `.moc3`、`.model3.json`。

目前交付的是**可持续精修与检验的真实源图分层工程**，并非可直接投产的 Live2D 模型。