#!/usr/bin/env python3
"""
SyncTV 采集站资源搜索和导入工具
用法: python3 synctv_collector.py [关键词]
"""
import requests
import sys
import json
import os
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# 配置文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECTORS_FILE = os.path.join(SCRIPT_DIR, "collectors.json")
CONFIG_FILE = os.path.join(SCRIPT_DIR, ".config.json")

# 默认配置
DEFAULT_CONFIG = {
    "synctv_url": "http://172.17.0.2:8080",
    "username": "root",
    "password": "root",
    "room_id": "4d798e90700743c1907f830df0798f8e",
    "collector": "1"
}


def load_config():
    """加载用户配置"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            saved = json.load(f)
            return {**DEFAULT_CONFIG, **saved}
    except:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存用户配置"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass


def load_collectors():
    """从 JSON 文件加载采集站配置"""
    try:
        with open(COLLECTORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ 采集站配置文件不存在: {COLLECTORS_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ 采集站配置文件格式错误: {e}")
        sys.exit(1)


def login(url, username, password):
    """登录获取 token"""
    try:
        resp = requests.post(f"{url}/api/user/login", json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("token")
        print(f"✗ 登录失败: {resp.status_code}")
        return None
    except Exception as e:
        print(f"✗ 登录错误: {e}")
        return None


def clear_playlist(url, token, room_id):
    """清空房间播放列表"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        requests.post(f"{url}/api/room/movie/current?roomId={room_id}", json={}, headers=headers, timeout=10)
        resp = requests.post(f"{url}/api/room/movie/clear?roomId={room_id}", json={"parentId": ""}, headers=headers, timeout=10)
        if resp.status_code in (200, 204):
            print("✓ 已清空播放列表")
            return True
        elif resp.status_code == 400:
            try:
                if "not found" in resp.json().get('error', '').lower():
                    print("✓ 播放列表已为空")
                    return True
            except:
                pass
        print(f"✗ 清空失败: {resp.status_code}")
        return False
    except Exception as e:
        print(f"✗ 清空错误: {e}")
        return False


