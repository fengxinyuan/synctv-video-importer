#!/usr/bin/env python3
import requests
import sys

# 配置
SYNCTV_URL = "http://localhost:8080"
TOKEN = ""  # 填入你的 Bearer token
ROOM_ID = ""  # 填入房间 ID (32位)

def batch_import(urls_file):
    with open(urls_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    movies = []
    for line in lines:
        # 支持 | 和 $ 两种分隔符
        if '$' in line:
            parts = line.split('$', 1)
            name = parts[0].strip()
            url = parts[1].strip()
        elif '|' in line:
            parts = line.split('|', 1)
            url = parts[0].strip()
            name = parts[1].strip()
        else:
            url = line.strip()
            name = url.split('/')[-1]

        movies.append({"url": url, "name": name})

    headers = {"Authorization": TOKEN}
    resp = requests.post(
        f"{SYNCTV_URL}/api/room/movie/pushs?roomId={ROOM_ID}",
        json=movies,
        headers=headers
    )

    if resp.status_code == 200:
        print(f"✓ 成功导入 {len(movies)} 个视频")
    else:
        print(f"✗ 导入失败: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 synctv_import_token.py videos.txt")
        print("\n文件格式(每行一个):")
        print("  名称$https://example.com/video.mp4")
        print("  https://example.com/video.mp4|名称")
        print("  https://example.com/video.mp4")
        sys.exit(1)

    batch_import(sys.argv[1])
