#!/usr/bin/env python3
"""异动停牌观测：A方案（当前停牌）+ B方案（近触发异动预警）"""

import json, os, sys
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT = os.path.join(DATA_DIR, "suspension_alert.json")

def fetch_suspension():
    """A: 获取当前停牌股票列表"""
    try:
        import akshare as ak
        df = ak.stock_tfp_em(date=datetime.now().strftime("%Y%m%d"))
        if df is None or df.empty:
            print("  [停牌] 无数据")
            return []
        results = []
        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            name = str(row.get("名称", "")).strip()
            reason = str(row.get("停牌原因", "")).strip()
            date_str = str(row.get("停牌日期", "")).strip()
            if not code or not name:
                continue
            # 计算停牌天数
            try:
                d = datetime.strptime(date_str, "%Y%m%d")
                days = (datetime.now() - d).days
            except:
                days = 0
            results.append({"code": code, "name": name, "days": days, "reason": reason[:20]})
        print(f"  [停牌] 当前 {len(results)} 只")
        return results
    except Exception as e:
        print(f"  [停牌] 异常: {e}")
        return []

def fetch_near_trigger():
    """B: 扫描金股池中连续涨幅接近触发异的股票（连续3日偏离≥20%触发）"""
    try:
        pool_path = os.path.join(DATA_DIR, "gold_pool.json")
        if not os.path.exists(pool_path):
            return []
        with open(pool_path, "r", encoding="utf-8") as f:
            gp = json.load(f)
        stocks = gp.get("stocks", {})
        alerts = []
        for code, s in stocks.items():
            sources = s.get("sources", [])
            if "三足鼎立" not in sources:
                continue
            chg_20d = s.get("chg_20d", 0)
            chg_5d = s.get("chg_5d", 0)
            # 简单规则：5日涨幅≥15%或20日涨幅≥18% 接近触发
            if chg_5d and chg_5d >= 15:
                gap = max(0, 20 - chg_5d)
                alerts.append({"code": code, "name": s.get("name", ""), "pct": chg_5d, "type": "5日", "gap": round(gap, 1)})
            elif chg_20d and chg_20d >= 18:
                gap = max(0, 20 - chg_20d)
                alerts.append({"code": code, "name": s.get("name", ""), "pct": chg_20d, "type": "20日", "gap": round(gap, 1)})
        # 按偏离度降序
        alerts.sort(key=lambda x: -x["pct"])
        print(f"  [近触发] {len(alerts)} 只")
        return alerts[:5]
    except Exception as e:
        print(f"  [近触发] 异常: {e}")
        return []

def main():
    print("=" * 50)
    print("  异动停牌观测")
    print("=" * 50)

    suspended = fetch_suspension()
    near = fetch_near_trigger()

    result = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "suspended": suspended[:5],
        "near_trigger": near,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 已保存: {OUTPUT}")

if __name__ == "__main__":
    main()
