# 小红书 CLI 使用指南

> 小红书命令行工具 — 搜索、阅读、互动、发布、数据可视化，全部在终端完成

---

## 快速启动

项目提供两个版本：**Python 交互式终端**和 **Go 命令行工具**，共享同一登录状态。

**Python 版（推荐）**

```python
# 方式一：双击图标「小红书 CLI」直接打开

# 方式二：运行启动脚本
./启动小红书CLI.sh

# 方式三：直接运行 Python
.venv/bin/python xhs_repl.py
```

**Go 版**

```python
# 每次调用直接执行，执行完即退出
./xhs-cli-go/bin/xhs search "武汉美食"
./xhs-cli-go/bin/xhs status
./xhs-cli-go/bin/xhs read abc123
./xhs-cli-go/bin/xhs comments abc123
./xhs-cli-go/bin/xhs user 5f2e123
```

首次打开会自动从 Firefox 浏览器提取登录凭证，无需手动登录。

---

## 两个版本对比

| 特性 | Python 版（交互式 REPL） | Go 版（命令行工具） |
|------|--------------------------|---------------------|
| 启动方式 | `./启动小红书CLI.sh` 或双击桌面图标 | `./xhs-cli-go/bin/xhs <命令>` |
| 交互模式 | 常驻终端，连续操作，自动补全 | 单次执行，适合管道和脚本 |
| 界面风格 | 彩色 Rich 表格、面板、进度条 | 纯文本输出 |
| 搜索 | `search "关键词"` | `xhs search "关键词"` |
| 阅读笔记 | `read 1`（用编号） | `xhs read <笔记ID>` |
| 点赞/收藏 | `like 1` / `favorite 1` | `xhs like <笔记ID>` |
| 数据可视化 | stats / analyze / chart / wordcloud / covers | 无 |
| 浏览器打开 | `open 1` | 无 |
| 主题切换 | `theme ocean` | 无 |
| Cookie 来源 | Firefox 浏览器自动提取 | 共享同一 Cookie 文件 |
| 运行依赖 | Python 3.10+，需 .venv 环境 | 单个静态编译二进制，无依赖 |
| 适用场景 | 日常浏览、数据分析、交互探索 | 自动化脚本、批量操作、定时任务 |

**Python 版 — 日常交互浏览**

```python
xhs >: search "武汉美食"
xhs >: read 3
xhs >: like 3
xhs >: stats
xhs >: analyze
xhs >: open 3
```

**Go 版 — 脚本自动化**

```python
# 批量搜索并保存结果
./xhs-cli-go/bin/xhs search "武汉美食" > results.json

# 检查登录状态
./xhs-cli-go/bin/xhs status

# 定时采集（配合 cron）
0 9 * * * cd /path/to/reds && ./xhs-cli-go/bin/xhs search "今日热点" >> /var/log/xhs.log
```

---

## 核心功能

> 以下命令均在 Python 交互式终端中使用。搜索结果带编号（1、2、3...），后续命令直接用编号代替笔记 ID。

### 搜索与阅读

| 命令 | 说明 | 示例 |
|------|------|------|
| `search "关键词"` | 搜索笔记 | `search "武汉美食"` |
| `read 1` | 阅读第 N 条笔记详情 | `read 3` |
| `comments 1` | 查看笔记评论 | `comments 1` |
| `user <用户ID>` | 查看用户资料 | `user 5f2e123` |
| `user-posts <用户ID>` | 查看用户发布的笔记 | `user-posts 5f2e123` |
| `feed` | 推荐首页 | `feed` |
| `hot` | 热门笔记 | `hot` |
| `topics "话题"` | 搜索话题 | `topics "美食探店"` |
| `search-user "名字"` | 搜索用户 | `search-user "摄影师"` |

### 互动操作

| 命令 | 说明 | 示例 |
|------|------|------|
| `like 1` | 点赞 | `like 1` |
| `like 1 --undo` | 取消点赞 | `like 1 --undo` |
| `favorite 1` | 收藏 | `favorite 1` |
| `unfavorite 1` | 取消收藏 | `unfavorite 1` |
| `comment 1 -c "好看！"` | 发表评论 | `comment 1 -c "写得好"` |
| `reply 1 --comment-id X -c "谢谢"` | 回复评论 | `reply 1 --comment-id abc -c "感谢"` |

### 社交

| 命令 | 说明 |
|------|------|
| `follow <用户ID>` | 关注 |
| `unfollow <用户ID>` | 取消关注 |
| `favorites` | 收藏列表 |
| `likes` | 点赞列表 |

### 创作

| 命令 | 说明 |
|------|------|
| `post --title "标题" --body "正文"` | 发布图文笔记 |
| `delete <笔记ID>` | 删除笔记 |
| `my-notes` | 我的笔记列表 |

### 通知

| 命令 | 说明 |
|------|------|
| `unread` | 未读通知数 |
| `notifications` | 查看通知 |
| `notifications --type likes` | 按类型查看（mentions/likes/connections） |

### 账号

| 命令 | 说明 |
|------|------|
| `status` | 登录状态 |
| `whoami` | 当前用户详情 |
| `login` | 登录（自动提取浏览器 Cookie） |
| `logout` | 退出登录 |

---

## 浏览器打开笔记

```python
xhs > open 1       # 打开搜索结果第 1 条
xhs > open 3       # 打开第 3 条
xhs > open abc123  # 打开指定笔记 ID
```

搜索结果底部会显示完整链接，终端里 **Ctrl + 点击** 也可直接打开。

---

## 数据可视化

搜索完成后，对结果进行数据分析和可视化：

