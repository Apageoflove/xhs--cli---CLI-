# xhs CLI 使用指南

## 快速开始

```bash
# 先进入项目目录
cd /media/work/Additional3/Agent/reds

# ★ 推荐：交互式终端（类似 Claude Code 的 REPL 界面）
./xhs.sh

# 单条命令模式 - Python 版
./xhs-py.sh <命令>

# 单条命令模式 - Go 版
./xhs-go.sh <命令>
```

## 交互式终端

运行 `./xhs.sh` 进入交互模式，支持：

| 命令 | 说明 |
|------|------|
| `search "美食"` | 搜索笔记（结果带表格） |
| `read 1` | 读取第1条搜索结果 |
| `comments 1` | 查看第1条的评论 |
| `like 1` | 给第1条点赞 |
| `hot -c travel` | 查看旅行热门 |
| `whoami` | 查看当前用户 |
| `help` | 查看所有命令 |
| `theme ocean` | 切换主题颜色 |
| `background 图片路径` | 设置终端背景图 |
| `clear` | 清屏 |
| `exit` | 退出 |

主题可选：`default` / `ocean` / `forest` / `sunset` / `purple`

> 也可以用完整路径，不用 cd：
> ```bash
> /media/work/Additional3/Agent/reds/xhs-py.sh <命令>
> /media/work/Additional3/Agent/reds/xhs-go.sh <命令>
> ```

## 第一步：登录

```bash
# Python 版 — 自动从浏览器提取 cookie
./xhs-py.sh login

# Python 版 — 扫码登录
./xhs-py.sh login --qrcode

# Go 版 — 手动输入 cookie
./xhs-go.sh login

# Go 版 — 从 JSON 文件导入 cookie
./xhs-go.sh import-cookies -f cookies.json

# 检查登录状态
./xhs-py.sh status        # 或 ./xhs-go.sh status
```

登录成功后两个版本共享 cookie，只需登录一次。

---

## 全部命令对比表

### 认证 (Auth)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `login` | ✅ 自动提取浏览器cookie | ✅ 手动输入cookie | 登录 | `xhs login` |
| `login --qrcode` | ✅ 扫码登录 | ❌ 不支持 | 二维码登录 | `xhs login --qrcode` |
| `status` | ✅ | ✅ | 检查登录状态 | `xhs status` |
| `whoami` | ✅ | ✅ | 查看当前用户详情 | `xhs whoami` |
| `logout` | ✅ | ✅ | 退出登录 | `xhs logout` |
| `import-cookies -f FILE` | ❌ 不需要 | ✅ Go独有 | 从JSON文件导入cookie | `xhs import-cookies -f cookies.json` |

### 搜索 (Search)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `search "关键词"` | ✅ | ✅ | 搜索笔记 | `xhs search "美食"` |
| `search "关键词" --sort popular` | ✅ | ✅ | 按热度排序 | `xhs search "旅行" --sort popular` |
| `search "关键词" --sort latest` | ✅ | ✅ | 按最新排序 | `xhs search "穿搭" --sort latest` |
| `search "关键词" --type video` | ✅ | ✅ | 只搜视频 | `xhs search "AI" --type video` |
| `search "关键词" --type image` | ✅ | ✅ | 只搜图片 | `xhs search "猫咪" --type image` |
| `search "关键词" --page 2` | ✅ | ✅ | 翻页 | `xhs search "美食" --page 2` |
| `search-user "用户名"` | ✅ | ✅ | 搜索用户 | `xhs search-user "摄影师"` |
| `topics "关键词"` | ✅ | ✅ | 搜索话题/标签 | `xhs topics "美食探店"` |

