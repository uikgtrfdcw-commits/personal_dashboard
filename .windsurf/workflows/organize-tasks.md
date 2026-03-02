---
description: 整理 Google Sheets 任务清单
---

# 整理任务清单 Workflow

这个 workflow 会自动整理你的 Google Sheets 任务清单：
1. 把标记"已完成"的任务移到 archive
2. **不改变**主表格的分类和顺序（用户自己管理）

## 执行步骤

### 1. 读取当前任务清单

// turbo
读取 Google Sheets 任务清单的所有数据：

```
使用 mcp1_read_sheet 工具读取：
- spreadsheetId: 1jxztmCu0gPYkYna05ZVGnnjGEnaJKKCx5YsF_fraerk
- range: A1:F50
```

### 2. 识别需要归档的任务

**查找已完成任务**：
- 查找描述列或任何列中包含"已完成"的任务
- 记录这些任务的大类、编号、描述

### 3. 归档已完成任务

// turbo
对于每个标记"已完成"的任务，使用 `mcp1_append_row` 追加到 archive sheet：

```
- spreadsheetId: 1jxztmCu0gPYkYna05ZVGnnjGEnaJKKCx5YsF_fraerk
- range: archive!A:D
- values: [大类任务, 编号, 描述, 完成日期(YYYY/MM/DD)]
```

**大类任务名称规则**：
- 如果原大类是"新增任务"或"任务X：XXX"格式，改为简短总结
- 参考已有 archive 格式：如"拖延症文章"、"家庭任务"、"设备验证"
- 根据任务描述生成简短的大类名称（2-6个字）

### 4. 从主表格删除已归档任务

// turbo
使用 Node.js 脚本从主表格删除已完成的任务：

```bash
cd google_sheets_mcp
node remove_completed.js
```

脚本会：
- 读取主表格所有数据
- 过滤掉包含"已完成"的行
- 重写主表格（只保留未完成任务）

### 5. 整理 archive sheet

// turbo
使用 Node.js 脚本整理 archive：

```bash
cd google_sheets_mcp
node reorganize_archive.js
```

脚本会：
- 修改大类名称为简短总结
- 去除"任务X："前缀
- 去除重复条目
- 按完成日期倒序排序（最新的在最前面）

### 6. 确认完成

输出整理结果摘要：
- 归档了多少条已完成任务
- 从主表格删除了多少行
- archive 去重后剩余多少条

## 注意事项

- **主表格**：只删除已完成任务，不改变其他任务的分类和顺序
- **大类名称**：改为简短总结（如"AI工具配置"、"家庭健康"、"设备采购"）
- **去除前缀**：所有"任务X："前缀都会被去掉
- **归档排序**：按完成日期倒序（最新的在最前面）
- **去重**：相同描述+日期的任务只保留一条
