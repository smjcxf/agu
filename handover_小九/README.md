# 小九交接 — 九宝量化 v6.0
## 日期：2026-06-16 23:26

### 唯一地址
```
https://ah-quant999.github.io/quant-scanner-v6/
```

### 小九需要做的事

#### 1. 复制交接包到小九
```
从 阿狸咪: E:\workspace\stock-scanner\handover_小九\
到   小九: E:\workspace\stock-scanner\
```

#### 2. 运行一次全量扫描（初始化数据）
```
cd E:/workspace/stock-scanner
python scanner.py full
python generate_recommend.py
python update_triple_resonance_daily.py
python update_data_v2.py
python deploy_now.py --force
```

#### 3. 在小九 WorkBuddy 创建 10 个自动化

| 时间 | 名称 | prompt |
|------|------|--------|
| 09:15 | 九宝量化-盘前更新09:15 | `cd E:/workspace/stock-scanner && python batch_update.py pre_market` |
| 09:45 | 九宝量化-全盘扫描09:45 | `cd E:/workspace/stock-scanner && python batch_update.py morning_scan` |
| 10:00 | 九宝量化-全盘扫描10:00 | `cd E:/workspace/stock-scanner && python batch_update.py morning_scan` |
| 10:30 | 九宝量化-全盘扫描10:30 | `cd E:/workspace/stock-scanner && python batch_update.py morning_scan` |
| 11:45 | 九宝量化-盘中11:45 | `cd E:/workspace/stock-scanner && python batch_update.py morning_report` |
| 13:30 | 九宝量化-盘中13:30 | `cd E:/workspace/stock-scanner && python batch_update.py afternoon` |
| 14:30 | 九宝量化-盘中14:30 | `cd E:/workspace/stock-scanner && python batch_update.py afternoon` |
| 16:30 | 九宝量化-盘中16:30 | `cd E:/workspace/stock-scanner && python batch_update.py afternoon` |
| 19:30 | 九宝量化-收盘后全量更新19:30 | `cd E:/workspace/stock-scanner && python batch_update.py close` |
| 21:00 | 九宝量化-每日自动备份21:00 | `cd E:/workspace/stock-scanner && python batch_update.py backup` |

全部 scheduleType=recurring, status=ACTIVE, cwds=E:/workspace/stock-scanner

### 架构变更（重要）

旧：`&&` 链式调用（一个挂全挂）
新：`batch_update.py` 统一调度（每步独立超时 + 失败重试一次 + 汇总报告）

### 交接包内容
- batch_update.py（核心调度脚本）
- deploy_now.py、update_data_v2.py、update_triple_resonance_daily.py
- scanner.py、generate_recommend.py、guanlan_extractor.py
- fetch_herding_data.py、fetch_lhb.py、fetch_north_fund.py、fetch_main_stock.py
- fetch_market_alerts.py、fetch_sector_fund_flow.py、fetch_concept_ranking.py
- push_notify.py、generate_triple_resonance_history.py、backup_daily.py
