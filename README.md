# SyncTV 采集站导入工具

从采集站搜索视频资源并批量导入到 SyncTV 房间。

## 使用

```bash
# 交互模式
python3 synctv_collector.py

# 直接搜索
python3 synctv_collector.py "关键词"
```

最快流程（3次回车）：
```
python3 synctv_collector.py "葬送的芙莉莲"
→ 回车(使用配置) → 回车(选第一个) → 回车(全部导入)
```

## 功能

- 记住配置（采集站、房间、用户名、密码）
- 支持命令行参数直接搜索
- 默认选择第一个结果和播放源
- 自动清空播放列表后导入
- 支持 11 个采集站，自动重试和备用 API

## 文件

```
synctv_collector.py  # 主程序
collectors.json      # 采集站配置
.config.json         # 用户配置（自动生成）
```

## 依赖

```bash
pip install requests
```
