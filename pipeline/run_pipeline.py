"""
Deals Pipeline 总调度器
"""
import sys
from pathlib import Path
from collector import collect_all_deals
from transformer import write_deals_to_astro

def main():
    root_dir = Path(__file__).resolve().parent.parent
    astro_root = root_dir / "site"

    print("=" * 60)
    print(">>> 启动自动化 Deal 采集与数据转化流水线")
    print("=" * 60)

    # 1. 采集数据
    deals = collect_all_deals()
    if not deals:
        print("未抓取到有效数据，使用本地备用优质 Deals 样本...")
        return

    # 2. 转换并注入 Astro 站点
    write_deals_to_astro(deals, astro_root)
    print(">>> 流水线执行成功！数据已同步到 Astro 静态站点。")

if __name__ == "__main__":
    main()
