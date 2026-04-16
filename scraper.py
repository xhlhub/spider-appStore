import csv
import os
import time
from urllib.parse import quote

import requests

REVIEW_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortBy=mostRecent/page={page}/json"
)
LOOKUP_URL = "https://itunes.apple.com/lookup"
SEARCH_URL = "https://itunes.apple.com/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

MAX_PAGES = 10
MAX_RETRIES = 3
RETRY_DELAY = 2


def search_app(name: str, country: str = "cn") -> dict | None:
    """通过 iTunes Search API 根据名称搜索 App，返回最匹配的结果"""
    params = {
        "term": name,
        "country": country,
        "entity": "software",
        "limit": 5,
    }
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        # 优先精确匹配名称，否则取第一个结果
        best = results[0]
        for app in results:
            if app.get("trackName", "").strip().lower() == name.strip().lower():
                best = app
                break
        return {
            "app_id": str(best["trackId"]),
            "name": best.get("trackName", ""),
            "developer": best.get("artistName", ""),
            "rating": best.get("averageUserRating", 0),
            "version": best.get("version", ""),
        }
    except requests.RequestException as e:
        print(f"  [错误] 搜索App失败: {e}")
    return None


def fetch_app_info(app_id: str, country: str = "cn") -> dict | None:
    """通过 iTunes Lookup API 获取 App 基本信息"""
    params = {"id": app_id, "country": country}
    try:
        resp = requests.get(LOOKUP_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            app = results[0]
            return {
                "app_id": app_id,
                "name": app.get("trackName", ""),
                "developer": app.get("artistName", ""),
                "rating": app.get("averageUserRating", 0),
                "version": app.get("version", ""),
            }
    except requests.RequestException as e:
        print(f"  [错误] 获取App信息失败: {e}")
    return None


def _parse_entry(entry: dict) -> dict | None:
    """解析单条 RSS entry 为评论字典，跳过非评论条目"""
    if "im:rating" not in entry:
        return None
    return {
        "author": entry.get("author", {}).get("name", {}).get("label", ""),
        "rating": entry.get("im:rating", {}).get("label", ""),
        "title": entry.get("title", {}).get("label", ""),
        "content": entry.get("content", {}).get("label", ""),
        "version": entry.get("im:version", {}).get("label", ""),
        "updated": entry.get("updated", {}).get("label", ""),
    }


def _fetch_page(app_id: str, country: str, page: int) -> list[dict]:
    """请求单页评论，含重试机制"""
    url = REVIEW_URL.format(country=country, app_id=app_id, page=page)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            feed = resp.json().get("feed", {})
            entries = feed.get("entry", [])
            if not isinstance(entries, list):
                entries = [entries]
            reviews = []
            for entry in entries:
                parsed = _parse_entry(entry)
                if parsed:
                    reviews.append(parsed)
            return reviews
        except requests.RequestException as e:
            if attempt < MAX_RETRIES:
                print(f"  [重试] 第{page}页请求失败({attempt}/{MAX_RETRIES}): {e}")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  [错误] 第{page}页请求失败，已跳过: {e}")
    return []


def fetch_reviews(
    app_id: str, country: str = "cn", max_pages: int = MAX_PAGES, delay: float = 1.5
) -> list[dict]:
    """抓取指定 App 的全部评论（最多 max_pages 页）"""
    all_reviews = []
    for page in range(1, max_pages + 1):
        print(f"  正在抓取第 {page}/{max_pages} 页...")
        reviews = _fetch_page(app_id, country, page)
        if not reviews:
            print(f"  第{page}页无更多评论，停止翻页")
            break
        all_reviews.extend(reviews)
        print(f"  本页获取 {len(reviews)} 条，累计 {len(all_reviews)} 条")
        if page < max_pages:
            time.sleep(delay)
    return all_reviews


CSV_FIELDS = ["author", "rating", "title", "content", "version", "updated"]


def save_to_csv(reviews: list[dict], filepath: str) -> None:
    """将评论列表保存为 CSV 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(reviews)
    print(f"  已保存 {len(reviews)} 条评论到 {filepath}")
