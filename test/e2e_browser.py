"""浏览器自动化验证：中文会议文本生成纪要全流程（复现并验证超时修复）。

核心目标：验证「粘贴中文会议文本 → 生成纪要」在前端不再误报失败、
纪要区域正确渲染、左侧历史出现本次会议。

注册用 API 完成以避开注册弹窗选择器脆弱性；浏览器聚焦核心生成流程。
前置：后端跑在 8000、前端跑在 5173。运行：
    cd backend && source .venv/Scripts/activate
    python ../test/e2e_browser.py
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
待办：李四 7 月 10 日前完成购物车前端；王五 7 月 5 日前提供优惠接口；王五和李四本周四出退款方案；张三负责整体进度协调。
"""


def main():
    username = f"tester_{uuid.uuid4().hex[:6]}"
    password = "test123456"

    # 用 API 注册并拿 token（避开注册弹窗 UI 的选择器脆弱性）
    r = requests.post(f"{API}/auth/register", json={"username": username, "password": password}, timeout=15)
    r.raise_for_status()
    token = r.json()["access_token"]
    print(f"[0] API 注册用户 {username} 成功，已拿 token")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        # 注入 token，模拟已登录（localStorage）
        ctx.add_init_script(
            f"localStorage.setItem('ma_token',{token!r});"
            f"localStorage.setItem('ma_user',JSON.stringify({{user_id:'x',username:{username!r}}}));"
        )
        page = ctx.new_page()

        print(f"[1] 打开 {FRONT}")
        page.goto(FRONT, wait_until="domcontentloaded")
        # 确认已登录（顶栏显示用户名）
        page.wait_for_selector(f"text={username}", timeout=10000)
        print("    已登录，顶栏显示用户名")

        print("[2] 填写会议输入（粘贴中文文本）")
        page.get_by_placeholder("会议名称（可选）").fill("V2.3 周会")
        textarea = page.get_by_placeholder("粘贴会议转写文本…")
        textarea.fill(SAMPLE)

        print("[3] 点击「生成纪要」并等待（最长 180s）…")
        t0 = time.time()
        page.get_by_role("button", name="生成纪要").click()

        # 等待「会议纪要」区域出现 markdown 内容（h2 标题）
        try:
            page.wait_for_selector(".markdown-body h2", timeout=180000)
        except PWTimeout:
            print("    失败：180 秒内未出现纪要内容")
            page.screenshot(path="test_e2e_fail.png")
            browser.close()
            sys.exit(1)
        dt = time.time() - t0
        print(f"    纪要出现，耗时 {dt:.1f}s（原 30s 超时已修复）")

        # 校验纪要区域有实质内容
        body_text = page.locator(".markdown-body").inner_text()
        has_table = "事项" in body_text and "负责人" in body_text
        has_topic = "议题" in body_text or "购物车" in body_text
        has_decision = "决策" in body_text
        print(f"    含待办表格: {has_table} | 含议题: {has_topic} | 含决策: {has_decision}")

        # 校验左侧历史出现这条会议
        print("[4] 校验左侧历史列表")
        # 历史列表加载可能稍滞后，等一下
        page.wait_for_selector(".history-item", timeout=10000)
        history_text = page.locator(".app-sidebar").inner_text()
        in_history = "V2.3" in history_text or "周会" in history_text or "未命名" in history_text
        print(f"    历史中出现本次会议: {in_history}")

        # 点击历史项，确认能切回详情
        print("[5] 点击历史项验证详情回显")
        page.locator(".history-item").first.click()
        page.wait_for_selector(".markdown-body h2", timeout=10000)
        body_after = page.locator(".markdown-body").inner_text()
        reloaded = "会议纪要" in body_after
        print(f"    详情回显正常: {reloaded}")

        page.screenshot(path="test_e2e_ok.png", full_page=True)
        print("[6] 截图已存 test_e2e_ok.png")

        ok = has_table and has_topic and in_history and reloaded
        print(f"\n结论: {'通过 ✅' if ok else '失败 ❌'}")
        browser.close()
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
