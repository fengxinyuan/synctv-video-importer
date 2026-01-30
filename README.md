# SyncTV 视频导入工具

批量导入视频到 SyncTV 房间的 Python 工具集。

## 功能

- 从采集站搜索并导入视频资源
- 支持本地文件批量导入
- 支持账号密码登录或 Token 认证

## 工具说明

| 工具 | 说明 |
|------|------|
| `synctv_collector.py` | **推荐** - 从采集站搜索导入，支持 11 个采集站 |
| `synctv_import.py` | 从本地文件导入，账号密码登录 |
| `synctv_import_token.py` | 从本地文件导入，Token 认证 |

## 快速开始

### 方式一：从采集站搜索导入（推荐）

```bash
python3 synctv_collector.py
```

交互流程：
1. 选择采集站（推荐 2-360资源 或 3-红牛资源）
2. 输入搜索关键词
3. 选择搜索结果
4. 选择播放源和集数范围
5. 输入 SyncTV 房间信息
6. 确认导入

### 方式二：从本地文件导入

1. 编辑 `videos.txt`：
```
第1集$https://example.com/ep1.m3u8
第2集$https://example.com/ep2.m3u8
```

2. 运行导入：
```bash
python3 synctv_import.py
```

## 支持的采集站

| 序号 | 名称 | 状态 | 说明 |
|------|------|------|------|
| 1 | 量子资源 | ✓ | |
| 2 | 360资源 | ✓ | 推荐，稳定 |
| 3 | 红牛资源 | ✓ | 推荐，稳定 |
| 4 | 速播资源 | ✓ | |
| 5 | 最大资源 | ✓ | |
| 6 | 卧龙资源 | ✓ | |
| 7 | 光速资源 | ✓ | |
| 8 | 新浪资源 | ✓ | |
| 9 | 无尽资源 | ✓ | |
| 10 | 魔都资源 | ✓ | 动漫专注 |
| 11 | 淘片资源 | ⚠ | 可能需要特殊网络 |

## 自定义采集站

创建 `collectors_custom.json`：

```json
{
  "自定义站点": {
    "api": "https://example.com/api.php/provide/vod/",
    "type": "json"
  }
}
```

## 文件格式

支持三种格式（每行一个）：

```
名称$链接
链接|名称
链接
```

## 配置

修改脚本中的配置：

```python
SYNCTV_URL = "http://localhost:8080"  # SyncTV 地址
DEFAULT_USERNAME = "root"              # 默认用户名
DEFAULT_PASSWORD = "root"              # 默认密码
```

## 依赖

```bash
pip install requests
```

## License

MIT
