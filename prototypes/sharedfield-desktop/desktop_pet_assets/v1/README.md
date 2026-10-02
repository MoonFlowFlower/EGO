# 桌宠房间角色素材 · 第一版

生成方式：内置 GPT Image / image_gen。独立原创，无输入参考图；没有使用悠小喵模型包的贴图或立绘。

文件：`original_companion_atlas.png`。用途：房间中角色活动的原型素材，与既有 Live2D 的形象一致性尚未解决，不能视为悠小喵的配套原画。

图集布局为 4 列 × 4 行：前三行分别为站立、迈步 A、迈步 B，方向依次为前、左、右、后；第四行为吃饭、看平板、写信、睡觉。

已目视检查：16 个姿态、四向和生活动作均已生成。尚未切图、校准落脚点或验证连续播放效果；此图不是已经接入桌宠的完整动画。生成结果的实际尺寸与透明通道以文件检查为准，不以提示词要求代替验证。

## 生成提示词

```text
Use case: stylized-concept
Asset type: original prototype sprite atlas for a cozy top-down desktop companion game.
Create one square 2048x2048 PNG sprite sheet on a genuinely transparent background, exactly 4 columns by 4 rows of equally sized invisible cells. No visible grid lines, no text, no labels, no watermark. Each pose fully contained in its cell with generous transparent margins, no overlaps.
Character: one completely original adult catgirl in cute chibi proportions, warm brown bobbed hair, brown cat ears, small fluffy tail, sage green loose cardigan over cream shirt, dark brown shorts, cream socks and soft brown slippers. Consistent character, outfit, proportions and scale throughout. Clean softly shaded hand-drawn 2D game art, readable silhouettes and restrained detail.
Camera: fixed high-angle orthographic three-quarter top-down RPG camera, looking down about 55 degrees; visible crown of head, shortened legs, never eye-level portrait. All frames same camera and character scale.
Rows 1-3 have direction columns SOUTH (front looking toward bottom of canvas), WEST (left), EAST (right), NORTH (back looking toward top of canvas).
Row 1: four neutral standing idle poses.
Row 2: four walking poses with left foot forward.
Row 3: four walking poses with right foot forward.
Row 4: four unique everyday actions, all facing southeast: cell 1 sitting and eating from a small bowl with spoon; cell 2 sitting watching a small tablet held on lap; cell 3 sitting writing a letter on a small lap board with pen; cell 4 curled up asleep hugging a small cream pillow. No large furniture, no beds or room background. Small props fit within cell.
Keep all feet/body bases consistently registered in cells for rows 1-3; don't draw shadows spanning cells. Genuine alpha transparency, no painted checkerboard. This is an independent original design with no reference to existing characters.
```
