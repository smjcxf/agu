# 阿狸咪 → 小九 交接记录

## 最新版本信息
- **交接时间**: 2026-07-01 23:50
- **最新 commit**: `2c0ee7d`
- **Build**: `20260701234650`
- **已部署**: ✅ gh-pages（GitHub Pages 已更新）

---

## 小九明天晚上跑任务前请确认

### ✅ 自动完成（无需手动操作）
`batch_update.py` 启动时自动执行：
```
git pull --autostash --no-rebase origin main
```
会自动拉取最新代码，包括今晚阿狸咪的所有修改。

### ⚠️ 手动确认（仅需确认一次）
运行 `git log --oneline -3`，输出应包含：
```
2c0ee7d fix: 已过申购日的新股直接不显示...
afb84fe fix: 逻辑详解页泄露二次修复+健康看板缓存问题...
75288e4 fix: 止损公式案例说明...
```
如果看不到这些 commit，说明 git pull 没成功，手动执行：
```bash
cd E:\workspace\stock-scanner
git pull origin main
```

---

## 今晚主要修改内容（小九需了解）

### 1. IPO申购日过滤（renderIpoScore）
- **修改**: `index_master.html` 第452442行附近
- **逻辑**: `if (ad < today) continue;` → 已过申购日的新股完全不显示
- **影响**: 打新研判卡片只显示"今日申购"或未来申购的新股

### 2. 逻辑详解页泄露修复（共2轮，约54处）
- **修改**: `index_master.html` 多处
- **铁律**: 不显示脚本名、数据源名、内部变量名
- **影响**: 逻辑详解页 + 定时任务表格区域

### 3. deploy_now.py 双机覆盖根因修复
- **修改**: `deploy_now.py`
- **关键**: 删除从 origin/main 拉模板的逻辑，避免覆盖本地修改
- **影响**: 小九和阿狸咪互不影响对方的模板修改

### 4. batch_update.py git pull 恢复
- **修改**: `batch_update.py` `_sync_dual_machine_code()`
- **关键**: 恢复 `git pull --autostash --no-rebase origin main`
- **影响**: 小九每次跑任务前自动拉取最新代码

### 5. 止损公式案例说明
- **修改**: `index_master.html` 逻辑详解页
- **内容**: 补充V型反弹股票止损线较宽的案例解释

---

## 双机协作规范（重要！）

| 规则 | 说明 |
|------|------|
| 小九跑时间 | 工作日 19:30-21:00 |
| 阿狸咪跑时间 | 周末/节假日 19:30-21:00 |
| 代码推送 | 修改完立即 commit + push main |
| 部署目标 | gh-pages（deploy_now.py 自动处理）|
| 模板修改 | 任意一方修改 index_master.html 后推 main，另一方自动拉取 |

---

## 故障处理

### 如果小九跑任务时报错
1. 先看 `batch_update.log`（和 batch_update.py 同目录）
2. 确认 git status 是否干净（无未提交修改）
3. 如果模板被覆盖，从 main 重新拉取

### 如果页面显示旧版本
1. 强刷浏览器：Ctrl+Shift+R
2. 确认 GitHub Pages 构建状态（仓库 Settings → Pages）
3. 确认 dist/index.html 的 Build stamp 是否是最新的

---

## 联系人
- 阿狸咪（家里电脑）: 周末/节假日值班
- 小九（单位电脑）: 工作日值班

交接完成 ✅
