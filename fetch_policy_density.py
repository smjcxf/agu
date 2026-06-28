#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
政策信号密度 — 可靠数据源版（不依赖neodata）
用法：python fetch_policy_density.py
输出：data/policy_density.json

数据源：akshare stock_info_global_cls() 财联社电报 + 关键词匹配
"""
import json, os, sys, datetime, re

OUT = "data/policy_density.json"

# 政策关键词库（含权重）
POLICY_KEYWORDS = {
    "降准": 3, "降息": 3, "LPR下调": 3, "LPR": 2, "MLF": 2, "逆回购": 1,
    "再贷款": 2, "定向降准": 3, "结构性货币政策": 2,
    "财政赤字": 3, "特别国债": 3, "专项债": 2, "减税降费": 2,
    "转移支付": 1, "消费补贴": 2,
    "产业补贴": 2, "新质生产力": 2, "国产替代": 2, "芯片": 2,
    "新能源": 1, "人工智能": 1, "数据要素": 1,
    "注册制": 2, "退市": 2, "再融资": 1, "并购重组": 1,
    "印花税": 2, "T+0": 2,
    "房贷利率": 2, "限购放松": 2, "保障房": 1,
    "关税": 1, "中美": 1, "制裁": 1,
}

def log(msg): print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def calc_density(content_text):
    """计算政策信号密度"""
    score = 0
    hits = {}
    for kw, weight in POLICY_KEYWORDS.items():
        count = len(re.findall(kw, content_text))
        if count > 0:
            hits[kw] = count * weight
            score += count * weight
    density = min(100, round(score * 3, 1))
    return {
        "density": density,
        "hits": hits,
        "total_score": score,
        "level": "高" if density >= 60 else "中" if density >= 30 else "低"
    }

def main():
    log("政策信号密度抓取 (akshare)...")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    result = {"update_time": now_str, "density": 0, "level": "低", "signals": [],
              "summary": "", "note": "数据源: akshare(财联社电报) + 关键词匹配"}

    try:
        import akshare as ak
        df = ak.stock_info_global_cls()
        if df is None or df.empty:
            result["note"] = "akshare返回空数据"
            log("  ⚠️ 财联社电报返回空")
        else:
            # 取最近50条电报
            recent = df.head(50)
            text_all = " ".join(recent["content"].fillna("").astype(str))
            
            # 计算密度
            density_info = calc_density(text_all)
            result.update(density_info)
            
            # 提取信号
            signals = []
            for _, row in recent.head(20).iterrows():
                content = str(row.get("content", "")).strip()
                if content and len(content) > 5:
                    # 过滤出含政策关键词的
                    has_policy = False
                    for kw in POLICY_KEYWORDS:
                        if kw in content:
                            has_policy = True
                            break
                    if has_policy:
                        signals.append({"event": content[:200]})
            
            result["signals"] = signals[:20]
            result["summary"] = text_all[:2000]
            log(f"  ✓ 密度={result['density']} 级别={result['level']} 信号{len(signals)}条")

    except Exception as e:
        result["note"] = f"akshare查询失败: {e}"
        log(f"  ❌ {e}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"✅ 已保存: {OUT} (密度{result.get('density',0)}, 级别{result.get('level','低')})")

if __name__ == "__main__":
    main()
