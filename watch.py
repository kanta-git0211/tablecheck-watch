"""TableCheck の空き状況を見て、空きがあれば ntfy でスマホに通知する。
予約・フォーム送信は一切しない（見るだけ）。
"""
import os
import sys
import urllib.request

from playwright.sync_api import sync_playwright

PARTY = os.environ.get("PARTY", "2")
WEEKS = int(os.environ.get("WEEKS", "12"))  # 何週先まで見るか
TOPIC = os.environ.get("NTFY_TOPIC", "")
TEST = os.environ.get("TEST_NOTIFY") == "1"

SHOPS = [
    ("eman", "https://www.tablecheck.com/ja/shops/eman/reserve"),
    ("静龍苑", "https://www.tablecheck.com/ja/shops/seiryuen/reserve"),
]

# 表の中で「空き」を拾う JS
READ_WEEK = r"""
() => {
  const body = document.querySelector('#timetable-body');
  if (!body) return {ok:false};
  const heads = [...body.querySelectorAll('td.wday')];
  const months = [...document.querySelectorAll('#timetable-panel th.month')]
      .flatMap(th => Array(parseInt(th.getAttribute('colspan')||'1')).fill(th.textContent.trim()));
  const days = heads.map((td,i) => (months[i]||'') + td.querySelector('.date-num').textContent.trim() + '日');
  const open = [];
  heads.forEach((td,i) => { if (!td.classList.contains('day-closed')) open.push(days[i]); });
  // 時間枠の行（見出し行・ダミー行以外）で × 以外のマス
  const slots = [];
  const rows = [...document.querySelectorAll('#timetable-panel tbody tr')]
      .filter(tr => tr.id !== 'timetable-body' && !tr.classList.contains('mobile_week_change')
                    && !tr.classList.contains('timetable-fake-row') && tr.querySelector('td'));
  rows.forEach(tr => {
    const label = (tr.querySelector('th')||{}).textContent || '';
    [...tr.querySelectorAll('td')].forEach((td,i) => {
      if (!td.className.includes('not_available') && td.textContent.trim() !== '')
        slots.push((days[i]||'?') + ' ' + label.trim() + ' ' + td.textContent.trim());
    });
  });
  const next = document.querySelector('#timetable-panel th.time-right a.next-week');
  return {ok:true, first: days[0], open, slots, hasNext: !!next && getComputedStyle(next).display !== 'none'};
}
"""


def notify(title_ascii: str, msg: str, url: str):
    if not TOPIC:
        print("NTFY_TOPIC 未設定のため通知スキップ:", msg)
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=msg.encode("utf-8"),
        headers={"Title": title_ascii, "Click": url, "Priority": "high", "Tags": "fork_and_knife"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=20)


def check(page, name, url):
    page.goto(url, wait_until="networkidle", timeout=60000)
    sel = page.locator('select:has(option:text-is("-- 人数 --"))').first
    sel.select_option(PARTY)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    found, seen = [], []
    for _ in range(WEEKS):
        r = page.evaluate(READ_WEEK)
        if not r.get("ok"):
            raise RuntimeError(f"{name}: 予約状況の表が見つからない（ページ構成が変わった可能性）")
        seen.append(r["first"])
        found += r["open"] + r["slots"]
        if not r["hasNext"]:
            break
        page.locator('#timetable-panel th.time-right a.next-week').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
    return sorted(set(found)), seen


def main():
    if TEST:
        notify("TEST", "テスト通知です。これが届けば通知設定はOK", SHOPS[0][1])
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="ja-JP")
        for name, url in SHOPS:
            try:
                found, seen = check(page, name, url)
                print(f"{name}: 確認した週 {seen[0]}〜{seen[-1]} / 空き {found or 'なし'}")
                if found:
                    notify("Table available!", f"【空きあり】{name} {PARTY}名: " + "、".join(found[:10]), url)
            except Exception as e:  # 1店失敗してももう1店は見る
                print(f"{name}: エラー {e}")
                errors.append(name)
        browser.close()
    if errors:
        sys.exit(1)  # Actions の画面で失敗が分かるように


if __name__ == "__main__":
    main()
