# 九宝量化 V6.0 260701满意版 — 定版保留

**归档时间**：2026-07-01 21:57  
**创建人**：阿狸咪（代表主人）  
**版本状态**：定版保留，不参与自动备份清理，确保不被新版本覆盖

## ⚠️ 定版说明

此版本为 **定版保留**，用于回滚恢复和版本参照。
- ✅ 可以手动复制回滚到 dist/
- ⛔ 自动化备份/清理流程不得覆盖此目录
- ⛔ 新版本归档请另建目录，避免覆盖此版

## 📦 包含内容

| 目录/文件 | 说明 |
|----------|------|
| `dist/index.html` | 前端主页面（含逻辑详解tab） |
| `dist/index_master.html` | 源页面（含逻辑详解tab） |
| `dist/multi_resonance.html` | 多线共振页 |
| `dist/triple_resonance.html` | 三线共振页 |
| `dist/data/` | 全部数据文件（71个JSON） |
| `scripts/` | 核心Python脚本（16个） |

## 📋 核心特性

- ✅ 逻辑详解 tab 正常显示
- ✅ 打新研判 在 异动停牌观测 上方
- ✅ 全部 Tab（总览、市场异动、AI速览、资金流向、预判信号、宏观观测、历史追踪、逻辑详解）
- ✅ GitHub Pages 部署就绪

## 🔄 回滚步骤

1. 将此目录下的 `dist/` 复制到 `E:\workspace\stock-scanner\dist\`
2. 执行 `cd E:/workspace/stock-scanner && python deploy_now.py --force`
3. 验证 `https://ah-quant999.github.io/quant-scanner-v6/`

## ⛔ 禁止操作

- 禁止直接修改此目录中的任何文件
- 禁止将此目录用作开发目录
- 禁止删除此目录
