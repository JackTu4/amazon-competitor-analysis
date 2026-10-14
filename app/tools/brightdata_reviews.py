import json
import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from app.models.review import Review

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)
API_KEY = os.getenv("BRIGHTDATA_API_KEY")
DATASET_ID = os.getenv("BRIGHTDATA_DATASET_ID")
BASE_URL = "https://api.brightdata.com/datasets/v3"

def collect_amazon_reviews(
    asin: str,
    max_reviews: int = 3,
    poll_interval: int = 10,
    max_wait: int = 600,
)-> list[Review]:
    """采集 Amazon 评论并保存到本地 JSON。"""

    if not API_KEY:
        raise ValueError("没有读取到 BRIGHTDATA_API_KEY")
    if not DATASET_ID:
        raise ValueError("没有读取到 BRIGHTDATA_DATASET_ID")
    if not asin or len(asin.strip()) != 10:
        raise ValueError("请传入有效的 Amazon ASIN")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    trigger_url = f"{BASE_URL}/trigger"
    params = {
        "dataset_id": DATASET_ID,
        "format": "json",
    }
    payload = [
        {
            "url": f"https://www.amazon.com/product-reviews/{asin.strip()}/",
            "max_reviews": max_reviews,
            "reviews_to_not_include": [],
            "variation_specific": False,
        }
    ]
    response = requests.post(
        trigger_url,
        params=params,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    task = response.json()

    snapshot_id = task.get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError(f"没有获取到 snapshot_id：{task}")

    print("采集任务已提交，Snapshot ID：", snapshot_id)

    deadline = time.monotonic() + max_wait
    status_url = f"{BASE_URL}/progress/{snapshot_id}"

    while time.monotonic() < deadline:
        status_response = requests.get(
            status_url,
            headers=headers,
            timeout=30,
        )
        status_response.raise_for_status()
        status_data = status_response.json()

        status = status_data.get("status")
        print("当前任务状态：", status)

        if status == "ready":
            break

        if status in {"failed", "error"}:
            raise RuntimeError(f"评论采集失败：{status_data}")

        time.sleep(poll_interval)
    else:
        raise TimeoutError(
            f"等待评论结果超时。Snapshot ID：{snapshot_id}"
        )

    result_url = f"{BASE_URL}/snapshot/{snapshot_id}"
    result_response = requests.get(
        result_url,
        headers=headers,
        params={"format": "json"},
        timeout=120,
        )
    result_response.raise_for_status()
    data = result_response.json()

    if isinstance(data, list):
        reviews = data
    elif isinstance(data, dict):
        reviews = data.get("data", [])
        if not isinstance(reviews, list):
            raise ValueError(f"返回结果结构不符合预期：{data.keys()}")
    else:
        raise ValueError("Bright Data 返回了无法识别的数据格式")

        # 5. 保存到本地
    output_dir = PROJECT_ROOT / "app" / "data" / "reviews"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{asin.strip()}_reviews.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    print(f"评论数量：{len(reviews)}")
    print(f"结果已保存：{output_file}")
    review_objects = [
        Review.model_validate(item)
        for item in reviews
    ]

    return review_objects