| 命令 | 说明 |
|------|------|
| `stats` | 统计表格（总数/平均点赞/收藏/评论） |
| `analyze` | 关键词分析 + 互动趋势（热度条、作者分布） |
| `chart` | 终端柱状图（点赞/收藏/评论对比） |
| `chart pie` | 终端饼图 |
| `wordcloud` | 生成词云图片（自动在浏览器打开） |
| `covers` | 封面图网格预览 |

所有可视化命令基于**最近一次搜索结果**，每次重新搜索后数据自动更新。

### 可视化示例

以搜索「武汉经开万达」为例，演示完整流程：

**第一步 — 搜索**

```python
xhs >: search "武汉经开万达"
```

| # | 标题 | ❤️ | 类型 | 链接 |
|---|------|-----:|------|------|
| 1 | 汉阳找搭子 | 0 | 📷 | search_result/6a06be88... |
| 2 | 经开万达争点气好吗 | 3 | 📷 | search_result/69dacc30... |
| 3 | 武汉经开万达广场全… | 0 | 📷 | search_result/69defe84... |
| 4 | 武汉经开万达要开manner | 0 | 📷 | search_result/69e372aa... |
| 5 | 经开万达跳舞搭子 | 0 | 📷 | search_result/686b4cf3... |
| ... | ... | ... | ... | ... |

> More results available — use --page to paginate

**第二步 — 数据统计**

```python
xhs >: stats
```

| 指标 | 数值 |
|------|-----:|
| 总笔记数 | 22 |
| 图文笔记 | 19 |
| 视频笔记 | 3 |
| 总点赞 | 663 |
| 总收藏 | 441 |
| 总评论 | 0 |
| 平均点赞 | 30 |
| 平均收藏 | 20 |
| 平均评论 | 0 |

**第三步 — 关键词分析**

```python
xhs >: analyze
```

标题关键词 Top 20：

| 排名 | 关键词 | 出现次数 | 热度 |
|------|--------|--------:|------|
| 1 | 经开 | 8 | ████████████████████ |
| 2 | 万达 | 8 | ████████████████████ |
| 3 | 武汉 | 5 | ████████████ |
| 4 | 搭子 | 2 | █████ |
| 5 | 汉阳 | 1 | ██ |
| 6 | 争点 | 1 | ██ |
| 7 | 广场 | 1 | ██ |
| 8 | 全新 | 1 | ██ |
| 9 | 品牌 | 1 | ██ |
| 10 | manner | 1 | ██ |

作者分布：

| 作者 | 笔记数 |
|------|-------:|
| 武汉经开万达广场 | 6 |
| koi | 1 |
| 好困困zZz | 1 |
| 攒够三十万就辞职的悲催工地牛马 | 1 |
| ilessee_ | 1 |
| 麻辣烫，烫烫 | 1 |
| 空白 | 1 |
| 蔘染 | 1 |
| 野原新之助 | 1 |
| 187的蒜鸟 | 1 |

互动趋势：

| 互动级别 | 数量 | 占比 | 分布 |
|----------|-----:|-----:|------|
| 低互动 | 20 | 90.9% | ███████████████████████████ |
| 中互动 | 2 | 9.1% | ██ |
| 高互动 | 0 | 0.0% | |
| 爆款 | 0 | 0.0% | |

**第四步 — 终端图表**

```python
xhs >: chart
```

![chart](/media/work/Additional3/Agent/OpenCode/home/config/Typora/typora-user-images/image-20260519160739173.png)

> 图表使用 plotext 在终端内直接渲染，无需额外 GUI 依赖。

**第五步 — 词云**

```python
xhs >: wordcloud
# ✓ 词云已生成: exports/wordcloud_xhs_20260519_155611.png
```

![wordcloud](/media/work/Additional3/Agent/OpenCode/home/config/Typora/typora-user-images/image-20260519160501892.png)

---

## 主题切换

| 命令 | 主题 |
|------|------|
| `theme ocean` | 海洋蓝 |
| `theme forest` | 森林绿 |
| `theme sunset` | 日落红 |
| `theme purple` | 紫色 |
| `theme default` | 默认 |

---

## 适合谁用

- **内容创作者** — 搜索热点话题、分析关键词趋势、查看竞品数据
- **数据分析师** — 批量获取笔记数据、生成词云和统计图表
- **运营人员** — 监控热门内容、追踪互动数据、管理收藏和点赞
- **开发者** — 通过 CLI 集成到自动化流程、CI/CD 管道
- **终端爱好者** — 不离开终端完成小红书全部操作

---

## 项目结构

```python
reds/
├── 启动小红书CLI.sh          # 双击启动
├── xhs_repl.py               # 交互式终端（Python）
├── xhs_cli/                  # Python 核心库
│   ├── cli.py                # CLI 入口
│   ├── client.py             # API 客户端
│   ├── client_mixins.py      # API 端点
│   ├── cookies.py            # Cookie 管理
│   ├── signing.py            # 签名
│   ├── formatter_renderers.py# 输出格式化
│   └── commands/             # 命令实现
├── xhs-cli-go/               # Go 版本
│   └── bin/xhs               # Go 编译好的二进制
├── plugins/                  # 可视化插件
│   ├── analyzer.py           # 关键词分析
│   ├── charts.py             # 终端图表
│   ├── export.py             # 导出
│   └── image_preview.py      # 词云/封面图
├── assets/
│   ├── icon.png              # 小红书官方图标
│   └── fonts/                # 中文字体
├── tests/                    # 测试用例（166 个）
└── .venv/                    # Python 虚拟环境
```
