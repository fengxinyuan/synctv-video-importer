#!/usr/bin/env python3
"""
SyncTV 采集站资源搜索和导入工具
支持从多个采集站搜索视频资源并批量导入到 SyncTV
"""
import requests
import sys
import json
import warnings
import os

# 禁用SSL警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# SyncTV 配置
SYNCTV_URL = "http://172.17.0.2:8080"
DEFAULT_USERNAME = "root"
DEFAULT_ROOM_ID = "4d798e90700743c1907f830df0798f8e"
DEFAULT_PASSWORD = "root"

# 自定义配置文件路径
CUSTOM_CONFIG_FILE = "collectors_custom.json"

# 采集站配置 (经过测试的可用站点)
COLLECTORS = {
    "1": {
        "name": "魔都资源",
        "api": "https://moduzy.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓",
        "note": "推荐，专注动漫资源",
        "backup_apis": [
            "https://moduzy1.com/api.php/provide/vod/"
        ]
    },
    "2": {
        "name": "360资源",
        "api": "https://360zy5.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "3": {
        "name": "红牛资源",
        "api": "http://hongniuzy2.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "4": {
        "name": "量子资源",
        "api": "https://cj.lziapi.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "5": {
        "name": "速播资源",
        "api": "https://subocaiji.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "6": {
        "name": "最大资源",
        "api": "https://api.zuidapi.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "7": {
        "name": "卧龙资源",
        "api": "https://collect.wolongzyw.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "8": {
        "name": "光速资源",
        "api": "https://api.guangsuapi.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "9": {
        "name": "新浪资源",
        "api": "https://api.xinlangapi.com/xinlangapi.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "10": {
        "name": "无尽资源",
        "api": "https://api.wujinapi.com/api.php/provide/vod/",
        "type": "json",
        "status": "✓"
    },
    "11": {
        "name": "淘片资源",
        "api": "https://taopianzy.com/api.php/provide/vod/",
        "type": "json",
        "status": "⚠",
        "note": "可能需要特殊网络环境",
        "backup_apis": [
            "https://www.taopianzy.com/api.php/provide/vod/"
        ]
    }
}


