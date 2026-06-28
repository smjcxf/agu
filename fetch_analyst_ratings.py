#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析师评级转向 — 可靠数据源版（不依赖neodata）
用法：python fetch_analyst_ratings.py
输出：data/analyst_ratings.json

数据源：akshare stock_research_report_em() 东方财富研报数据
"""
import json, os, sys, datetime, time as _time
import requests as req

OUT = "data/analyst_ratings.json"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def log(msg): print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    log("分析师评级抓取 (akshare)...")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    result = {"update_time": now_str, "upgrades": [], "downgrades": [], "new_coverage": [],
              "hot_stocks": [], "note": "数据源: akshare(东方财富研报)"}

    try:
        import akshare as ak
        import pandas as pd

        # 获取金股池活跃股票代码（top30）
        codes = []
        gp_path = os.path.join(DATA_DIR, "gold_pool.json")
        if os.path.exists(gp_path):
            with open(gp_path, 'r', encoding='utf-8') as f:
                gp = json.load(f)
            stocks = gp.get("stocks", {}) if isinstance(gp, dict) else {}
            # 取最近入池的30只
            sorted_stocks = sorted(stocks.items(), key=lambda x: x[1].get("entry_date", ""), reverse=True)
            codes = [s[0] for s in sorted_stocks[:30]]
            log(f"  金股池获取到 {len(codes)} 只候选")

        if not codes:
            codes = ["000001", "000002", "000858", "002415", "300750", "600519", "601318"]  # 兜底
            log(f"  使用兜底股票列表 {len(codes)} 只")

        # 逐只查询研报数据
        hot_stocks = []
        for code in codes:
            try:
                df = ak.stock_research_report_em(symbol=code)
                if df is None or df.empty:
                    continue
                # 取最近3个月研报
                if "评级日期" in df.columns:
                    df["评级日期"] = pd.to_datetime(df["评级日期"], errors="coerce")
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
                    df = df[df["评级日期"] >= cutoff]
                if df.empty:
                    continue
                row = df.iloc[0]
                rating = str(row.get("东财评级", "") or row.get("评级", ""))
                inst = str(row.get("机构", ""))
                report_count = len(df)
                if rating:
                    hot_stocks.append({
                        "code": code,
                        "name": str(row.get("股票简称", "")),
                        "rating": rating,
                        "institution": inst,
                        "report_count_3m": report_count,
                    })
                if len(hot_stocks) >= 20:
                    break
            except Exception as e:
                pass  # 单只失败不影响整体
            _time.sleep(0.3)

        result["hot_stocks"] = hot_stocks
        log(f"  ✓ 获取到 {len(hot_stocks)} 只有效研报数据")

    except Exception as e:
        result["note"] = f"akshare查询失败: {e}"
        log(f"  ❌ {e}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"✅ 已保存: {OUT} (热点{len(result['hot_stocks'])}只)")

if __name__ == "__main__":
    main()