def search(collector, keyword, retry=2):
    """搜索资源"""
    apis = [collector['api']] + collector.get('backup_apis', [])
    print(f"\n🔍 搜索 [{collector['name']}]: {keyword}")

    for api_idx, api_url in enumerate(apis):
        if api_idx > 0:
            print(f"  ⚠ 尝试备用API...")

        for attempt in range(retry + 1):
            try:
                resp = requests.get(f"{api_url}?wd={keyword}", timeout=10, verify=False,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get('list', data.get('data', []))
                    if not results:
                        print("✗ 没有找到相关资源")
                    return results
            except:
                if attempt < retry:
                    continue
                if api_idx < len(apis) - 1:
                    break

    print("✗ 搜索失败")
    return []


def get_detail(collector, vod_id):
    """获取视频详情"""
    try:
        resp = requests.get(f"{collector['api']}?ac=detail&ids={vod_id}", timeout=10, verify=False,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        if resp.status_code == 200:
            results = resp.json().get('list', resp.json().get('data', []))
            if results:
                return results[0]
    except:
        pass
    return None


def parse_episodes(play_url_str):
    """解析播放地址"""
    episodes = []
    parts = play_url_str.split('#') if '#' in play_url_str else [play_url_str]
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '$' in part:
            name, url = part.split('$', 1)
            episodes.append({"name": name.strip(), "url": url.strip()})
        else:
            episodes.append({"name": f"第{len(episodes)+1}集", "url": part})
    return episodes


def batch_import(url, token, room_id, movies):
    """批量导入视频"""
    if not movies:
        return False
    try:
        resp = requests.post(f"{url}/api/room/movie/pushs?roomId={room_id}",
            json=[{"url": m["url"], "name": m["name"]} for m in movies],
            headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if resp.status_code == 200:
            print(f"✓ 成功导入 {len(movies)} 个视频")
            return True
        print(f"✗ 导入失败: {resp.status_code}")
        return False
    except Exception as e:
        print(f"✗ 导入错误: {e}")
        return False


def main():
    print("=" * 60)
    print("  SyncTV 采集站导入工具 v2.4")
    print("=" * 60)

    # 加载配置
    config = load_config()
    collectors = load_collectors()

    # 命令行参数
    keyword = sys.argv[1] if len(sys.argv) > 1 else None

    # 显示当前配置，询问是否使用
    collector_name = collectors.get(config['collector'], {}).get('name', '未知')
    print(f"\n当前配置: 采集站={collector_name}, 房间={config['room_id'][:8]}...")

    use_last = input("使用此配置? (Y/n): ").strip().lower()

    if use_last == 'n':
        # 重新配置
        print("\n可用采集站:")
        for id, info in collectors.items():
            print(f"  [{id}] {info.get('status','')} {info['name']}")

        config['collector'] = input(f"采集站 [{config['collector']}]: ").strip() or config['collector']
        config['synctv_url'] = input(f"SyncTV地址 [{config['synctv_url']}]: ").strip() or config['synctv_url']
        config['room_id'] = input(f"房间ID [{config['room_id']}]: ").strip() or config['room_id']
        config['username'] = input(f"用户名 [{config['username']}]: ").strip() or config['username']
        config['password'] = input(f"密码 [{config['password']}]: ").strip() or config['password']
        save_config(config)
        print("✓ 配置已保存")

    # 搜索关键词
    if not keyword:
        keyword = input("\n搜索关键词: ").strip()
    if not keyword:
        print("✗ 关键词不能为空")
        sys.exit(1)

    # 搜索
    collector = collectors.get(config['collector'])
    if not collector:
        print("✗ 无效的采集站")
        sys.exit(1)

    results = search(collector, keyword)
    if not results:
        sys.exit(0)

    # 显示结果
    print(f"\n找到 {len(results)} 个结果:")
    for i, item in enumerate(results[:10], 1):
        print(f"  [{i}] {item.get('vod_name', '未知')} ({item.get('type_name', '')} {item.get('vod_year', '')})")

    # 选择结果（默认第一个）
    choice = input(f"选择 [1]: ").strip() or "1"
    if choice == '0':
        sys.exit(0)
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(results):
        print("✗ 无效选择")
        sys.exit(1)

    selected = results[int(choice) - 1]
    print(f"\n📺 {selected.get('vod_name')}")

    # 获取播放地址（搜索结果可能不含播放地址，需调详情API）
    vod_play_url = selected.get('vod_play_url', '')
    if not vod_play_url:
        detail = get_detail(collector, selected.get('vod_id'))
        if detail:
            vod_play_url = detail.get('vod_play_url', '')

    if not vod_play_url:
        print("✗ 没有播放地址")
        sys.exit(1)

    # 解析播放源
    play_urls = vod_play_url.split('$$$') if '$$$' in vod_play_url else [vod_play_url]
    play_sources = selected.get('vod_play_from', '').split('$$$') if selected.get('vod_play_from') else ['默认']

    all_episodes = []
    for source, urls in zip(play_sources, play_urls):
        eps = parse_episodes(urls)
        print(f"  [{len(all_episodes)+1}] {source} - {len(eps)}集")
        all_episodes.append({"source": source, "episodes": eps})

    # 选择播放源（默认第一个）
    if len(all_episodes) > 1:
        src = input(f"播放源 [1]: ").strip() or "1"
        episodes = all_episodes[int(src)-1]["episodes"] if src.isdigit() and 0 < int(src) <= len(all_episodes) else all_episodes[0]["episodes"]
    else:
        episodes = all_episodes[0]["episodes"]

    print(f"\n共 {len(episodes)} 集")

    # 选择范围（默认全部）
    range_input = input("范围 (回车=全部, 1-5=范围): ").strip()
    if not range_input:
        to_import = episodes
    elif '-' in range_input:
        start, end = map(int, range_input.split('-'))
        to_import = episodes[start-1:end]
    elif range_input.isdigit():
        to_import = [episodes[int(range_input)-1]]
    else:
        to_import = episodes

    # 登录并导入
    print(f"\n登录中...")
    token = login(config['synctv_url'], config['username'], config['password'])
    if not token:
        sys.exit(1)
    print("✓ 登录成功")

    print("清空播放列表...")
    clear_playlist(config['synctv_url'], token, config['room_id'])

    batch_import(config['synctv_url'], token, config['room_id'], to_import)
    print("\n完成!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        sys.exit(1)
