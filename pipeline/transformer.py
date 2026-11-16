"""
Transformer: 将结构化 Deals 写入 Astro Content Collection 与 JSON 数据库
"""
import os
import json
import yaml
from pathlib import Path
from typing import List, Dict

def write_deals_to_astro(deals: List[Dict], astro_root: Path):
    content_dir = astro_root / "src" / "content" / "deals"
    data_dir = astro_root / "src" / "data"
    
    content_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. 导出 JSON 全量聚合库
    json_path = data_dir / "deals.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(deals)} deals to {json_path}")

    # 2. 为每个 Deal 生成独立的 Markdown 页面 (用于 SEO 独立收录与 Schema.org 生成)
    for deal in deals:
        md_file = content_dir / f"{deal['slug']}.md"
        
        frontmatter = {
            "title": deal["title"],
            "slug": deal["slug"],
            "deal_price": deal["deal_price"],
            "original_price": deal["original_price"],
            "discount_percent": deal["discount_percent"],
            "merchant": deal["merchant"],
            "category": deal["category"],
            "image_url": deal["image_url"],
            "affiliate_url": deal["affiliate_url"],
            "published_at": deal["published_at"],
            "features": deal["features"],
            "status": deal["status"]
        }

        body = f"""
## Deal Overview

{deal['description']}

### Key Deal Highlights
- **Current Price**: **${deal['deal_price']:.2f}** (Regularly ${deal['original_price']:.2f})
- **Total Savings**: Save **{deal['discount_percent']}%**
- **Available at**: **{deal['merchant']}**
- **Deal Status**: Verified Active

---

*Notice: Prices and inventory change rapidly. As an independent affiliate publisher, we may earn a small commission on qualifying purchases at no additional cost to you.*
"""
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, allow_unicode=True, sort_keys=False)
            f.write("---\n")
            f.write(body)

    print(f"Generated {len(deals)} markdown content pages in {content_dir}")
