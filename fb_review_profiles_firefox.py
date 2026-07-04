#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
fb_review_profiles_firefox.py

Mở lần lượt profile Facebook bằng Firefox qua Selenium.
Điểm mới:
- Nhấn s = skip thì tự đóng tab profile hiện tại.
- Có thể bật --close-after-action để Enter/k/u cũng tự đóng tab sau khi đánh dấu.

Cài:
    pip install -r requirements.txt

Chạy:
    python fb_review_profiles_firefox.py --input friends_input.txt

Chỉ lấy người 0 tương tác:
    python fb_review_profiles_firefox.py --input friends_input.txt --only-zero

Dùng dạng facebook.com/<id>:
    python fb_review_profiles_firefox.py --input friends_input.txt --url-style slash

Đóng tab sau mọi hành động:
    python fb_review_profiles_firefox.py --input friends_input.txt --close-after-action

Phím:
    Enter = reviewed
    k     = keep
    u     = đã tự gỡ bằng tay
    s     = skip và đóng tab
    b     = quay lại
    q     = thoát
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


PROGRESS_FILE = "review_progress.json"
RESULTS_FILE = "review_results.csv"
QUEUE_FILE = "review_queue.csv"
IDS_ONLY_FILE = "ids_only.txt"
FIREFOX_PROFILE_DIR = "firefox_fb_profile"


def parse_records(text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in text.splitlines()]
    records: list[dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if re.fullmatch(r"\d{6,20}", line):
            fb_id = line
            j = i + 1

            while j < len(lines) and not lines[j]:
                j += 1

            name = ""
            if j < len(lines) and not re.fullmatch(r"\d{6,20}", lines[j]):
                name = lines[j]

            likes = comments = messages = None
            k = j + 1

            while k < len(lines) and not re.fullmatch(r"\d{6,20}", lines[k]):
                current = lines[k]

                if "Lượt thích" in current or "thích" in current.lower():
                    m = re.search(r"(\d+)\s*/\s*(\d+)", current)
                    if m:
                        likes = int(m.group(1))
                        comments = int(m.group(2))

                if "Số tin nhắn" in current or "tin nhắn" in current.lower():
                    m = re.search(r"(\d+)", current)
                    if m:
                        messages = int(m.group(1))

                k += 1

            records.append({
                "id": fb_id,
                "name": name,
                "likes": likes,
                "comments": comments,
                "messages": messages,
            })
            i = k
        else:
            i += 1

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for record in records:
        fb_id = str(record["id"])
        if fb_id not in seen:
            unique.append(record)
            seen.add(fb_id)

    return unique


def make_url(fb_id: str, style: str) -> str:
    if style == "slash":
        return f"https://facebook.com/{fb_id}"

    return f"https://facebook.com/profile.php?id={fb_id}"


def is_zero_interaction(record: dict[str, Any]) -> bool:
    return (
        (record.get("likes") in (0, None))
        and (record.get("comments") in (0, None))
        and (record.get("messages") in (0, None))
    )


def load_progress() -> dict[str, str]:
    path = Path(PROGRESS_FILE)
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"[WARN] {PROGRESS_FILE} bị lỗi JSON, bỏ qua progress cũ.")
        return {}


def save_progress(progress: dict[str, str]) -> None:
    Path(PROGRESS_FILE).write_text(
        json.dumps(progress, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_result(record: dict[str, Any], status: str, url: str) -> None:
    path = Path(RESULTS_FILE)
    write_header = not path.exists()

    with path.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "name",
                "likes",
                "comments",
                "messages",
                "status",
                "url",
            ],
        )

        if write_header:
            writer.writeheader()

        writer.writerow({
            "id": record.get("id", ""),
            "name": record.get("name", ""),
            "likes": "" if record.get("likes") is None else record.get("likes"),
            "comments": "" if record.get("comments") is None else record.get("comments"),
            "messages": "" if record.get("messages") is None else record.get("messages"),
            "status": status,
            "url": url,
        })


def export_files(records: list[dict[str, Any]], url_style: str) -> None:
    with open(QUEUE_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name", "likes", "comments", "messages", "url"],
        )
        writer.writeheader()

        for record in records:
            row = dict(record)
            row["likes"] = "" if row.get("likes") is None else row.get("likes")
            row["comments"] = "" if row.get("comments") is None else row.get("comments")
            row["messages"] = "" if row.get("messages") is None else row.get("messages")
            row["url"] = make_url(str(record["id"]), url_style)
            writer.writerow(row)

    Path(IDS_ONLY_FILE).write_text(
        "\n".join(str(record["id"]) for record in records),
        encoding="utf-8",
    )


def find_default_input() -> Path | None:
    candidates = [
        Path("friends_input.txt"),
        Path("friends.txt"),
        Path("Pasted text(2).txt"),
    ]

    for path in candidates:
        if path.exists():
            return path

    txt_files = sorted(Path(".").glob("*.txt"))
    return txt_files[0] if txt_files else None


def start_firefox() -> webdriver.Firefox:
    profile_dir = Path(FIREFOX_PROFILE_DIR).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    options = FirefoxOptions()

    # Dùng profile riêng để bạn login Facebook một lần rồi lần sau nhớ đăng nhập.
    # Lưu ý: đây KHÔNG phải profile Firefox mặc định của máy.
    options.add_argument("-profile")
    options.add_argument(str(profile_dir))

    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.maximize_window()
    except Exception:
        pass

    driver.get("about:blank")
    return driver


