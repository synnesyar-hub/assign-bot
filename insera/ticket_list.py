# insera/ticket_list.py

import re
import math
from config import TICKET_COLUMNS


async def fetch_ticket_list(page, url, table_id="datalistInboxAllticketV2"):
    await page.goto(url, wait_until="load")
    await page.wait_for_load_state("networkidle")

    table = page.locator(f"#{table_id}")
    await table.wait_for(state="visible", timeout=15000)

    header_cells = table.locator("thead th")
    header_count = await header_cells.count()

    headers = []
    for i in range(header_count):
        text = await header_cells.nth(i).text_content()
        headers.append((text or "").strip())

    empty_row = table.locator("tbody tr.empty")
    if await empty_row.count() > 0:
        return []

    rows = table.locator("tbody tr")
    row_count = await rows.count()

    results = []
    for r in range(row_count):
        row = rows.nth(r)
        cells = row.locator("td")
        cell_count = await cells.count()

        raw_row = {}
        for c in range(min(cell_count, len(headers))):
            try:
                value = await cells.nth(c).text_content(timeout=5000)
            except Exception as e:
                print(f"[WARN] Gagal baca cell row={r} col={c}: {e}")
                value = ""
            key = headers[c]
            raw_row[key] = (value or "").strip()

        filtered_row = {col: raw_row.get(col, "") for col in TICKET_COLUMNS}
        results.append(filtered_row)

    return results


async def get_total_items(page) -> int:
    """
    Baca total item dari teks '<span class="pagebanner">X items found...</span>'
    yang muncul setelah fetch_ticket_list() dipanggil (asumsi masih di halaman yang sama).
    Return 0 kalau tidak ketemu / format tidak dikenali.
    """
    banner = page.locator("span.pagebanner")
    if await banner.count() == 0:
        return 0

    text = await banner.first.inner_text()
    match = re.search(r"([\d,]+)\s+items?\s+found", text, re.IGNORECASE)
    if not match:
        return 0

    number_str = match.group(1).replace(",", "")
    return int(number_str)


def _set_page_param(url: str, page_prefix: str, page_number: int) -> str:
    pattern = rf"({re.escape(page_prefix)}-p=)\d+"
    return re.sub(pattern, rf"\g<1>{page_number}", url)


def _get_page_size(url: str, page_prefix: str, default: int = 10) -> int:
    pattern = rf"{re.escape(page_prefix)}-ps=(\d+)"
    match = re.search(pattern, url)
    if match:
        return int(match.group(1))
    return default


async def fetch_ticket_list_paginated(page, base_url, page_prefix, table_id):
    """
    Ambil SEMUA halaman berdasarkan total item yang dilaporkan sistem
    (bukan menebak dari halaman kosong, karena sistem bisa mengembalikan
    data lama alih-alih kosong saat halaman melebihi batas).
    """
    page_size = _get_page_size(base_url, page_prefix)

    # ambil halaman 1 dulu untuk tahu total item
    url_page1 = _set_page_param(base_url, page_prefix, 1)
    first_page_results = await fetch_ticket_list(page, url_page1, table_id=table_id)

    total_items = await get_total_items(page)

    if total_items == 0:
        print("[INFO] Tidak ada tiket ditemukan atau gagal baca total item.")
        return first_page_results

    total_pages = math.ceil(total_items / page_size)
    print(f"[INFO] Total {total_items} tiket, page size {page_size} -> {total_pages} halaman.")

    all_results = list(first_page_results)
    print(f"[INFO] Halaman 1/{total_pages} - Total terkumpul: {len(all_results)}")

    for page_number in range(2, total_pages + 1):
        url = _set_page_param(base_url, page_prefix, page_number)
        results = await fetch_ticket_list(page, url, table_id=table_id)
        all_results.extend(results)
        print(f"[INFO] Halaman {page_number}/{total_pages} - Total terkumpul: {len(all_results)}")

    return all_results