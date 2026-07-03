"""
盘中扫描统一入口 — 带错误追踪，失败步骤写入 .fetch_errors.json
用法: python run_intraday_scan.py
     python run_intraday_scan.py --skip-standalone   # 跳过独立页面更新
     python run_intraday_scan.py --only-scan          # 只跑数据获取，不更新数据注入和独立页
"""
import subprocess, json, os, sys, time, argparse
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ERROR_FILE = os.path.join(BASE, 'data', '.fetch_errors.json')

STEPS = [
    ('scanner.py watch',      ['python', 'scanner.py', 'watch']),
    ('涨跌家数',               ['python', 'fetch_up_down_stats.py']),
    ('盘中数据NT',             ['python', 'fetch_nt_data.py']),
    ('概念排行',               ['python', 'fetch_concept_ranking.py']),
    ('板块资金',               ['python', 'fetch_sector_fund_flow.py']),
    ('ETF资金',                ['python', 'fetch_etf_flow.py']),
    ('市场快报',               ['python', 'fetch_market_alerts.py']),
]

def run():
    parser = argparse.ArgumentParser(description='盘中数据扫描')
    parser.add_argument('--skip-standalone', action='store_true', help='跳过独立页面更新')
    parser.add_argument('--only-scan', action='store_true', help='只跑数据获取，不更新数据注入和独立页')
    args = parser.parse_args()
    
    errors = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for name, cmd in STEPS:
        print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ▶ {name}...')
        try:
            r = subprocess.run(cmd, cwd=BASE,
                             capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                err_msg = r.stderr.strip()[-200:] if r.stderr else f'exit code {r.returncode}'
                print(f'  ❌ {name} 失败: {err_msg}')
                errors.append({'step': name, 'time': now, 'error': err_msg})
                # 网络错误自动重试一次
                if 'DNS' in err_msg or '502' in err_msg or 'timeout' in err_msg.lower() or 'timed out' in err_msg.lower():
                    print(f'  🔄 网络错误，60秒后重试...')
                    time.sleep(60)
                    r2 = subprocess.run(cmd, cwd=BASE,
                                       capture_output=True, text=True, timeout=300)
                    if r2.returncode == 0:
                        print(f'  ✅ {name} 重试成功')
                        continue
            else:
                print(f'  ✅ {name} 完成')
        except subprocess.TimeoutExpired:
            print(f'  ❌ {name} 超时')
            errors.append({'step': name, 'time': now, 'error': '超时'})
        except Exception as e:
            print(f'  ❌ {name} 异常: {e}')
            errors.append({'step': name, 'time': now, 'error': str(e)[:200]})
    
    # 保存错误记录
    if errors:
        with open(ERROR_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last_scan': now, 'errors': errors}, f, ensure_ascii=False, indent=2)
        print(f'\n⚠️ {len(errors)} 个步骤失败，已记录到 {ERROR_FILE}')
        return 1
    else:
        # 清除之前的错误
        if os.path.exists(ERROR_FILE):
            os.remove(ERROR_FILE)
        print('\n✅ 全部步骤成功')
    
    # 数据获取完成后，更新数据注入 + 独立页面
    if not args.only_scan and not args.skip_standalone:
        print('\n' + '='*50)
        print('▶ 自动更新独立页面并部署')
        print('='*50)
        try:
            r = subprocess.run(
                [sys.executable, 'refresh_standalone_and_deploy.py'],
                cwd=BASE, capture_output=True, text=True, timeout=600
            )
            if r.returncode == 0:
                print('  ✅ 独立页面更新+部署完成')
            else:
                print(f'  ⚠️ 独立页面更新失败: {r.stderr[-200:]}')
                print('  （数据获取已成功，独立页面更新失败不影响主流程）')
        except Exception as e:
            print(f'  ⚠️ 独立页面更新异常: {e}')
    
    return 0

if __name__ == '__main__':
    sys.exit(run())