def login(username, password):
    """登录获取 token"""
    try:
        resp = requests.post(
            f"{SYNCTV_URL}/api/user/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("token")
        else:
            print(f"✗ 登录失败: {resp.status_code}")
            return None
    except Exception as e:
        print(f"✗ 登录错误: {e}")
        return None


def clear_playlist(token, room_id):
    """清空房间播放列表"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(
            f"{SYNCTV_URL}/api/room/movie/clear?roomId={room_id}",
            json={"parentId": ""},
            headers=headers,
            timeout=10
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
    except Exception as e:
        print(f"✗ 清空错误: {e}")
        return False


def search_collector_direct(collector, keyword, retry=2):
    """直接使用collector对象搜索资源 (带重试机制和备用API)"""
    # 获取所有可用的API列表
    apis = [collector['api']]
    if 'backup_apis' in collector:
        apis.extend(collector['backup_apis'])

    print(f"\n🔍 正在搜索 [{collector['name']}]: {keyword}")

    # 尝试每个API
    for api_index, api_url in enumerate(apis):
        if api_index > 0:
            print(f"  ⚠ 尝试备用API ({api_index}/{len(apis)-1})")

        search_url = f"{api_url}?wd={keyword}"

        for attempt in range(retry + 1):
            try:
                resp = requests.get(
                    search_url,
                    timeout=10,
                    verify=False,  # 禁用SSL验证
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )

                if resp.status_code != 200:
                    if attempt < retry:
                        print(f"  ⚠ 请求失败 ({resp.status_code})，重试中... ({attempt + 1}/{retry})")
                        continue
                    else:
                        # 如果还有备用API，跳到下一个
                        if api_index < len(apis) - 1:
                            break
                        print(f"✗ 请求失败: {resp.status_code}")
                        return []

                # 解析 JSON 响应
                try:
                    data = resp.json()
                    if 'list' in data:
                        results = data['list']
                    elif 'data' in data:
                        results = data['data']
                    else:
                        print(f"✗ 未知的响应格式: {list(data.keys())}")
                        return []

                    # 过滤掉空结果
                    if not results:
                        print(f"✗ 没有找到相关资源")
                    return results

                except json.JSONDecodeError:
                    if attempt < retry:
                        print(f"  ⚠ 响应解析失败，重试中... ({attempt + 1}/{retry})")
                        continue
                    else:
                        # 如果还有备用API，跳到下一个
                        if api_index < len(apis) - 1:
                            break
                        print(f"✗ 响应格式错误 (非JSON)")
                        return []

            except requests.exceptions.Timeout:
                if attempt < retry:
                    print(f"  ⚠ 请求超时，重试中... ({attempt + 1}/{retry})")
                    continue
                else:
                    # 如果还有备用API，跳到下一个
                    if api_index < len(apis) - 1:
                        break
                    print(f"✗ 请求超时，采集站可能无法访问")
                    return []
            except requests.exceptions.SSLError:
                # 如果还有备用API，跳到下一个
                if api_index < len(apis) - 1:
                    break
                print(f"✗ SSL证书错误")
                return []
            except Exception as e:
                if attempt < retry:
                    print(f"  ⚠ 错误: {str(e)[:30]}，重试中... ({attempt + 1}/{retry})")
                    continue
                else:
                    # 如果还有备用API，跳到下一个
                    if api_index < len(apis) - 1:
                        break
                    print(f"✗ 搜索错误: {str(e)[:50]}")
                    return []

    return []


def display_results(results):
    """显示搜索结果"""
    if not results:
        print("✗ 没有找到相关资源\n")
        return False

    print(f"\n找到 {len(results)} 个结果：\n")
    print(f"{'序号':<4} {'名称':<40} {'类型':<10} {'年份':<6}")
    print("-" * 70)

    for i, item in enumerate(results, 1):
        name = item.get('vod_name', '未知')
        type_name = item.get('type_name', '未知')
        year = item.get('vod_year', '未知')
        print(f"{i:<4} {name:<40} {type_name:<10} {year:<6}")

    print()
    return True


def parse_play_url(play_url_str):
    """解析播放地址
    格式: 第1集$http://xxx#第2集$http://yyy 或其他分隔符
    """
    episodes = []

    # 尝试不同的分隔符
    if '#' in play_url_str:
        parts = play_url_str.split('#')
    elif '$$$' in play_url_str:
        parts = play_url_str.split('$$$')
    else:
        parts = [play_url_str]

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 解析 集数$链接 格式
        if '$' in part:
            name, url = part.split('$', 1)
            episodes.append({"name": name.strip(), "url": url.strip()})
        else:
            # 只有链接，使用序号作为名称
            episodes.append({
                "name": f"第{len(episodes)+1}集",
                "url": part.strip()
            })

    return episodes


def get_video_detail_from_api(collector, vod_id):
    """从API获取视频详情"""
    try:
        resp = requests.get(
            f"{collector['api']}?ac=detail&ids={vod_id}",
            timeout=10,
            verify=False,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        if resp.status_code == 200:
            data = resp.json()
            results = data.get('list', data.get('data', []))
            if results:
                return results[0]
    except Exception as e:
        print(f"  ⚠ 获取详情失败: {str(e)[:50]}")

    return None


def get_video_detail(item, collector=None):
    """获取视频详情和播放列表"""
    print(f"\n📺 {item.get('vod_name', '未知')}")
    print(f"   类型: {item.get('type_name', '未知')}")
    print(f"   年份: {item.get('vod_year', '未知')}")
    print(f"   地区: {item.get('vod_area', '未知')}")
    print(f"   导演: {item.get('vod_director', '未知')}")
    print(f"   主演: {item.get('vod_actor', '未知')}")
    print(f"   简介: {item.get('vod_content', '无')[:100]}...")

    # 获取播放列表
    vod_play_from = item.get('vod_play_from', '')
    vod_play_url = item.get('vod_play_url', '')

    # 如果搜索结果没有播放地址，尝试调用详情API
    if not vod_play_url and collector and item.get('vod_id'):
        print(f"\n  ⚠ 搜索结果无播放地址，正在获取详情...")
        detail = get_video_detail_from_api(collector, item.get('vod_id'))
        if detail:
            vod_play_from = detail.get('vod_play_from', '')
            vod_play_url = detail.get('vod_play_url', '')
            print(f"  ✓ 成功获取详情")

    if not vod_play_url:
        print("\n✗ 没有可用的播放地址")
        return []

    # 如果有多个播放源
    play_sources = vod_play_from.split('$$$') if vod_play_from else ['默认']
    play_urls = vod_play_url.split('$$$') if '$$$' in vod_play_url else [vod_play_url]

    all_episodes = []

    print(f"\n可用播放源:")
    for i, (source, urls) in enumerate(zip(play_sources, play_urls), 1):
        episodes = parse_play_url(urls)
        print(f"  [{i}] {source} - {len(episodes)} 集")
        all_episodes.append({"source": source, "episodes": episodes})

    return all_episodes


def batch_import(token, room_id, movies):
    """批量导入视频到 SyncTV"""
    if not movies:
        print("✗ 没有可导入的视频")
        return False

    headers = {"Authorization": f"Bearer {token}"}

    # 转换为 SyncTV 格式
    import_list = [{"url": m["url"], "name": m["name"]} for m in movies]

    try:
        resp = requests.post(
            f"{SYNCTV_URL}/api/room/movie/pushs?roomId={room_id}",
            json=import_list,
            headers=headers,
            timeout=30
        )

        if resp.status_code == 200:
            print(f"\n✓ 成功导入 {len(movies)} 个视频")
            return True
        else:
            print(f"\n✗ 导入失败: {resp.status_code}")
            try:
                error = resp.json()
                print(f"  错误: {error.get('error', resp.text)}")
            except:
                print(f"  错误: {resp.text}")
            return False
    except Exception as e:
        print(f"\n✗ 导入错误: {e}")
        return False


def load_custom_collectors():
    """加载自定义采集站配置"""
    if not os.path.exists(CUSTOM_CONFIG_FILE):
        return {}

    try:
        with open(CUSTOM_CONFIG_FILE, 'r', encoding='utf-8') as f:
            custom = json.load(f)
            print(f"✓ 加载自定义配置: {len(custom)} 个采集站\n")
            return custom
    except Exception as e:
        print(f"⚠ 加载自定义配置失败: {e}\n")
        return {}


def main():
    print("=" * 70)
    print("  SyncTV 采集站资源搜索导入工具 v2.2")
    print("=" * 70)

    # 加载自定义配置
    custom_collectors = load_custom_collectors()

    # 合并采集站列表
    all_collectors = COLLECTORS.copy()
    if custom_collectors:
        start_id = len(all_collectors) + 1
        for i, (name, config) in enumerate(custom_collectors.items()):
            all_collectors[str(start_id + i)] = {
                "name": name,
                "api": config.get("api"),
                "type": config.get("type", "json"),
                "status": "⭐"  # 自定义站点标记
            }

    # 显示采集站列表
    print("\n可用采集站:")
    print("-" * 70)
    for id, info in all_collectors.items():
        status = info.get('status', '')
        name = info['name']
        # 显示是否有备用API
        backup_info = ""
        if 'backup_apis' in info:
            backup_info = f" (含{len(info['backup_apis'])}个备用API)"
        # 显示注释
        note = info.get('note', '')
        note_str = f" - {note}" if note else ""
        print(f"  [{id:>2}] {status} {name:<20}{backup_info}{note_str}")
    print("-" * 70)
    print("\n提示:")
    print("  ✓ = 已测试可用")
    print("  ⚠ = 可能需要特殊网络环境")
    print("  ⭐ = 自定义采集站")
    print("  推荐: 1-魔都资源 (动漫专注), 2-360资源, 3-红牛资源")

    # 选择采集站
    collector_id = input(f"\n选择采集站 [1-{len(all_collectors)}] (默认: 1): ").strip() or "1"
    if collector_id not in all_collectors:
        print("✗ 无效的选择")
        sys.exit(1)

    # 输入搜索关键词
    keyword = input("搜索关键词: ").strip()
    if not keyword:
        print("✗ 关键词不能为空")
        sys.exit(1)

    # 使用all_collectors进行搜索
    selected_collector = all_collectors[collector_id]
    results = search_collector_direct(selected_collector, keyword)
    if not display_results(results):
        sys.exit(0)

    # 选择结果
    choice = input("选择结果序号 (0=退出): ").strip()
    if choice == '0' or not choice.isdigit():
        print("已取消")
        sys.exit(0)

    choice = int(choice)
    if choice < 1 or choice > len(results):
        print("✗ 无效的序号")
        sys.exit(1)

    selected = results[choice - 1]

    # 显示详情和播放列表
    all_episodes = get_video_detail(selected, selected_collector)
    if not all_episodes:
        sys.exit(0)

    # 选择播放源
    if len(all_episodes) > 1:
        source_choice = input(f"\n选择播放源 [1-{len(all_episodes)}]: ").strip()
        if not source_choice.isdigit() or int(source_choice) < 1 or int(source_choice) > len(all_episodes):
            print("✗ 无效的选择")
            sys.exit(1)
        episodes = all_episodes[int(source_choice) - 1]["episodes"]
    else:
        episodes = all_episodes[0]["episodes"]

    print(f"\n共 {len(episodes)} 集")

    # 选择导入范围
    import_choice = input(f"导入范围 (1-{len(episodes)}, 或 'all' 全部, 或 '1-10' 范围): ").strip()

    to_import = []

    if import_choice.lower() == 'all':
        to_import = episodes
    elif '-' in import_choice:
        # 范围导入 1-10
        try:
            start, end = map(int, import_choice.split('-'))
            to_import = episodes[start-1:end]
        except:
            print("✗ 无效的范围格式")
            sys.exit(1)
    elif import_choice.isdigit():
        # 单集导入
        idx = int(import_choice) - 1
        if 0 <= idx < len(episodes):
            to_import = [episodes[idx]]
        else:
            print("✗ 无效的序号")
            sys.exit(1)
    else:
        print("✗ 无效的选择")
        sys.exit(1)

    print(f"\n准备导入 {len(to_import)} 集:")
    for ep in to_import[:5]:  # 只显示前5个
        print(f"  - {ep['name']}")
    if len(to_import) > 5:
        print(f"  ... 还有 {len(to_import) - 5} 集")

    # 登录 SyncTV
    print("\n" + "=" * 70)
    room_id = input(f"SyncTV 房间 ID (默认: {DEFAULT_ROOM_ID}): ").strip() or DEFAULT_ROOM_ID
    username = input(f"用户名 (默认: {DEFAULT_USERNAME}): ").strip() or DEFAULT_USERNAME
    password = input(f"密码 (默认: {DEFAULT_PASSWORD}): ").strip() or DEFAULT_PASSWORD
    clear_before = input("导入前清空播放列表? (y/N): ").strip().lower() == 'y'

    print("\n正在登录...")
    token = login(username, password)
    if not token:
        sys.exit(1)

    print("✓ 登录成功")

    # 确认导入
    confirm = input(f"\n确认导入 {len(to_import)} 集到房间? (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        sys.exit(0)

    # 清空播放列表
    if clear_before:
        print("\n清空播放列表...")
        clear_playlist(token, room_id)

    # 批量导入
    batch_import(token, room_id, to_import)
    print("\n完成！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