### 阅读 (Reading)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `read <笔记ID>` | ✅ | ✅ | 读取笔记详情 | `xhs read abc123` |
| `read 1` | ✅ | ✅ | 读取上次搜索的第1条 | `xhs read 1` |
| `read "https://...xsec_token=xxx"` | ✅ | ✅ | 通过URL读取笔记 | `xhs read "https://www.xiaohongshu.com/explore/xxx?xsec_token=yyy"` |
| `read <ID> --xsec-token TOKEN` | ✅ | ✅ | 指定token读取 | `xhs read abc123 --xsec-token xxx` |
| `comments <笔记ID>` | ✅ | ✅ | 查看评论 | `xhs comments abc123` |
| `comments 1` | ✅ | ✅ | 查看第1条结果的评论 | `xhs comments 1` |
| `comments <ID> --all` | ✅ | ✅ | 获取全部评论(自动翻页) | `xhs comments abc123 --all` |
| `comments <ID> --xsec-token T` | ✅ | ✅ | 指定token查看评论 | `xhs comments abc123 --xsec-token xxx` |
| `sub-comments <笔记ID> <评论ID>` | ✅ | ✅ | 查看评论的回复 | `xhs sub-comments abc123 cmt456` |
| `user <用户ID>` | ✅ | ✅ | 查看用户资料 | `xhs user 5f2e123` |
| `user-posts <用户ID>` | ✅ | ✅ | 查看用户发布的笔记 | `xhs user-posts 5f2e123` |
| `user-posts <用户ID> --cursor X` | ✅ | ✅ | 翻页 | `xhs user-posts 5f2e123 --cursor xxx` |
| `feed` | ✅ | ✅ | 推荐首页 | `xhs feed` |
| `hot` | ✅ | ✅ | 热门笔记(默认美食) | `xhs hot` |
| `hot -c fashion` | ✅ | ✅ | 指定分类看热门 | `xhs hot -c fashion` |
| `my-notes` | ✅ | ✅ | 我的笔记列表 | `xhs my-notes` |
| `my-notes --page 1` | ✅ | ✅ | 翻页 | `xhs my-notes --page 1` |

### 互动 (Interactions)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `like <笔记ID>` | ✅ | ✅ | 点赞 | `xhs like abc123` |
| `like 1` | ✅ | ✅ | 给第1条结果点赞 | `xhs like 1` |
| `like <ID> --undo` | ✅ | ✅ | 取消点赞 | `xhs like abc123 --undo` |
| `favorite <笔记ID>` | ✅ | ✅ | 收藏 | `xhs favorite abc123` |
| `favorite 1` | ✅ | ✅ | 收藏第1条结果 | `xhs favorite 1` |
| `unfavorite <笔记ID>` | ✅ | ✅ | 取消收藏 | `xhs unfavorite abc123` |
| `unfavorite 1` | ✅ | ✅ | 取消收藏第1条 | `xhs unfavorite 1` |
| `comment <ID> -c "内容"` | ✅ | ✅ | 发表评论 | `xhs comment abc123 -c "好看！"` |
| `comment 1 -c "内容"` | ✅ | ✅ | 评论第1条结果 | `xhs comment 1 -c "收藏了"` |
| `reply <ID> --comment-id X -c "内容"` | ✅ | ✅ | 回复评论 | `xhs reply abc123 --comment-id cmt456 -c "谢谢"` |
| `delete-comment <笔记ID> <评论ID>` | ✅ | ✅ | 删除评论 | `xhs delete-comment abc123 cmt456` |
| `delete-comment ... -y` | ✅ | ✅ | 跳过确认删除 | `xhs delete-comment abc123 cmt456 -y` |

### 社交 (Social)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `follow <用户ID>` | ✅ | ✅ | 关注用户 | `xhs follow 5f2e123` |
| `unfollow <用户ID>` | ✅ | ✅ | 取消关注 | `xhs unfollow 5f2e123` |
| `favorites` | ✅ | ✅ | 我的收藏列表 | `xhs favorites` |
| `favorites <用户ID>` | ✅ | ✅ | 查看他人的收藏 | `xhs favorites 5f2e123` |
| `likes` | ✅ | ✅ | 我点赞过的笔记 | `xhs likes` |
| `likes <用户ID>` | ✅ | ✅ | 查看他人的点赞 | `xhs likes 5f2e123` |

