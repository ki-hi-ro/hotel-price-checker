
import csv
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# 検索条件
today = datetime.now()
stay_date = today + timedelta(days=30)

# 新宿駅から徒歩15分以内の確認済みホテル
HOTELS = [
    {"name": "かどやホテル", "id": "376275", "walk": 3},
    {"name": "ホテルグレイスリー新宿", "id": "309286", "walk": 5},
    {"name": "アパホテル〈新宿御苑前〉", "id": "333633", "walk": 9},
    {"name": "新宿プリンスホテル", "id": "374925", "walk": 5},
    {"name": "新宿アーバンホテル", "id": "321016", "walk": 10},
    {"name": "新宿タウンホテル", "id": "388402", "walk": 15},
    {"name": "ビジネスホテル山城", "id": "358176", "walk": 10},
    {"name": "新宿ワシントンホテル（本館）", "id": "336266", "walk": 8},
    {"name": "プレミアホテル-CABIN-新宿", "id": "304851", "walk": 8},
    {"name": "ホテルたてしな", "id": "349948", "walk": 14},
]


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def get_min_price(hotel):
    """ホテルの最安料金とプラン一覧URLを取得する"""

    url = f"https://www.jalan.net/yad{hotel['id']}/plan/"

    params = {
        "screenId": "UWW3101",
        "yadNo": hotel["id"],
        "reSearchFlg": 1,
        "roomCrack": "100000",
        "smlCd": "138002",
        "distCd": "01",
        "stayYear": stay_date.year,
        "stayMonth": stay_date.month,
        "stayDay": stay_date.day,
        "stayCount": 1,
        "roomCount": 1,
        "adultNum": 1,
        "minPrice": 0,
        "maxPrice": 999999,
        "activeSort": 17,
    }

    response = session.get(
        url,
        params=params,
        timeout=15,
    )
    response.raise_for_status()

    # HTML内の料金JSONを取得
    match = re.search(
        r'"dsgPlanSortData"\s*:\s*',
        response.text,
    )

    if not match:
        raise ValueError("料金データが見つかりません")

    data, _ = json.JSONDecoder().raw_decode(
        response.text[match.end():]
    )

    # 取得したデータの宿泊条件を検証
    conditions = (
        data.get("request_data") or {}
    ).get("search_conditions") or {}

    expected_checkin = stay_date.strftime("%Y-%m-%d")
    expected_checkout = (
        stay_date + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    dates = conditions.get("date") or {}
    rooms = conditions.get("rooms") or []

    if (
        dates.get("checkin_date") != expected_checkin
        or dates.get("checkout_date") != expected_checkout
        or not rooms
        or rooms[0].get("adult_num") != 1
        or rooms[0].get("child_num") != 0
    ):
        raise ValueError("取得した宿泊条件が一致しません")

    prices = [
        plan["price"]
        for plan in data.get("plans", [])
        if isinstance(plan, dict)
        and type(plan.get("price")) in (int, float)
        and plan["price"] > 0
    ]

    if not prices:
        raise ValueError("有効な料金が見つかりません")

    return {
        "ホテル名": hotel["name"],
        "徒歩分数": hotel["walk"],
        "取得日": today.strftime("%Y/%m/%d"),
        "宿泊日": stay_date.strftime("%Y/%m/%d"),
        "最安料金": min(prices),
        "URL": response.url,
    }


# ホテルごとに料金を取得
results = []

for i, hotel in enumerate(HOTELS):
    print(f"取得中: {hotel['name']}")

    try:
        result = get_min_price(hotel)
        results.append(result)
        print(f"  {result['最安料金']:,}円")

    except (requests.RequestException, ValueError,
            json.JSONDecodeError) as e:
        print(f"  取得失敗: {e}")

    # サーバーへの負荷を抑える
    if i < len(HOTELS) - 1:
        time.sleep(2)


if not results:
    print("料金を取得できたホテルがありません")
    raise SystemExit(1)

# 料金の安い順に並べ替え
results.sort(key=lambda row: row["最安料金"])

# 結果表示
print(f"\n宿泊日: {stay_date:%Y/%m/%d}")
print("条件: 大人1名・1泊\n")

for rank, result in enumerate(results, start=1):
    print(
        f"{rank}位 {result['ホテル名']} "
        f"{result['最安料金']:,}円 "
        f"徒歩{result['徒歩分数']}分"
    )
    print(result["URL"])

# CSV出力
csv_path = Path(__file__).resolve().parent / "shinjuku_hotels.csv"

with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "ホテル名",
            "徒歩分数",
            "取得日",
            "宿泊日",
            "最安料金",
            "URL",
        ],
    )
    writer.writeheader()
    writer.writerows(results)

print(f"\nCSV保存完了: {csv_path}")
print(f"取得成功: {len(results)}/{len(HOTELS)}件")