#!/usr/bin/env python3
import requests
import sys

SYNCTV_URL = "http://localhost:8080"
DEFAULT_USERNAME = "root"
DEFAULT_PASSWORD = "root"
DEFAULT_FILE = "videos.txt"

def login(username, password):
    """登录获取 token"""
    resp = requests.post(
        f"{SYNCTV_URL}/api/user/login",
        json={"username": username, "password": password}
    )
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("token")
    else:
        print(f"✗ 登录失败: {resp.status_code} {resp.text}")
        sys.exit(1)

def clear_playlist(token, room_id):
    """清空房间播放列表"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{SYNCTV_URL}/api/room/movie/clear?roomId={room_id}",
        json={"parentId": ""},
        headers=headers
    )

    if resp.status_code == 204 or resp.status_code == 200:
        print("✓ 已清空播放列表")
        return True
    else:
        print(f"✗ 清空失败: {resp.status_code}")
        try:
            error = resp.json()
            print(f"  错误: {error.get('error', resp.text)}")
        except:
            print(f"  错误: {resp.text}")
        return False


def batch_import(token, room_id, movies):
    """批量导入视频"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{SYNCTV_URL}/api/room/movie/pushs?roomId={room_id}",
        json=movies,
        headers=headers
    )

    if resp.status_code == 200:
        print(f"✓ 成功导入 {len(movies)} 个视频")
        return True
    else:
        print(f"✗ 导入失败: {resp.status_code}")
        try:
            error = resp.json()
            print(f"  错误: {error.get('error', resp.text)}")
        except:
            print(f"  错误: {resp.text}")
        return False

def parse_file(file_path, enable_rename=False):
    """解析文件"""
    movies = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # 支持 | 和 $ 两种分隔符
        if '$' in line:
            parts = line.split('$', 1)
        else:
            parts = line.split('|', 1)

        name = parts[0].strip() if len(parts) > 1 else parts[0].split('/')[-1]
        url = parts[1].strip() if len(parts) > 1 else parts[0].strip()

        if enable_rename:
            new_name = input(f"  [{i}] {name} -> 新名称 (回车跳过): ").strip()
            if new_name:
                name = new_name

        movies.append({"url": url, "name": name})
        print(f"  [{i}] {name}")

    return movies

def main():
    # 解析参数
    room_id = input("房间 ID: ").strip()

    username = input(f"用户名 (默认: {DEFAULT_USERNAME}): ").strip() or DEFAULT_USERNAME
    password = input(f"密码 (默认: {DEFAULT_PASSWORD}): ").strip() or DEFAULT_PASSWORD
    file_path = input(f"文件路径 (默认: {DEFAULT_FILE}): ").strip() or DEFAULT_FILE

    rename = input("是否重命名视频? (y/N): ").strip().lower() == 'y'
    clear_before = input("导入前清空播放列表? (y/N): ").strip().lower() == 'y'

    print("\n正在登录...")
    token = login(username, password)
    print("✓ 登录成功\n")

    print("解析文件:")
    movies = parse_file(file_path, rename)

    if not movies:
        print("没有找到有效的链接")
        sys.exit(1)

    print(f"\n共 {len(movies)} 个视频")

    if clear_before:
        print("\n清空播放列表...")
        clear_playlist(token, room_id)

    print("开始导入...")
    batch_import(token, room_id, movies)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
    except FileNotFoundError:
        print(f"\n错误: 文件不存在，请创建 {DEFAULT_FILE} 文件")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