def open_profile_tab(driver: webdriver.Firefox, url: str) -> str:
    driver.execute_script("window.open(arguments[0], '_blank');", url)
    handle = driver.window_handles[-1]
    driver.switch_to.window(handle)
    return handle


def close_tab_safe(driver: webdriver.Firefox, handle: str | None) -> None:
    if not handle:
        return

    try:
        if handle in driver.window_handles:
            driver.switch_to.window(handle)
            driver.close()
    except Exception as exc:
        print(f"[WARN] Không đóng được tab: {exc}")

    try:
        if driver.window_handles:
            driver.switch_to.window(driver.window_handles[0])
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mở profile Facebook bằng Firefox để review thủ công, skip thì tự đóng tab."
    )
    parser.add_argument("--input", "-i", help="File danh sách ID/tên. Ví dụ: friends_input.txt")
    parser.add_argument("--start", type=int, default=1, help="Bắt đầu từ vị trí thứ mấy, mặc định 1.")
    parser.add_argument("--delay", type=float, default=1.0, help="Nghỉ mấy giây sau khi mở tab, mặc định 1.0.")
    parser.add_argument("--only-zero", action="store_true", help="Chỉ lấy người có like/comment/message đều bằng 0.")
    parser.add_argument("--include-reviewed", action="store_true", help="Mở lại cả người đã review trước đó.")
    parser.add_argument("--export-only", action="store_true", help="Chỉ xuất review_queue.csv và ids_only.txt, không mở trình duyệt.")
    parser.add_argument(
        "--url-style",
        choices=["profilephp", "slash"],
        default="profilephp",
        help="profilephp = facebook.com/profile.php?id=ID, slash = facebook.com/ID",
    )
    parser.add_argument(
        "--close-after-action",
        action="store_true",
        help="Đóng tab sau cả Enter/k/u. Mặc định chỉ s=skip mới đóng tab.",
    )

    args = parser.parse_args()

    input_path = Path(args.input) if args.input else find_default_input()
    if not input_path or not input_path.exists():
        print("Không tìm thấy file input.")
        print("Hãy đặt file tên friends_input.txt hoặc chạy:")
        print("    python fb_review_profiles_firefox.py --input ten_file.txt")
        return 1

    text = input_path.read_text(encoding="utf-8", errors="ignore")
    records = parse_records(text)

    if args.only_zero:
        records = [record for record in records if is_zero_interaction(record)]

    progress = load_progress()

    if not args.include_reviewed:
        records = [record for record in records if str(record["id"]) not in progress]

    if args.start > 1:
        records = records[args.start - 1 :]

    if not records:
        print("Không còn profile nào để mở.")
        return 0

    export_files(records, args.url_style)

    print(f"\nInput: {input_path}")
    print(f"Số profile trong hàng chờ: {len(records)}")
    print("Lần đầu Firefox mở profile riêng, bạn cần login Facebook trong cửa sổ đó.")
    print("Tool chỉ mở link/đóng tab, không tự click và không tự gỡ bạn bè.\n")

    if args.export_only:
        print(f"Đã xuất {QUEUE_FILE} và {IDS_ONLY_FILE}")
        return 0

    try:
        driver = start_firefox()
    except Exception as exc:
        print("[ERROR] Không mở được Firefox Selenium.")
        print("Thử cài lại:")
        print("    pip install -U selenium webdriver-manager")
        print("Và đảm bảo máy đã cài Firefox.")
        print(f"Chi tiết lỗi: {exc}")
        return 1

    index = 0
    current_handle: str | None = None

    while 0 <= index < len(records):
        record = records[index]
        fb_id = str(record["id"])
        name = record.get("name") or "(không có tên)"
        url = make_url(fb_id, args.url_style)

        print("=" * 70)
        print(f"[{index + 1}/{len(records)}] {name}")
        print(f"ID: {fb_id}")
        print(
            f"Like/comment/message: "
            f"{record.get('likes')}/{record.get('comments')}/{record.get('messages')}"
        )
        print(f"URL: {url}")

        try:
            current_handle = open_profile_tab(driver, url)
            time.sleep(args.delay)
        except Exception as exc:
            print(f"[ERROR] Không mở được tab: {exc}")
            index += 1
            continue

        cmd = input(
            "Enter=reviewed | k=keep | u=unfriended manually | s=skip+close | b=back | q=quit: "
        ).strip().lower()

        if cmd == "q":
            print("Đã thoát.")
            break

        if cmd == "b":
            close_tab_safe(driver, current_handle)
            index = max(0, index - 1)
            continue

        if cmd == "s":
            close_tab_safe(driver, current_handle)
            index += 1
            continue

        status = {
            "": "REVIEWED",
            "k": "KEEP",
            "u": "UNFRIENDED_MANUALLY",
        }.get(cmd, "REVIEWED")

        progress[fb_id] = status
        save_progress(progress)
        append_result(record, status, url)

        if args.close_after_action:
            close_tab_safe(driver, current_handle)

        index += 1

    print("\nXong.")
    print(f"Progress: {PROGRESS_FILE}")
    print(f"Kết quả: {RESULTS_FILE}")
    print("Firefox vẫn có thể đang mở. Bạn tự tắt cửa sổ khi xong.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
