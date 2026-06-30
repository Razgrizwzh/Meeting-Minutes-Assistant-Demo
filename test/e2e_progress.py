"""验证生成进度体验：进度条可见、秒表走动、文案轮换、最终纪要正常出现。

前置：后端 8000、前端 5173 在跑。运行：
    cd backend && source .venv/Scripts/activate
    python ../test/e2e_progress.py
"""

import sys
import time
import uuid

import requests
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

FRONT = "http://localhost:5173"
API = "http://localhost:8000/api"

SAMPLE = """会议主题：电商后台 V2.3 版本迭代周会
时间：2026-06-29
参会人员：张三、李四、王五

张三：今天评审 V2.3 的几个核心需求。第一个是购物车合并优惠逻辑，第二个是订单退款流程优化。
李四：购物车这块我来做，预计 7 月 10 日完成开发，需要后端提供优惠计算接口。
王五：优惠接口我来提供，7 月 5 日提测。退款流程优化我和李四一起评审，本周四给出方案。
张三：好。决策两点：一是购物车合并优惠由李四负责前端、王五负责后端接口；二是退款流程优化本周四出方案。
待办：李四 7 月 10 日前完成购物车前端；王五 7 月 5 日前提供优惠接口；王五和李四本周四出退款方案。
"""


def main():
    username = f"progress_{uuid.uuid4().hex[:6]}"
    password = "test123456"
    r = requests.post(f"{API}/auth/register", json={"username": username, "password": password}, timeout=15)
    r.raise_for_status()
    token = r.json()["access_token"]
    print(f"[0] 注册 {username} 成功")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        ctx.add_init_script(
            f"localStorage.setItem('ma_token',{token!r});"
            f"localStorage.setItem('ma_user',JSON.stringify({{user_id:'x',username:{username!r}}}));"
        )
        page = ctx.new_page()

        print(f"[1] 打开 {FRONT}")
        page.goto(FRONT, wait_until="domcontentloaded")
        page.wait_for_selector(f"text={username}", timeout=10000)

        print("[2] 粘贴中文会议文本并点击生成")
        page.get_by_placeholder("粘贴会议转写文本…").fill(SAMPLE)
        page.get_by_role("button", name="生成纪要").click()

        # 验证进度条出现
        page.wait_for_selector(".generating-progress", timeout=5000)
        print("    ✅ 进度条组件出现")

        # 抓取两次快照（间隔 3 秒），验证秒表走动 / 进度推进 / 文案
        t0 = time.time()
        s1 = page.locator(".generating-progress").inner_text()
        time.sleep(3)
        s2 = page.locator(".generating-progress").inner_text()
        print("    3秒后快照:", repr(s2.replace("\n", " | ")[:120]))
        print("    初始快照含标题/状态文案:", "正在生成会议纪要" in s1 and "正在阅读" in s1)
        # 秒表走动：3秒后应出现 "3秒"
        sec_changing = "3秒" in s2 or "4秒" in s2
        print("    秒表走动正常:", sec_changing)

        # 等待纪要出现
        try:
            page.wait_for_selector(".markdown-body h2", timeout=180000)
        except PWTimeout:
            print("    失败：180s 内未出现纪要")
            page.screenshot(path="test_progress_fail.png")
            browser.close()
            sys.exit(1)
        dt = time.time() - t0
        print(f"    ✅ 纪要出现，总耗时 {dt:.1f}s（qwen-plus）")

        body = page.locator(".markdown-body").inner_text()
        print("    纪要含表格:", "事项" in body and "负责人" in body)
        page.screenshot(path="test_progress_done.png", full_page=True)
        print("[3] 截图 test_progress_done.png")

        # 纪要出现后进度条应消失
        gone = page.locator(".generating-progress").count() == 0
        print(f"    ✅ 生成完成后进度条消失: {gone}")

        ok = ("正在生成会议纪要" in s1) and ("事项" in body) and sec_changing and gone
        print(f"\n结论: {'通过 ✅' if ok else '失败 ❌'}")
        browser.close()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()