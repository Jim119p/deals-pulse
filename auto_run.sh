#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Deals Pulse Pipeline..."
echo "=========================================================="

# 1. 运行 Python 采集并同步数据
cd "$DIR/pipeline"
./venv/bin/python3 run_pipeline.py

# 2. 构建 Astro 静态站点
cd "$DIR/site"
npm run build

echo ">>> Build completed successfully. Static output ready in site/dist/"

# 3. 如果配置了 Git 远程仓库，自动提交并触发 Cloudflare Pages 自动构建
if [ -d "$DIR/.git" ]; then
    cd "$DIR"
    if git remote | grep -q 'origin'; then
        echo ">>> Pushing updates to GitHub..."
        git add site/src/data/deals.json site/src/content/deals/
        git commit -m "chore(auto-update): sync daily deals [$(date '+%Y-%m-%d %H:%M')]" || true
        git push origin main || true
    fi
fi

echo "=========================================================="
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline Finished!"
echo "=========================================================="
