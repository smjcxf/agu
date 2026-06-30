#!/usr/bin/env python3
"""
sync_check.py — 部署前双机同步检查 + 坚果云冲突清理
确保两台电脑都使用最新代码，防止旧版覆盖新版

用法：
  python sync_check.py          # 检查并同步
  python sync_check.py --force  # 强制 git pull（忽略本地冲突）

集成：在 batch_update.py 所有 deploy 步骤之前调用
"""

import os
import sys
import subprocess
import glob
import json
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ─────────── 关键代码标记（不匹配 = 旧版） ───────────
SAFETY_MARKERS = {
    "index_master.html": [
        "typeof CLOSED_SET !== 'undefined'",  # CLOSED_SET 防御检查
    ],
    "fetch_sector_fund_flow.py": [
        "neodata流入+流出完整",              # neodata 双查询修复
        "流入TOP10",
        "流出TOP10",
    ],
    "generate_triple_resonance_history.py": [
        "scan_result] 刷新:",                # _tracking_latest 价格刷新
    ],
    "update_data_v2.py": [
        "verify_runtime_smoke",              # 运行时冒烟测试
    ],
}


def run(cmd, cwd=None):
    """执行命令并返回 CompletedProcess"""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=cwd or PROJECT_ROOT)


def clean_conflict_files():
    """清理坚果云冲突残余文件"""
    patterns = [
        os.path.join(PROJECT_ROOT, "**", "*冲突*"),
        os.path.join(PROJECT_ROOT, "**", "*conflict*"),
    ]
    cleaned = 0
    for pattern in patterns:
        for f in glob.glob(pattern, recursive=True):
            try:
                os.remove(f)
                print(f"  🧹 清理冲突文件: {os.path.relpath(f, PROJECT_ROOT)}")
                cleaned += 1
            except Exception as e:
                print(f"  ⚠️ 清理失败: {f} ({e})")
    if cleaned:
        print(f"  ✅ 清理了 {cleaned} 个冲突文件")


def check_version_markers():
    """检查关键代码是否包含最新版本的标记"""
    all_ok = True
    for fname, markers in SAFETY_MARKERS.items():
        fpath = os.path.join(PROJECT_ROOT, fname)
        if not os.path.exists(fpath):
            print(f"  ⚠️ {fname} 不存在，跳过检查")
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        missing = [m for m in markers if m not in content]
        if missing:
            all_ok = False
            print(f"  ❌ {fname} 缺少关键代码标记: {missing}")
            print(f"     该文件可能是旧版！坚果云同步可能未完成！")
        else:
            print(f"  ✓ {fname} 版本标记通过")
    return all_ok


def git_sync(force=False):
    """从 GitHub 强制同步最新代码"""
    print("  🔄 从 GitHub 同步最新代码...")
    
    # 先检查是否有未合并文件（合并冲突状态），有则重置
    r_status = run("git status --porcelain")
    if r_status.returncode == 0:
        unmerged = [l for l in r_status.stdout.split('\n') if l[:2] in ('UU', 'AA', 'DD', 'AU', 'UA', 'DU', 'UD')]
        if unmerged:
            print(f"  ⚠️ 检测到未合并文件（合并冲突），执行 git reset --hard origin/main")
            r_reset = run("git reset --hard origin/main")
            if r_reset.returncode != 0:
                print(f"  ❌ git reset --hard 失败: {r_reset.stderr.strip()[:200]}")
                return False
            print(f"  ✓ 已重置到 origin/main，冲突已清理")
            # 重置后直接 pull
            r = run("git pull --rebase origin main")
            if r.returncode != 0:
                err = r.stderr.strip()[:200] if r.stderr else r.stdout.strip()[:200]
                print(f"  ❌ git pull 失败: {err}")
                return False
            print(f"  ✓ 代码已同步")
            return True
    
    # 先 stash 本地修改
    r = run("git stash -u -m 'sync-check-stash'")
    stashed = r.returncode == 0 and "No local changes" not in r.stdout
    
    # git pull
    r = run("git pull --rebase origin main")
    if r.returncode != 0:
        err = r.stderr.strip()[:200] if r.stderr else r.stdout.strip()[:200]
        print(f"  ❌ git pull 失败: {err}")
        if not force:
            if stashed:
                run("git stash pop")
            return False
        print(f"  ⚠️ --force 模式，继续执行")
    
    # 恢复 stash
    if stashed:
        r_pop = run("git stash pop")
        if r_pop.returncode != 0:
            print(f"  ⚠️ git stash pop 有冲突，可能需手动处理")
    
    print(f"  ✓ 代码已同步")
    return True


def check_nutstore_lag():
    """检查坚果云同步延迟：比较本地文件修改时间和 git HEAD 时间"""
    key_files = ["index_master.html", "update_data_v2.py", "deploy_now.py"]
    issues = []
    
    for fname in key_files:
        fpath = os.path.join(PROJECT_ROOT, fname)
        if not os.path.exists(fpath):
            continue
        
        # 本地文件修改时间
        local_mtime = os.path.getmtime(fpath)
        
        # git HEAD 版本时间
        try:
            r = run(f'git log -1 --format="%at" -- {fname}')
            git_mtime = int(r.stdout.strip()) if r.stdout.strip() else 0
        except:
            git_mtime = 0
        
        lag_seconds = local_mtime - git_mtime
        if abs(lag_seconds) > 300:  # 超过5分钟差异
            issues.append(f"{fname}: 本地与git HEAD差 {lag_seconds:.0f}秒")
    
    if issues:
        print(f"  ⚠️ 坚果云可能延迟同步: {issues}")
        return False
    else:
        print(f"  ✓ 关键文件时间戳一致")
        return True


def main():
    force = "--force" in sys.argv
    
    print(f"\n{'='*55}")
    print(f"🔍 部署前同步检查 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")
    
    # 1. 清理冲突文件
    print("\n[1/4] 清理坚果云冲突文件...")
    clean_conflict_files()
    
    # 2. Git 同步
    print("\n[2/4] Git 同步...")
    sync_ok = git_sync(force=force)
    
    # 3. 版本标记检查
    print("\n[3/4] 版本标记检查...")
    version_ok = check_version_markers()
    
    # 4. 坚果云延迟检查
    print("\n[4/4] 坚果云同步检查...")
    nutstore_ok = check_nutstore_lag()
    
    # 汇总
    print(f"\n{'='*55}")
    if sync_ok and version_ok:
        print(f"✅ 同步检查通过，可以安全部署")
        print(f"{'='*55}\n")
        return 0
    else:
        if not sync_ok:
            print(f"❌ Git 同步失败！请手动 git pull 后重试")
        if not version_ok:
            print(f"❌ 关键代码版本标记不匹配！")
            print(f"   可能原因：坚果云未同步最新代码")
            print(f"   解决方法：1) 等坚果云同步完成 2) 手动 git pull")
        print(f"{'='*55}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
