# SyncTV 批量导入工具

批量导入视频链接到 SyncTV 房间的 Python 工具。

## 功能特点

- ✅ 支持账号密码登录或 Token 认证
- ✅ 批量导入视频链接
- ✅ 支持多种文件格式 (`名称$链接`, `链接|名称`, 纯链接)
- ✅ 交互式重命名功能
- ✅ 详细的错误提示

## 工具列表

### 1. synctv_import.py (推荐)
**账号密码登录版本**

```bash
python3 synctv_import.py
```

特点:
- 使用账号密码登录
- 默认用户名/密码: root/root
- 默认文件: videos.txt
- 支持交互式重命名

### 2. synctv_import_token.py
**Token 认证版本**

```bash
python3 synctv_import_token.py videos.txt
```

特点:
- 使用 Bearer Token 认证
- 需要在脚本中配置 TOKEN 和 ROOM_ID
- 适合自动化脚本

## 快速开始

### 1. 准备视频列表

编辑 `videos.txt`:

```
# 格式 1: 名称$链接
第1集$https://example.com/video1.m3u8
第2集$https://example.com/video2.m3u8

# 格式 2: 链接|名称
https://example.com/video3.mp4|电影名称

# 格式 3: 仅链接
https://example.com/video4.mp4
```

### 2. 运行导入

```bash
python3 synctv_import.py
```

按提示输入:
- 房间 ID (32位字符)
- 用户名 (默认: root)
- 密码 (默认: root)
- 文件路径 (默认: videos.txt)
- 是否重命名 (y/N)

## 文件格式

支持三种格式:

| 格式 | 示例 | 说明 |
|------|------|------|
| 名称$链接 | `第1集$https://example.com/video.m3u8` | 名称在前,链接在后 |
| 链接\|名称 | `https://example.com/video.mp4\|电影` | 链接在前,名称在后 |
| 仅链接 | `https://example.com/video.mp4` | 自动使用文件名 |

注释行以 `#` 开头会被忽略。

## 示例

```bash
# 创建视频列表
cat > videos.txt << 'EOF'
# 电视剧
第1集$https://example.com/ep1.m3u8
第2集$https://example.com/ep2.m3u8

# 电影
https://example.com/movie.mp4|功夫熊猫
EOF

# 运行导入
python3 synctv_import.py
```

## 常见问题

**Q: 如何获取房间 ID?**
A: 在 SyncTV 房间页面 URL 中,格式为 32 位字符串

**Q: 导入失败显示 401/403?**
A: 检查用户名密码或 Token 是否正确

**Q: 导入失败显示 404?**
A: 检查房间 ID 是否正确,必须是 32 位字符

**Q: 支持哪些视频格式?**
A: 支持所有 SyncTV 支持的格式: mp4, m3u8, flv 等

## 依赖

```bash
pip install requests
```

## License

MIT
