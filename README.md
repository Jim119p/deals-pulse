# ⚡ DealsPulse - 自动化海外好价监控与全球静态站分发系统

> **项目愿景**：基于本地私有算力与全球边缘云网络，构建合规、稳定、零边际成本的 24 小时长期海外数字资产，实现自动化被动收入（Sleep Income）。

---

## 🌐 线上正式环境与仓库

- **全球线上访问地址**: [https://deals-pulse.jimtailor953.workers.dev](https://deals-pulse.jimtailor953.workers.dev)
- **GitHub 源码仓库**: [https://github.com/Jim119p/deals-pulse](https://github.com/Jim119p/deals-pulse)
- **Rocky Linux 虚拟机绝对路径**: `/home/user/deals_engine`

---

## 🏗️ 系统整体技术架构

```
[本地基础设施]
Rocky Linux 虚拟机 (192.168.122.197, 4C4G)
  ├── 1. 定时任务 (Cron 每 6 小时自动唤醒)
  ├── 2. Python 采集器 (抓取欧美主流电商/公开聚合好价数据)
  ├── 3. 数据清洗与结构化 (计算折扣、提取卖点、生成 Markdown/JSON)
  └── 4. 静态生成引擎 (Astro 1.4秒编译 30+ 静态 HTML)
          ↓
[自动化全球分发]
自动 Git Push -> GitHub 仓库 -> 触发 Cloudflare 全球边缘网络 (300+ CDN 节点 Anycast 加速)
          ↓
[全球流量与合规变现]
Google / Bing 搜索爬虫 (索引 Schema.org 绿标富媒体折扣卡片) -> 海外买家访问 -> 官方联盟 CPS 佣金
```

---

## ⚡ 核心启动与关闭命令速查（必读）

系统支持 **后台无人值守自动化**、**手动单次运行** 以及 **本地实时预览** 三种模式，对应的启动与关闭操作如下：

### 1. 24 小时后台自动化任务（Crontab）的启动与关闭
后台每 6 小时自动唤醒一次采集与发布。

- **🟢 开启 / 恢复后台自动运行**：
  ```bash
  (crontab -l 2>/dev/null | grep -v 'auto_run.sh'; echo '0 */6 * * * /bin/bash /home/user/deals_engine/auto_run.sh >> /home/user/deals_engine/pipeline.log 2>&1') | crontab -
  ```
- **🔴 暂停 / 关闭后台自动运行**（暂时不需要机器人打工时使用）：
  ```bash
  crontab -l | grep -v 'auto_run.sh' | crontab -
  ```
- **🔍 检查当前自动化是否处于开启状态**：
  ```bash
  crontab -l
  # 如果输出包含 auto_run.sh，说明正在 24 小时自动运行中；如果为空，说明已关闭
  ```

---

### 2. 手动单次任务的启动与紧急终止
- **🟢 手动启动运行一次完整流水线**（立即抓取最新好价并打包推送到线上）：
  ```bash
  /bin/bash /home/user/deals_engine/auto_run.sh
  ```
- **🔴 紧急强行关闭 / 终止当前正在跑的采集进程**：
  ```bash
  pkill -f run_pipeline.py
  ```

---

### 3. 本地开发预览服务器（Dev Server）的启动与关闭
在 VS Code 编写页面模板时，如果想在浏览器边改边看实时效果：

- **🟢 启动本地实时预览**：
  ```bash
  cd /home/user/deals_engine/site
  npm run dev
  # 启动后会在终端显示本地预览地址 (如 http://localhost:4321)
  ```
- **🔴 关闭本地实时预览**：
  在运行该命令的终端窗口直接按下键盘快捷键：
  ```bash
  Ctrl + C
  ```
  *(或者在后台执行: `pkill -f astro` 彻底关闭)*

---

### 4. 线上网站的公网访问一键开启与关闭（维护模式）
如果网站临时需要改版或维护，不想对外开放：
- **🔴 关闭公网访问**：登录 Cloudflare 后台 -> 进入 `deals-pulse` -> 点击顶部 **【域】** 菜单 -> 将 `workers.dev` 开关切换为 **关闭 (Disabled)**。
- **🟢 恢复公网访问**：再次点击切换为 **打开 (Enabled)**，全球秒级恢复访问。

---

## 🚀 常用操作与运维速查手册

### 1. Mac 终端一键直连服务器
在 Mac 终端任意目录下执行，无需输入密码，直接穿透跳板进入 Rocky Linux：
```bash
ssh rocky-dev
```

### 2. 进入项目主目录
```bash
cd /home/user/deals_engine
```

### 3. 查看后台自动化定时运行日志
系统每 6 小时会自动执行一次采集、生成与代码推送，日志实时记录在：
```bash
# 查看实时日志流
tail -f /home/user/deals_engine/pipeline.log

# 或查看最近 50 行记录
tail -n 50 /home/user/deals_engine/pipeline.log
```

### 4. 手动立即触发一次完整更新
如果想要立刻抓取最新好价并推送到线上：
```bash
/bin/bash /home/user/deals_engine/auto_run.sh
```

### 5. 查看或调整定时任务频率
```bash
# 查看当前定时规则
crontab -l

# 编辑定时规则 (当前默认: 0 */6 * * * 每6小时执行一次)
crontab -e
```

---

## 📂 核心项目结构详解

```text
/home/user/deals_engine/
├── auto_run.sh              # 核心总调度脚本：串联采集、编译与 git push
├── pipeline.log             # 定时任务执行的运行日志
├── package.json             # 根目录 NPM 与 Wrangler 部署配置
├── wrangler.toml            # Cloudflare 全球资产托管绑定配置
├── worker.js                # Cloudflare 边缘极速响应入口
│
├── pipeline/                # Python 自动化采集模块
│   ├── venv/                # 独立的 Python 3.12 虚拟运行环境
│   ├── requirements.txt     # 依赖包列表 (httpx, beautifulsoup4, feedparser 等)
│   ├── collector.py         # 数据采集器 (提取商品图、价格、折扣率、商家、分类)
│   ├── transformer.py       # 数据清洗与 Markdown/JSON 转换器
│   └── run_pipeline.py      # 流水线主执行入口
│
└── site/                    # Astro 现代前端静态站点
    ├── src/
    │   ├── data/deals.json  # 采集落地的全量结构化商品数据库
    │   ├── content/deals/   # 独立生成的 SEO 静态 Markdown 单品文章
    │   ├── components/      # UI 组件 (DealCard.astro 卡片组件)
    │   ├── layouts/         # 页面骨架 (包含 FTC 免责声明与 Google Meta)
    │   └── pages/           # 路由页面 (首页、分类页、单品落地页)
    └── dist/                # 编译打包后的纯静态 HTML 产物 (秒级部署)
```

---

## 🛡️ 欧美市场合规与合法经营守则（核心生命线）

要建立长期存续的数字资产，必须严格恪守以下合规铁律：

### 1. FTC（美国联邦贸易委员会）联盟合规
- **法律依据**：美国联邦法规 `16 CFR Part 255`。
- **强制要求**：任何通过推荐链接获得佣金收益的网站，必须显著向消费者披露利益关系。
- **系统实现**：全站所有页面的 Footer 与详情页均已内置符合 FTC 标准的法律免责声明（FTC Disclosure）。

### 2. Google SEO 链接规范
- **规范要求**：Google 严格禁止未经声明的商业联盟付费链接操纵搜索权重。
- **系统实现**：所有直达商家的购买外链一律强制注入 `rel="noopener noreferrer sponsored"`，合规受 Google 白名单保护。

### 3. 数据采集边界
- **合规依据**：美国公开信息合理使用（Fair Use）原则。
- **系统实现**：采集器仅抓取公开公开的 Syndicated RSS 数据源及公开标价信息，不绕过身份验证、不破解任何反爬校验，完全合法合规。

### 4. 联盟账号防封禁准则（对接官方联盟时必读）
- **严禁自买自刷**：绝对不能通过自己的推广链接下单购买，也不能让同一局域网下的设备下单。
- **严禁私聊直链**：严禁在 Telegram、WhatsApp、邮件等私人沟通渠道直接发送原始推广短链（官方要求必须通过公开网站网页展示与跳转）。
- **标价时效性声明**：本站已内置价格时效性小字提醒（*Prices verified at time of posting, subject to change*），符合亚马逊价格展示规则。

---

## 💰 商业变现（Affiliate）对接操作指南

当网站自然运行 1~2 周、Google 开始逐步建立索引收录后，即可开始接入商业化变现：

1. **申请海外官方联盟账号**：
   - **Amazon Associates** (亚马逊官方联盟，全球品类最全)
   - **Impact.com** (高端数码、户外与品牌独立站联盟)
   - **CJ Affiliate / ShareASale** (成熟大型品牌联盟)
2. **替换专属推广追踪 Tag**：
   - 审核通过后，您将获得专属的联盟 ID（如 `yourtag-20`）。
   - 打开 `/home/user/deals_engine/pipeline/collector.py`，在 `affiliate_url` 字段处拼接您的专属追踪参数。
   - 今后所有抓取生成的购买链接都会自动打上您的佣金追踪代码，产生的每一笔海外订单均自动结算美金到您的账户！
