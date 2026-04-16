"""
App Store 评论爬虫
通过 Apple iTunes RSS Feed 抓取 iPhone App 的用户评论并导出为 CSV。

使用方法:
    python3 main.py <App名称>
    python3 main.py 微信
    python3 main.py 抖音
"""

import os
import sys

from scraper import fetch_reviews, save_to_csv, search_app

COUNTRY = "cn"
OUTPUT_DIR = "output"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 main.py <App名称>")
        print("示例: python3 main.py 微信")
        sys.exit(1)

    app_name_query = " ".join(sys.argv[1:])

    print(f"正在搜索: {app_name_query}")
    print("-" * 40)

    app_info = search_app(app_name_query, COUNTRY)
    if not app_info:
        print(f"[错误] 未找到 App「{app_name_query}」")
        sys.exit(1)

    app_id = app_info["app_id"]
    app_name = app_info["name"]
    print(f"  匹配到: {app_name} (ID: {app_id})")
    print(f"  开发者: {app_info['developer']}")
    print(f"  当前评分: {app_info['rating']:.1f}")
    print(f"  当前版本: {app_info['version']}")

    reviews = fetch_reviews(app_id, COUNTRY)

    if reviews:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in app_name)
        filename = f"{safe_name}_{app_id}_reviews.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        save_to_csv(reviews, filepath)
    else:
        print("  未获取到任何评论")

    print("\n完成！")


if __name__ == "__main__":
    main()