### 创作 (Creator)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `post --title "标题" --body "正文"` | ✅ | ❌ 暂不可用 | 发布笔记 | `xhs post --title "测试" --body "内容"` |
| `post ... --images img.png` | ✅ | ❌ 暂不可用 | 带图片发布 | `xhs post --title "标题" --body "内容" --images 1.jpg` |
| `delete <笔记ID>` | ✅ | ✅ | 删除笔记 | `xhs delete abc123` |
| `delete <笔记ID> -y` | ✅ | ✅ | 跳过确认删除 | `xhs delete abc123 -y` |

### 通知 (Notifications)

| 命令 | Python | Go | 说明 | 示例 |
|------|--------|-----|------|------|
| `unread` | ✅ | ✅ | 未读通知数量 | `xhs unread` |
| `notifications` | ✅ | ✅ | 查看@和评论通知 | `xhs notifications` |
| `notifications --type likes` | ✅ | ✅ | 查看赞和收藏通知 | `xhs notifications --type likes` |
| `notifications --type connections` | ✅ | ✅ | 查看新增关注通知 | `xhs notifications --type connections` |

---

## 输出格式

所有命令都支持以下输出选项：

```bash
xhs search "美食"              # 终端彩色输出（默认）
xhs search "美食" --json       # JSON 格式
xhs search "美食" --yaml       # YAML 格式
```

也可以用环境变量：

```bash
OUTPUT=json xhs search "美食"   # 全局 JSON 输出
OUTPUT=yaml xhs search "美食"   # 全局 YAML 输出
```

---

## 典型使用流程

```bash
cd /media/work/Additional3/Agent/reds

# 1. 登录（Python版推荐，可自动提取浏览器cookie）
./xhs-py.sh login

# 2. 搜索
./xhs-py.sh search "成都美食"
# 或 Go 版
./xhs-go.sh search "成都美食"

# 3. 读取第1条搜索结果
./xhs-py.sh read 1

# 4. 查看第1条的评论
./xhs-py.sh comments 1

# 5. 点赞第1条
./xhs-py.sh like 1

# 6. 收藏第1条
./xhs-py.sh favorite 1

# 7. 给第1条评论
./xhs-py.sh comment 1 -c "收藏了！"

# 8. 查看热门
./xhs-py.sh hot -c travel

# 9. 查看用户资料
./xhs-py.sh user <用户ID>

# 10. 关注用户
./xhs-py.sh follow <用户ID>

# 11. 查看通知
./xhs-py.sh unread
./xhs-py.sh notifications
```

---

## 两个版本的区别

| 特性 | Python 版 | Go 版 |
|------|-----------|-------|
| 运行方式 | `./xhs-py.sh <命令>` | `./xhs-go.sh <命令>` |
| 浏览器Cookie提取 | ✅ 自动支持多种浏览器 | ❌ 需手动输入 |
| QR码登录 | ✅ 支持 | ❌ 不支持 |
| 发布笔记(post) | ✅ 支持 | ❌ 暂不可用 |
| 签名方式 | xhshow真实加密签名 | 简化版签名 |
| 风控风险 | 较低（真实签名） | 较高（简化签名） |
| 启动速度 | 稍慢（加载Python） | 很快（编译好的二进制） |
| 共享登录 | ✅ 共享 cookies.json | ✅ 共享 cookies.json |

> **建议**：日常使用 Python 版（签名更真实，不容易被封），Go 版作为备用。

---

## 热门分类 (hot -c)

| 参数 | 分类 |
|------|------|
| fashion | 时尚 |
| food | 美食（默认） |
| cosmetics | 美妆 |
| movie | 影视 |
| career | 职场 |
| love | 情感 |
| home | 家居 |
| gaming | 游戏 |
| travel | 旅行 |
| fitness | 健身 |
