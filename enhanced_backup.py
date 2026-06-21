#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ 九宝量化 21:00 审核+备份增强脚本
=============================================
流程：
  【🔴 最优先】双机代码同步 (git pull/push)
  【📊 审计1】历史追踪日历正确性
  【📊 审计2】新前端定时任务覆盖检查
  【📊 审计3】宏观观测指标完整性
  【📊 审计4】逻辑详解页完整性
  【📊 审计5】全网无关联文件清理
  【💾 备份】执行增量+快照备份

🎯 核心原则：任何审计项不通过 → WARNING输出 → 但不阻断备份
   备份永远执行（数据保护优先），审计报告供次日修正参考
"""

import os, sys, json, re, datetime, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data')
DIST_DIR = os.path.join(BASE, 'dist')
TODAY = datetime.datetime.now().strftime('%Y%m%d')
TODAY_DATE = datetime.datetime.now().strftime('%Y-%m-%d')

# ═══════════════════════════════════════════════════════════
# 🔴 0. 双机代码同步（最重要，必须放最前）
# ═══════════════════════════════════════════════════════════
def sync_dual_machine():
    """阿狸咪↔小九 代码同步"""
    print("=" * 60)
    print("🔴 步骤0: 双机代码同步")
    print("=" * 60)
    
    issues = []
    try:
        # 1. 暂存本地修改
        r = subprocess.run(['git', 'add', '-A'], cwd=BASE, capture_output=True, text=True, timeout=30)
        print("  ✓ git add -A")
        
        # 2. 检查是否有改动需要提交
        r = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=BASE, timeout=30)
        has_changes = r.returncode != 0
        
        if has_changes:
            commit_msg = f"auto: 审核备份前提交 ({TODAY_DATE})"
            r = subprocess.run(['git', 'commit', '-m', commit_msg], cwd=BASE, capture_output=True, text=True, timeout=30)
            print(f"  ✓ git commit: {r.stdout.strip()[:80]}")
        else:
            print("  - 无本地改动，跳过commit")
        
        # 3. 拉取远程更新（小九可能有推送）
        r = subprocess.run(['git', 'pull', '--rebase', 'origin', 'main'], cwd=BASE, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"  ⚠ git pull 失败: {r.stderr.strip()[:100]}")
            issues.append("git pull 失败")
        else:
            pulled = 'Already up to date' not in r.stdout
            print(f"  {'✓' if pulled else '-'} git pull origin main")
        
        # 4. 推送本地改动
        r = subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f"  ⚠ git push 失败: {r.stderr.strip()[:100]}")
            issues.append("git push 失败")
        else:
            print(f"  ✓ git push origin main")
        
    except subprocess.TimeoutExpired:
        print("  ✗ git 操作超时")
        issues.append("git 操作超时")
    except Exception as e:
        print(f"  ✗ git 异常: {e}")
        issues.append(f"git 异常: {e}")
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 1. 历史追踪日历正确性审计
# ═══════════════════════════════════════════════════════════
def audit_history_calendar():
    """检查 triple_resonance_history.json 日期+假期+数据一致性"""
    print("\n" + "=" * 60)
    print("📊 审计1: 历史追踪日历正确性")
    print("=" * 60)
    
    issues = []
    
    # 1a. 假期列表正确性
    holidays_2026 = {
        '2026-01-01', '2026-01-02',              # 元旦
        '2026-01-28', '2026-01-29', '2026-01-30',  # 春节
        '2026-02-03', '2026-02-04',
        '2026-04-06',                              # 清明
        '2026-05-01', '2026-05-04', '2026-05-05',  # 劳动节
        '2026-06-19',                              # 端午（仅周五，6/22不调休）
        '2026-10-01', '2026-10-02', '2026-10-03',  # 国庆
        '2026-10-06', '2026-10-07',
    }
    
    def is_trading_day(d):
        if d in holidays_2026:
            return False
        dt = datetime.datetime.strptime(d, '%Y-%m-%d')
        return dt.weekday() < 5  # 周一到周五
    
    # 1b. 检查历史数据文件
    json_path = os.path.join(DATA_DIR, 'triple_resonance_history.json')
    if not os.path.exists(json_path):
        issues.append("triple_resonance_history.json 不存在")
        return issues
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        dates = sorted(data.keys())
        total_entries = sum(len(v) for v in data.values())
        print(f"  历史数据: {len(dates)} 天, {total_entries} 条记录")
        
        non_trading_dates = []
        for d in dates:
            if not is_trading_day(d):
                non_trading_dates.append(d)
        if non_trading_dates:
            print(f"  ✗ {len(non_trading_dates)} 个非交易日有数据: {non_trading_dates}")
            issues.append(f"非交易日数据: {non_trading_dates}")
        else:
            print(f"  ✓ 所有日期均为交易日")
        
        # 1c. 检查 enter_date/duration_days 完整性
        empty_enter = 0
        empty_dur = 0
        for d in dates:
            for s in data[d]:
                if not s.get('enter_date'): empty_enter += 1
                if not s.get('duration_days'): empty_dur += 1
        
        if empty_enter:
            print(f"  ✗ {empty_enter} 条 enter_date 为空")
            issues.append(f"{empty_enter}条enter_date为空")
        else:
            print(f"  ✓ enter_date 全部填写")
        
        if empty_dur:
            print(f"  ✗ {empty_dur} 条 duration_days 为空")
            issues.append(f"{empty_dur}条duration_days为空")
        else:
            print(f"  ✓ duration_days 全部填写")
        
        # 1d. 检查最近日期是否合理
        if dates:
            last = dates[-1]
            days_ago = (datetime.datetime.now() - datetime.datetime.strptime(last, '%Y-%m-%d')).days
            print(f"  最新日期: {last} ({days_ago}天前)")
        
    except Exception as e:
        print(f"  ✗ JSON解析失败: {e}")
        issues.append(f"JSON解析失败: {e}")
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 2. 新前端定时任务覆盖检查
# ═══════════════════════════════════════════════════════════
def audit_frontend_task_coverage():
    """检查 batch_update.py close 模式是否覆盖所有数据源"""
    print("\n" + "=" * 60)
    print("📊 审计2: 前端定时任务覆盖检查")
    print("=" * 60)
    
    issues = []
    
    # 前端数据源 → fetch脚本映射
    required = {
        'SCAN_DATA':        'scanner.py full',
        'WATCH_DATA':       'scanner.py full',
        'GOLD_POOL':        'scanner.py full',
        'STOCK_LIST':       'scanner.py full (内置)',
        'RECOMMEND':        'generate_recommend.py',
        'SH_FIB':           'fetch_sh_index_fib.py',
        'SZ_FIB':           'fetch_sh_index_fib.py',
        'SECTOR_FUND_FLOW': 'fetch_sector_fund_flow.py',
        'SH_SZ_HISTORY':    'fetch_sh_sz_history.py',
        'NT_DATA':          'fetch_nt_data.py',
        'CONCEPT_RANKING':  'fetch_concept_ranking.py',
        'MARKET_ALERTS':    'fetch_market_alerts.py',
        'MARGIN_DATA':      'fetch_margin.py',
        'ETF_SUBSCRIPTION': 'fetch_margin_etf.py',
        'MACRO_DATA':       'fetch_macro_data.py',
        'HERRING_DATA':     'fetch_herding_data.py',
        'LHB_DATA':         'fetch_lhb.py',
        'MAIN_STOCK':       'fetch_main_stock.py',
        'MAIN_WEEK':        'fetch_main_week.py',
        'NORTH_FUND':       'fetch_north_fund.py',
        'MAHORO_COVERAGE':  'fetch_mahoro_signals.py',
        'SUSPENSION_ALERT': 'fetch_suspension_alert.py',
        'STOCK_DEVIATION':  'fetch_stock_deviation.py',
        'FOMC_SUMMARY':     '(手动维护)',
        'RESONANCE_HISTORY':'update_triple_resonance_daily.py',
    }
    
    # 检查 batch_update.py close 模式
    batch_path = os.path.join(BASE, 'batch_update.py')
    if not os.path.exists(batch_path):
        issues.append("batch_update.py 不存在")
        return issues
    
    try:
        with open(batch_path, 'r', encoding='utf-8') as f:
            batch_content = f.read()
        
        missing = []
        for block, script in required.items():
            if script == '(手动维护)' or script == 'scanner.py full (内置)':
                continue
            if script.replace('.py', '') not in batch_content:
                missing.append(f"{block} → {script}")
        
        if missing:
            print(f"  ✗ {len(missing)} 个未在 batch_update close 中:")
            for m in missing:
                print(f"    - {m}")
            issues.extend(missing)
        else:
            print(f"  ✓ batch_update close 覆盖全部 {len(required)-1} 个数据源")
        
        # 额外检查：margin_data 写入冲突
        if 'fetch_margin.py' in batch_content and 'fetch_margin_etf.py' in batch_content:
            # 检查 fetch_margin_etf.py 是否仍然写 margin_data.json
            etf_path = os.path.join(BASE, 'fetch_margin_etf.py')
            if os.path.exists(etf_path):
                with open(etf_path, 'r', encoding='utf-8') as f:
                    etf_content = f.read()
                if 'margin_data.json' in etf_content and 'etf_subscription.json' in etf_content:
                    if 'fetch_margin_data' in etf_content:
                        issues.append("⚠ fetch_margin_etf.py 仍在写 margin_data.json（应已修复）")
                        print(f"  ✗ fetch_margin_etf.py 仍写 margin_data.json！")
                else:
                    print(f"  ✓ fetch_margin_etf.py 已正确（不再写margin_data.json）")
        
    except Exception as e:
        print(f"  ✗ batch_update 检查异常: {e}")
        issues.append(str(e))
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 3. 宏观观测指标完整性
# ═══════════════════════════════════════════════════════════
def audit_macro_data():
    """检查 macro_data.json 是否包含所有22项指标"""
    print("\n" + "=" * 60)
    print("📊 审计3: 宏观观测指标完整性")
    print("=" * 60)
    
    issues = []
    
    macro_path = os.path.join(DATA_DIR, 'macro_data.json')
    if not os.path.exists(macro_path):
        issues.append("macro_data.json 不存在")
        return issues
    
    try:
        with open(macro_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_keys = {
            'monetary': ['cn_bond_10y', 'us_bond_10y', 'cn_us_spread', 'lpr', 'shibor', 'm2_yoy', 'open_market_operation'],
            'global_macro': ['vix', 'dxy', 'usdcnh'],
            'global_macro.commodities': ['gold', 'silver', 'copper', 'oil', 'bitcoin'],
            'market_sentiment': ['new_investors'],
            'economy': ['pmi', 'cpi', 'ppi', 'social_financing', 'export_yoy', 'ipo'],
        }
        
        missing = []
        stale = []
        
        for section, keys in required_keys.items():
            if '.' in section:
                parent, child = section.split('.')
                section_data = data.get(parent, {}).get(child, {})
            else:
                section_data = data.get(section, {})
            
            for key in keys:
                if key not in section_data:
                    missing.append(f"{section}.{key}")
        
        # 检查数据新鲜度
        for key in required_keys.get('monetary', []):
            if key in data.get('monetary', {}) and data['monetary'][key]:
                v = data['monetary'][key]
                if isinstance(v, dict) and v.get('value') is None:
                    stale.append(f"monetary.{key} 值为None")
        
        if missing:
            missing_msg = f"缺失 {len(missing)} 项: {', '.join(missing)}"
            issues.append(missing_msg)
            print(f"  ✗ {missing_msg}")
        else:
            print(f"  ✓ 全部 22 项指标数据完整")
        
        if stale:
            print(f"  ⚠ 数据过期: {', '.join(stale)}")
            issues.extend(stale)
        
        # 检查日期
        update_time = data.get('update_time', '')
        print(f"  数据更新时间: {update_time}")
        
    except Exception as e:
        print(f"  ✗ macro_data 检查异常: {e}")
        issues.append(str(e))
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 4. 逻辑详解页完整性
# ═══════════════════════════════════════════════════════════
def audit_logic_guide():
    """检查逻辑详解页是否包含所有必要章节"""
    print("\n" + "=" * 60)
    print("📊 审计4: 逻辑详解页完整性")
    print("=" * 60)
    
    issues = []
    
    html_path = os.path.join(BASE, 'index_master.html')
    if not os.path.exists(html_path):
        html_path = os.path.join(DIST_DIR, 'index.html')
    if not os.path.exists(html_path):
        issues.append("找不到 index_master.html")
        return issues
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        required_sections = [
            ('🔴 铁律', '铁律'),
            ('📋 总览页', '总览页'),
            ('📈 数据监控', '数据监控'),
            ('🔮 预判信号', '预判信号'),
            ('🎯 选股核心信号', '选股核心信号'),
            ('📊 金股池构成', '金股池构成'),
            ('🏅 基础评分规则', '基础评分规则'),
            ('🏅 增强评分因子', '增强评分因子'),
            ('🔍 个股查询评分', '个股查询评分'),
            ('📦 个股查询扩展信息', '个股查询扩展信息'),
            ('⭐ 自选复盘', '自选复盘'),
        ]
        
        missing = []
        for title, keyword in required_sections:
            if keyword not in html:
                missing.append(title)
        
        if missing:
            print(f"  ✗ 缺失章节: {', '.join(missing)}")
            issues.extend([f"逻辑详解缺少: {m}" for m in missing])
        else:
            print(f"  ✓ 全部 {len(required_sections)} 个章节完整")
        
    except Exception as e:
        print(f"  ✗ 逻辑详解检查异常: {e}")
        issues.append(str(e))
    
    return issues


# ═══════════════════════════════════════════════════════════
# 📊 5. 全网无关联文件清理
# ═══════════════════════════════════════════════════════════
def cleanup_orphan_files():
    """清理临时文件、空文件、重复数据"""
    print("\n" + "=" * 60)
    print("📊 审计5: 全网无关联文件清理")
    print("=" * 60)
    
    issues = []
    deleted = []
    
    # 已知的无关联文件/临时文件
    known_orphans = [
        '.enhance_log.txt',
        'concept_history.json',
        'stock_sector_cache.json',
        'zsxq_selenium_snapshot.txt',
    ]
    
    for fname in known_orphans:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
                deleted.append(f"data/{fname}")
            except Exception as e:
                issues.append(f"无法删除 {fname}: {e}")
        
        # 同时检查 dist/data
        dpath = os.path.join(DIST_DIR, 'data', fname)
        if os.path.exists(dpath):
            try:
                os.remove(dpath)
                deleted.append(f"dist/data/{fname}")
            except:
                pass
    
    # 清理空 backup 目录
    for item in os.listdir(BASE):
        item_path = os.path.join(BASE, item)
        if os.path.isdir(item_path) and item.startswith('backup_'):
            try:
                contents = os.listdir(item_path)
                if not contents:
                    os.rmdir(item_path)
                    deleted.append(item)
            except:
                pass
    
    if deleted:
        print(f"  ✓ 已删除 {len(deleted)} 个文件: {', '.join(deleted)}")
    else:
        print(f"  ✓ 无需要清理的文件")
    
    if issues:
        print(f"  ✗ 清理问题: {issues}")
    
    return issues


# ═══════════════════════════════════════════════════════════
# 💾 6. 备份（原 backup_daily.py 逻辑增强）
# ═══════════════════════════════════════════════════════════
def perform_backup():
    """执行完整备份"""
    print("\n" + "=" * 60)
    print("💾 步骤6: 执行备份")
    print("=" * 60)
    
    issues = []
    backup_dir = os.path.join(BASE, f'backup_{TODAY}')
    
    try:
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
        
        # 备份 dist/index_master.html
        src = os.path.join(DIST_DIR, 'index_master.html')
        if os.path.exists(src):
            shutil.copy2(src, backup_dir)
            print(f"  ✓ dist/index_master.html")
        else:
            print(f"  ⚠ dist/index_master.html 不存在")
            issues.append("dist/index_master.html 不存在")
        
        # 备份 data/ 目录
        data_src = os.path.join(BASE, 'data')
        data_dst = os.path.join(backup_dir, 'data')
        if os.path.exists(data_src):
            shutil.copytree(data_src, data_dst)
            file_count = sum(1 for _ in os.listdir(data_dst))
            print(f"  ✓ data/ ({file_count} 文件)")
        
        # 备份所有 .py 脚本
        py_count = 0
        for f in os.listdir(BASE):
            if f.endswith('.py'):
                shutil.copy2(os.path.join(BASE, f), backup_dir)
                py_count += 1
        print(f"  ✓ {py_count} 个 .py 脚本")
        
        # 计算大小
        size = sum(os.path.getsize(os.path.join(dp, f)) 
                   for dp, _, fn in os.walk(backup_dir) for f in fn)
        print(f"  ✅ 备份完成: {backup_dir} ({size/1024/1024:.1f}MB)")
        
        # 清理 7 天前的旧备份
        cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
        for item in os.listdir(BASE):
            item_path = os.path.join(BASE, item)
            if not os.path.isdir(item_path):
                continue
            m = re.match(r'backup_(\d{8})$', item)
            if not m:
                continue
            try:
                d = datetime.datetime.strptime(m.group(1), '%Y%m%d')
                if d < cutoff:
                    shutil.rmtree(item_path)
                    print(f"  🗑️  已删除过期日备: {item}")
            except:
                pass
        
    except Exception as e:
        print(f"  ✗ 备份失败: {e}")
        issues.append(f"备份异常: {e}")
    
    return issues


# ═══════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════
def main():
    print("⚡ 九宝量化 21:00 审核+备份")
    print(f"   日期: {TODAY_DATE}")
    print(f"   路径: {BASE}")
    print()
    
    all_issues = {}
    
    # 🔴 最优先：双机同步
    all_issues['双机同步'] = sync_dual_machine()
    
    # 📊 审计1：历史追踪日历
    all_issues['历史追踪日历'] = audit_history_calendar()
    
    # 📊 审计2：定时任务覆盖
    all_issues['定时任务覆盖'] = audit_frontend_task_coverage()
    
    # 📊 审计3：宏观观测
    all_issues['宏观观测'] = audit_macro_data()
    
    # 📊 审计4：逻辑详解页
    all_issues['逻辑详解页'] = audit_logic_guide()
    
    # 📊 审计5：清理
    all_issues['文件清理'] = cleanup_orphan_files()
    
    # 💾 备份
    all_issues['备份'] = perform_backup()
    
    # ═══ 汇总报告 ═══
    print("\n" + "=" * 60)
    print("📋 审核汇总报告")
    print("=" * 60)
    
    total_errors = 0
    total_warnings = 0
    
    for section, issues in all_issues.items():
        count = len(issues)
        icon = '✗' if count > 0 else '✓'
        status = f'{count} 个问题' if count > 0 else '通过'
        print(f"  {icon} {section}: {status}")
        total_errors += count
    
    print(f"\n  总计: {total_errors} 个问题需要关注")
    
    # 生成审计报告文件
    report_path = os.path.join(DATA_DIR, 'audit_summary.json')
    report = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_issues': total_errors,
        'details': {k: v for k, v in all_issues.items() if v},
        'backup_path': os.path.join(BASE, f'backup_{TODAY}'),
    }
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"  📁 审计报告: {report_path}")
    
    if total_errors > 0:
        print(f"\n⚠️  有 {total_errors} 个问题需人工关注，备份已完成不受影响")
    else:
        print(f"\n✅ 全部审核通过，备份完成")

if __name__ == '__main__':
    main()
