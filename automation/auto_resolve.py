# automation/auto_resolve.py

import asyncio
from .modal import modal_handler, modal_confirm
from services.db_service import update_ticket_fields, sync_tickets, get_all_incs
from insera.ticket_list import fetch_ticket_list_paginated
from config import INS_TICKET_LIST_URL_1, INS_TICKET_LIST_URL_2, INS_TICKET_LIST_URL_3, INS_URL, INS_USERNAME


class TicketNotFoundError(Exception):
    pass

SOLUTION_MAP = {
    "50": "SQM002",
    "28": "RCIND030",
}

WORK_ORDER_GRID_ID = "formgrid_child_id_1_ticketUserInformationAfterRunCrud_work_order_form_524313410947936751111_188430514919531537511953153751"

BOOKMARK_CONFIG = {
    "bookmark1": {
        "url": INS_TICKET_LIST_URL_1,
        "page_prefix": "d-5564009",
        "table_id": "datalistInboxAllticketV2",
        "worksheet": "Database",
    },
    "bookmark2": {
        "url": INS_TICKET_LIST_URL_2,
        "page_prefix": "d-5564009",
        "table_id": "datalistInboxAllticketV2",
        "worksheet": "Database2",
    },
    "bookmark3": {
        "url": INS_TICKET_LIST_URL_3,
        "page_prefix": "d-6878233",
        "table_id": "datalistGlobal",
        "worksheet": "Database3",
    },
}


async def goto_with_retry(page, url, retries=3, timeout=60000, wait_between=3000, wait_until="load"):

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout)
            return
        except Exception as e:
            last_err = e
            print(f"[WARN] goto({url}) gagal (percobaan {attempt}/{retries}): {e}")
            if attempt < retries:
                await page.wait_for_timeout(wait_between)
    raise last_err


async def fetch_and_sync(page, url, page_prefix, table_id, worksheet_name):
    tickets = await fetch_ticket_list_paginated(
        page, url, page_prefix=page_prefix, table_id=table_id
    )
    print(f"[INFO] {len(tickets)} tiket ditemukan dari {worksheet_name}.")
    await sync_tickets(tickets, worksheet_name=worksheet_name)
    return tickets


async def _fetch_page_range(page, base_url, page_prefix, table_id, page_numbers, worker_id):
    """
    Fetch beberapa nomor halaman tertentu saja (bukan semua) -- dipakai
    oleh fetch_and_sync_parallel untuk membagi pekerjaan scraping ke
    beberapa page/tab sekaligus.
    """
    from insera.ticket_list import fetch_ticket_list, _set_page_param

    all_results = []
    for page_number in page_numbers:
        url = _set_page_param(base_url, page_prefix, page_number)
        print(f"[Scrape][Worker-{worker_id}] Mengambil halaman {page_number}...")
        results = await fetch_ticket_list(page, url, table_id=table_id)
        all_results.extend(results)
    return all_results


async def fetch_and_sync_parallel(pages, url, page_prefix, table_id, worksheet_name):
    """
    Versi paralel dari fetch_and_sync -- bagi rentang HALAMAN (bukan
    tiket) ke beberapa page/tab, fetch bersamaan, gabungkan semua hasil,
    baru panggil sync_tickets SATU KALI dengan data gabungan penuh.

    PENTING: sync_tickets tidak boleh dipanggil terpisah per worker --
    fungsi itu menghapus baris yang "tidak relevan" berdasarkan list
    tiket yang di-pass, jadi kalau dipanggil dengan data parsial akan
    menghapus tiket milik worker lain secara keliru.
    """
    from insera.ticket_list import fetch_ticket_list, get_total_items, _set_page_param, _get_page_size
    import math

    page_size = _get_page_size(url, page_prefix)

    # ambil halaman 1 dulu (di page/tab pertama) untuk tahu total item
    url_page1 = _set_page_param(url, page_prefix, 1)
    first_page_results = await fetch_ticket_list(pages[0], url_page1, table_id=table_id)
    total_items = await get_total_items(pages[0])

    if total_items == 0:
        print(f"[Scrape][Parallel] Tidak ada tiket ditemukan untuk {worksheet_name}.")
        await sync_tickets(first_page_results, worksheet_name=worksheet_name)
        return first_page_results

    total_pages = math.ceil(total_items / page_size)
    print(f"[Scrape][Parallel] Total {total_items} tiket, page size {page_size} -> {total_pages} halaman, "
          f"dibagi ke {len(pages)} worker.")

    if total_pages <= 1:
        await sync_tickets(first_page_results, worksheet_name=worksheet_name)
        return first_page_results

    remaining_pages = list(range(2, total_pages + 1))
    chunks = _split_into_chunks(remaining_pages, len(pages))

    tasks = [
        _fetch_page_range(pages[i], url, page_prefix, table_id, chunks[i], i + 1)
        for i in range(len(chunks))
    ]
    results_per_worker = await asyncio.gather(*tasks)

    all_results = list(first_page_results)
    for r in results_per_worker:
        all_results.extend(r)

    print(f"[Scrape][Parallel] Selesai fetch {len(all_results)} tiket dari {total_pages} halaman.")

    # SATU kali sync dengan data gabungan penuh -- ini yang mencegah
    # masalah penghapusan keliru.
    await sync_tickets(all_results, worksheet_name=worksheet_name)
    return all_results


async def sync_service_id_descriptions(page, worksheet_name="Database2"):

    from services.db_service import get_pool, _table_name

    pool = await get_pool()
    table = _table_name(worksheet_name)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT incident FROM {table}
            WHERE service_type IN ('ASTINET', 'VPNIP')
            AND (service_id_description IS NULL OR service_id_description = '')
        """)

    inc_numbers = [r["incident"] for r in rows]
    print(f"[ServiceID] {len(inc_numbers)} tiket ASTINET/VPNIP perlu dicek deskripsinya.")

    for inc_number in inc_numbers:
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except Exception as e:
            print(f"[ERR] Resolve gagal untuk {inc_number}: {e}")
            await recover_to_find_incident_page(page)
            continue

        desc = await fetch_service_id_description(page, record_id)
        if desc:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE {table} SET service_id_description = $1 WHERE incident = $2",
                    desc, inc_number
                )
            print(f"[OK] {inc_number} -> {desc}")


async def fetch_bookmark1(page):
    cfg = BOOKMARK_CONFIG["bookmark1"]
    return await fetch_and_sync(page, cfg["url"], cfg["page_prefix"], cfg["table_id"], cfg["worksheet"])


async def fetch_bookmark2(page):
    cfg = BOOKMARK_CONFIG["bookmark2"]
    return await fetch_and_sync(page, cfg["url"], cfg["page_prefix"], cfg["table_id"], cfg["worksheet"])


async def fetch_bookmark3(page):
    cfg = BOOKMARK_CONFIG["bookmark3"]
    return await fetch_and_sync(page, cfg["url"], cfg["page_prefix"], cfg["table_id"], cfg["worksheet"])


fetch_and_store_bookmark2 = fetch_bookmark2


async def fetch_service_id_description(page, ticket_id):

    url = f"https://oss-incident.telkom.co.id/jw/web/userview/ticketIncidentService/ticketIncidentService/_/allTicketList?_mode=edit&id={ticket_id}"
    await page.goto(url, wait_until="load")
    await page.wait_for_load_state("networkidle")

    try:
        field = page.locator("#description_serviceid")
        await field.wait_for(state="attached", timeout=8000)
        value = await field.input_value()
        return value.strip()
    except Exception as e:
        print(f"[WARN] Gagal ambil description_serviceid untuk {ticket_id}: {e}")
        return ""


async def recover_to_find_incident_page(page, timeout=20000):
    try:
        await page.goto(INS_URL["home"], wait_until="load")
        await page.wait_for_load_state("networkidle")
        await page.locator("#findIncidentGlobal").wait_for(state="visible", timeout=timeout)
    except Exception as e:
        print(f"[WARN] Gagal recover ke halaman find incident: {e}")


async def resolve_inc_to_record_id(page, inc_number, timeout=20000):
    """
    Cari INC lewat search global. Kalau ticket memang tidak ada di sistem,
    search ini akan menampilkan dialog .vex "Ticket Not Found" -- deteksi
    itu secara eksplisit dan lempar exception yang jelas, jangan biarkan
    caller menebak-nebak dari timeout form di halaman detail.
    """
    find_field = page.locator("#findIncidentGlobal")
    await find_field.wait_for(state="attached", timeout=timeout)
    await find_field.wait_for(state="visible", timeout=timeout)

    await find_field.fill(inc_number)
    await find_field.press("Enter")

    # tunggu SALAH SATU dari dua kemungkinan: navigasi berhasil (ada "id=" di URL)
    # ATAU dialog "Ticket Not Found" muncul.
    elapsed = 0
    interval = 300
    while elapsed < timeout:
        current_url = page.url
        if "id=" in current_url and ("viewFindIncedent" in current_url or "allTicketListRepo" in current_url):
            record_id = current_url.split("id=")[-1].split("&")[0]
            return record_id

        vex_msg = await _peek_vex_message(page)
        if vex_msg is not None:
            if "not found" in vex_msg.lower():
                raise TicketNotFoundError(f"INC {inc_number} tidak ditemukan di sistem (Ticket Not Found).")
            else:
                raise Exception(f"Search INC {inc_number} menampilkan dialog tak terduga: \"{vex_msg}\"")

        await page.wait_for_timeout(interval)
        elapsed += interval

    raise Exception(f"Gagal resolve INC {inc_number}: timeout {timeout}ms tanpa navigasi maupun dialog (url terakhir: {page.url})")


async def _click_with_retry(page, selector, retries=3, click_timeout=15000, wait_between=2000, label=""):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            await page.locator(selector).click(timeout=click_timeout)
            return
        except Exception as e:
            last_err = e
            print(f"[WARN] Klik {label or selector} gagal (percobaan {attempt}/{retries}): {e}")
            await page.wait_for_timeout(wait_between)
    raise last_err


async def _wait_block_overlay_gone(page, timeout_ms=20000):
    overlay = page.locator(".blockUI.blockOverlay")
    elapsed = 0
    interval = 500
    while elapsed < timeout_ms:
        try:
            count = await overlay.count()
        except Exception as e:
            # FIX: "Execution context was destroyed" terjadi kalau halaman
            # sedang bernavigasi/reload tepat saat count() dipanggil --
            # error transien, bukan bug logic. Tunggu sebentar, lalu retry
            # count() alih-alih langsung melempar exception ke caller.
            if "Execution context was destroyed" in str(e) or "context was destroyed" in str(e).lower():
                print(f"[INFO] Halaman sedang bernavigasi saat cek overlay, tunggu sebentar & retry.")
                await page.wait_for_timeout(1000)
                elapsed += 1000
                continue
            raise

        if count == 0:
            return True
        await page.wait_for_timeout(interval)
        elapsed += interval

    print(f"[WARN] Overlay .blockUI.blockOverlay masih ada setelah {timeout_ms}ms, coba hapus paksa.")
    try:
        await page.evaluate("if (window.jQuery) { $.unblockUI(); }")
        await page.wait_for_timeout(300)
    except Exception:
        pass
    return False


async def _peek_vex_message(page):
    vex_overlay = page.locator(".vex")
    if await vex_overlay.count() == 0:
        return None

    msg_locator = page.locator(".vex-dialog-message")
    if await msg_locator.count() > 0:
        try:
            return (await msg_locator.first.inner_text()).strip()
        except Exception:
            pass
    return ""


_KNOWN_BENIGN_VEX_SNIPPETS = (
    "cannot read properties of undefined (reading 'touppercase')",
    "$.unblockui is not a function",
)


def _is_benign_vex_message(msg: str) -> bool:
    if not msg:
        return False
    lowered = msg.lower()
    return any(snippet in lowered for snippet in _KNOWN_BENIGN_VEX_SNIPPETS)


async def _dismiss_vex_dialog(page, context_label=""):
    vex_overlay = page.locator(".vex")
    if await vex_overlay.count() == 0:
        return None

    msg_text = await _peek_vex_message(page)

    if _is_benign_vex_message(msg_text):
        print(f"[INFO] Dialog .vex (dikenal, diabaikan){f' saat {context_label}' if context_label else ''}.")
    else:
        print(f"[WARN] Dialog .vex terdeteksi{f' saat {context_label}' if context_label else ''}: \"{msg_text}\"")

    btn_primary = page.locator(".vex-dialog-button-primary")
    if await btn_primary.count() > 0:
        try:
            await btn_primary.first.click(timeout=3000)
            await page.wait_for_timeout(500)
            return msg_text
        except Exception:
            pass

    try:
        await page.evaluate(
            "document.querySelectorAll('.vex, .vex-overlay, .vex-content').forEach(el => el.remove())"
        )
    except Exception:
        pass
    return msg_text


async def _wait_measurement_category_or_vex(page, timeout_ms=25000, interval_ms=500, settle_ms=3000):
    """
    Tunggu #measurement_category terisi ATAU dialog .vex muncul.

    CATATAN: beberapa error JS di sisi website (mis. "$.unblockUI is not a
    function") ternyata TIDAK menghentikan kalkulasi AJAX-nya sendiri --
    cuma gagal di step UI cleanup setelahnya. Status ONT & ONU RX terbukti
    tetap terisi normal meski dialog ini muncul. Jadi begitu .vex terdeteksi,
    JANGAN langsung menyerah -- bersihkan dialognya dan tetap lanjut
    menunggu value, sampai timeout habis.
    """
    field = page.locator("#measurement_category")
    elapsed = 0
    value = ""
    vex_seen = None

    while elapsed < timeout_ms:
        value = await field.input_value()
        if value.strip():
            break

        vex_msg = await _peek_vex_message(page)
        if vex_msg is not None:
            if vex_seen is None:
                vex_seen = vex_msg
                if not _is_benign_vex_message(vex_msg):
                    print(f"[INFO] Dialog .vex muncul saat tunggu measurement_category (\"{vex_msg}\"), bersihkan & tetap lanjut tunggu value.")
            await _dismiss_vex_dialog(page, context_label="_wait_measurement_category_or_vex")

        await page.wait_for_timeout(interval_ms)
        elapsed += interval_ms

    if not value.strip():
        # Jaring pengaman terakhir: beri sedikit waktu ekstra, barangkali
        # AJAX baru saja selesai tepat di ambang timeout (terbukti terjadi
        # untuk sebagian tiket yang manual di web-nya normal).
        await page.wait_for_timeout(3000)
        value = await field.input_value()

        if not value.strip():
            print(f"[WARN] #measurement_category masih kosong setelah {timeout_ms}ms (+3s ekstra), lanjut dengan nilai apa adanya.")
            return value, vex_seen
        else:
            print(f"[INFO] #measurement_category akhirnya terisi setelah jeda ekstra: {value}")

    # Value sudah ada (mungkin cuma default "UNSPEC" sebelum AJAX selesai) --
    # tunggu sebentar lagi untuk memastikan AJAX benar-benar tuntas.
    settled_elapsed = 0
    while settled_elapsed < settle_ms:
        vex_msg = await _peek_vex_message(page)
        if vex_msg is not None:
            if vex_seen is None:
                vex_seen = vex_msg
            await _dismiss_vex_dialog(page, context_label="_wait_measurement_category_or_vex (settle)")
        await page.wait_for_timeout(interval_ms)
        settled_elapsed += interval_ms

    final_value = await field.input_value()
    return (final_value if final_value.strip() else value), vex_seen

async def _check_owner_status(page, ticket_id):
    owner_field = page.locator("#child_id_1_ticketUserInformationAfterRunCrud_owner")
    owner_val = await owner_field.input_value()

    if owner_val.strip().upper() == INS_USERNAME.upper():
        print(f"[INFO] Owner sudah kita ({owner_val}), skip take owner.")
        return "ours", owner_val

    if owner_val.strip():
        print(f"[INFO] Ticket sudah diambil oleh pengguna lain (owner: {owner_val}), skip ticket ini.")
        return "other_owner", owner_val
    try:
        ticket_status = await page.locator(
            "input[name='child_id_1_ticketUserInformationAfterRunCrud_ticket_status']"
        ).input_value()
    except Exception:
        ticket_status = ""

    if ticket_status.strip().upper() == "CLOSED":
        print(f"[INFO] Ticket berstatus CLOSED, tidak ada Take Owner. Skip.")
        return "closed", ticket_status

    print("[INFO] Owner masih kosong, klik Take Owner.")
    btn_take_owner = page.locator("button#takeOwnerShip")

    try:
        await btn_take_owner.wait_for(state="visible", timeout=10000)
    except Exception:
        btn_count = await btn_take_owner.count()
        action_btn_count = await page.locator("#ticketAction").count()

        msg = (
            f"Tombol Take Owner tidak muncul (count={btn_count}, "
            f"#ticketAction count={action_btn_count}, ticket_status='{ticket_status}')."
        )
        print(f"[WARN] {msg}")

        try:
            await page.screenshot(path=f"debug_no_takeowner_{ticket_id}.png", full_page=True)
            print(f"[INFO] Screenshot disimpan: debug_no_takeowner_{ticket_id}.png")
        except Exception as e:
            print(f"[WARN] Gagal ambil screenshot: {e}")

        return "no_button", msg

    await btn_take_owner.click()

    status, title, desc = await modal_handler(page, timeout=10000, required=False)

    if status == "no_modal":
        await page.wait_for_timeout(1000)
        owner_recheck = await owner_field.input_value()
        if owner_recheck.strip().upper() == INS_USERNAME.upper():
            print(f"[INFO] Take owner sukses tanpa modal konfirmasi untuk {ticket_id} (owner: {owner_recheck}).")
            return "taken", owner_recheck
        else:
            msg = f"Take owner gagal: tidak ada modal & owner sekarang '{owner_recheck}' (bukan kita)."
            print(f"[ERR] {msg}")
            return "failed", msg
    elif status in (True, None):
        btn_confirm = page.locator(".swal2-confirm.swal2-styled")
        if await btn_confirm.is_visible():
            await btn_confirm.click()
        await page.locator(".swal2-container").wait_for(state="hidden", timeout=15000)
        await page.wait_for_load_state("load")

        owner_recheck = await owner_field.input_value()
        if owner_recheck.strip().upper() == INS_USERNAME.upper():
            return "taken", owner_recheck
        else:
            msg = f"Take owner selesai tapi owner sekarang '{owner_recheck}' (bukan kita)."
            print(f"[ERR] {msg}")
            return "failed", msg
    else:
        print(f"[ERR] Take owner gagal untuk {ticket_id}: {desc}")
        return "failed", desc


async def select_actual_solution(page, solution_code, timeout=15000):
    # jaring pengaman: kalau ada .vex nyangkut dari step sebelumnya, bersihkan dulu
    await _dismiss_vex_dialog(page, context_label="select_actual_solution (pre-check)")

    frame_loc = page.frame_locator("iframe#jqueryDialogFrame")

    # FIX: bungkus SELURUH alur (buka popup -> isi filter -> submit -> pilih
    # baris) dalam retry, bukan cuma langkah buka popup saja. Field filter
    # kadang tetap "not visible" walau form induknya sudah visible (render
    # belum genap tuntas), jadi kegagalan bisa terjadi di langkah manapun.
    last_err = None
    for attempt in range(1, 3):
        try:
            await page.locator("#btnActualSolution").click()
            await page.locator("iframe#jqueryDialogFrame").wait_for(state="attached", timeout=8000)
            await frame_loc.locator("form[name^='filters_']").wait_for(state="visible", timeout=timeout)

            possible_filter_ids = [
                "input[id$='-fn_classification_code']",
                "input[id$='-fn_parent']",
            ]

            filter_field = None
            for sel in possible_filter_ids:
                loc = frame_loc.locator(sel)
                if await loc.count() > 0:
                    try:
                        await loc.first.wait_for(state="visible", timeout=3000)
                        filter_field = loc.first
                        break
                    except Exception:
                        continue  

            if filter_field is None:
                raise Exception("Tidak ada filter field yang visible di popup Actual Solution (classification_code & parent sama-sama hidden/tidak ditemukan).")

            await filter_field.wait_for(state="visible", timeout=10000)
            await filter_field.fill(solution_code, timeout=10000)

            submit_btn = frame_loc.locator("form[name^='filters_'] input[type='submit']")
            await submit_btn.click()

            row = frame_loc.locator(f"a.custSegment-list:has-text('{solution_code}')")
            await row.wait_for(state="visible", timeout=timeout)
            await row.click()
            await page.wait_for_timeout(1000)
            return  # sukses, keluar dari retry loop

        except Exception as e:
            last_err = e
            print(f"[WARN] select_actual_solution gagal (percobaan {attempt}/2): {e}")

            try:
                await page.evaluate("""
                    () => {
                        if (window.jQuery) {
                            jQuery('.ui-dialog-content').each(function() {
                                try { jQuery(this).dialog('close'); } catch(e) {}
                            });
                        }
                        // jaring pengaman terakhir: hapus paksa elemen dialog & overlay-nya
                        document.querySelectorAll('.ui-dialog, .ui-widget-overlay').forEach(el => el.remove());
                    }
                """)
            except Exception:
                pass

            await _dismiss_vex_dialog(page, context_label="select_actual_solution (retry cleanup)")
            await page.wait_for_timeout(1500)

    raise last_err


async def cancel_work_order(page, ticket_id):
    """
    Loop SEMUA baris di grid Work Order dan cancel yang masih berstatus
    aktif (bukan CANCELED/COMPLETED).
    """
    grid_id = WORK_ORDER_GRID_ID

    label = page.locator("label.tooltip-form-element:has-text('Attribut Workoder')")
    if await label.is_visible():
        await label.click()

    grid_selector = "#" + grid_id + " .grid-action-edit"
    row_edits = page.locator(grid_selector)
    row_count = await row_edits.count()

    if row_count == 0:
        print("[INFO] Tidak ada baris Work Order untuk diproses.")
        return

    print(f"[INFO] Ditemukan {row_count} baris Work Order, cek & cancel yang masih aktif.")

    wo_frame_id = "formGridFrame_" + grid_id
    wo_frame_selector = "iframe#" + wo_frame_id

    for i in range(row_count):
        row_edits = page.locator(grid_selector)
        current_row_count = await row_edits.count()
        if i >= current_row_count:
            break

        await row_edits.nth(i).click()

        status_select = None
        last_err = None
        for attempt in range(1, 3):
            try:
                await page.locator(wo_frame_selector).wait_for(state="attached", timeout=15000)
                wo_frame = page.frame_locator(wo_frame_selector)
                status_select = wo_frame.locator("select[name='status_wo_number']")
                await status_select.wait_for(state="visible", timeout=15000)
                break
            except Exception as e:
                last_err = e
                print(f"[WARN] Select status WO belum muncul (percobaan {attempt}/2): {e}")
                status_select = None
                try:
                    await page.evaluate(f"if (window.JPopup) {{ JPopup.hide('{wo_frame_id}'); }}")
                except Exception:
                    pass
                await page.wait_for_timeout(1500)
                await row_edits.nth(i).click()

        if status_select is None:
            print(f"[ERR] Gagal buka baris WO ke-{i+1} setelah retry, skip baris ini.")
            raise last_err

        current_status = await status_select.input_value()

        if current_status in ("CANCELED", "COMPLETED"):
            print(f"[INFO] WO baris {i+1} sudah berstatus {current_status}, skip.")
            try:
                await page.evaluate(f"JPopup.hide('{wo_frame_id}')")
            except Exception as e:
                print(f"[WARN] Gagal menutup popup WO via JPopup.hide: {e}")
            await page.wait_for_timeout(500)
            continue

        print(f"[INFO] WO baris {i+1} berstatus {current_status}, cancel sekarang.")
        await status_select.select_option("CANCELED")

        save_btn = wo_frame.locator("#btnSaveAct")
        await save_btn.wait_for(state="visible", timeout=15000)
        await save_btn.click()
        await page.wait_for_timeout(2000)


async def set_action_resolved(page):
    blackout = page.locator(".boxy-modal-blackout")
    if await blackout.count() > 0:
        print("[WARN] Overlay .boxy-modal-blackout masih ada, coba hapus paksa sebelum klik #ticketAction.")
        try:
            await page.evaluate(
                "document.querySelectorAll('.boxy-modal-blackout, .boxy-wrapper').forEach(el => el.remove())"
            )
        except Exception:
            pass
        await page.wait_for_timeout(300)

    await _wait_block_overlay_gone(page)

    await page.locator("#ticketAction").click()
    modal = page.locator("#modalActionPopup")
    await modal.wait_for(state="visible", timeout=10000)

    resolved_radio = modal.locator("input[type=radio][value*='finalcheck'], input[type=radio][value*='resolved']").first
    await resolved_radio.click()

    ok_btn = modal.locator("input[type=button][value='Ok']")
    await ok_btn.click()

    try:
        await modal.wait_for(state="hidden", timeout=8000)
    except Exception:
        pass

    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    await page.wait_for_timeout(500)
    vex_msg = await _dismiss_vex_dialog(page, context_label="set_action_resolved")

    if vex_msg is not None and vex_msg.strip():
        return False, vex_msg

    return True, None


async def click_save(page):
    try:
        await _wait_block_overlay_gone(page)
    except Exception as e:
        if "context was destroyed" in str(e).lower():
            print(f"[INFO] Halaman bernavigasi saat cek overlay sebelum Save, tunggu & lanjut.")
            await page.wait_for_timeout(1500)
        else:
            raise

    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass

    save_btn = page.locator("#ticketSave")
    if await save_btn.count() == 0:
        print("[INFO] #ticketSave tidak ditemukan -- kemungkinan tiket sudah tersubmit/reload sebelumnya. Anggap sudah tersimpan.")
        return

    try:
        await save_btn.click(timeout=8000)
    except Exception as e:
        print(f"[WARN] Klik #ticketSave normal gagal ({e}), cek overlay & dialog .vex dulu.")
        await _wait_block_overlay_gone(page)
        await _dismiss_vex_dialog(page, context_label="click_save (before)")
        await page.wait_for_timeout(500)

        save_btn = page.locator("#ticketSave")
        if await save_btn.count() == 0:
            print("[INFO] #ticketSave hilang setelah overlay dibersihkan -- anggap tiket sudah tersimpan.")
            return

        try:
            await save_btn.click(timeout=15000, force=True)
        except Exception as e2:
            print(f"[WARN] Klik #ticketSave paksa tetap gagal ({e2}) -- kemungkinan tiket sudah tersubmit lewat Action Status. Lanjut tanpa error fatal.")
            return

    await page.wait_for_timeout(1000)
    post_click_vex = await _dismiss_vex_dialog(page, context_label="click_save (after)")
    if post_click_vex is not None and post_click_vex.strip():
        print(f"[WARN] Save mungkin gagal karena validasi: \"{post_click_vex}\" -- lanjut tanpa menunggu navigasi.")
        return

    try:
        await page.wait_for_load_state("load", timeout=15000)
    except Exception:
        print("[WARN] Tidak ada navigasi terdeteksi setelah Save (mungkin submit gagal diam-diam atau AJAX tanpa reload).")


# ==== BOT-1: cek owner -> ibooster -> (swap WO/ActSol tergantung kategori) -> save ====

async def _read_actual_solution(page):
    field = page.locator("#actual_solution")
    try:
        return (await field.input_value()).strip()
    except Exception:
        return ""


async def process_ticket_bot1(page, ticket_id, worksheet_name, sheet_lock=None):
    """
    Bot-1: hanya proses ticket yang belum punya Owner ATAU belum punya
    Actual Solution. Kalau keduanya sudah terisi, ticket dianggap sudah
    pernah diproses -> skip.

    sheet_lock (opsional): asyncio.Lock() dipakai saat dijalankan paralel
    (beberapa page/worker sekaligus) supaya penulisan ke Google Sheets
    (update_ticket_fields) tidak bentrok antar worker. Kalau None
    (pemanggilan sekuensial biasa), langsung tulis tanpa lock.

    Urutan:
    1. Pastikan form ticket ter-render (page sudah di halaman detail yang
       benar dari resolve_inc_to_record_id -- TIDAK goto ulang)
    2. Cek/ambil owner
    3. Cek apakah tombol Ibooster memang bisa diinteraksi (tiket yang
       statusnya "selesai tapi belum di-close" biasanya tombol ini
       disabled/tidak ada -- bukan bug bot, memang kondisi tiketnya)
    4. Update Ibooster
    5. Simpan STATUS ONT & ONU RX ke sheet
    6a. SPEC & ONLINE -> Cancel WO dulu, baru Actual Solution, lalu Resolved, lalu Save
    6b. Selain itu -> Actual Solution sesuai channel, lalu Save
    """
    result = {
        "ticket_id": ticket_id, "inc_number": None,
        "status_ont": None, "onu_rx": None, "final": "PENDING", "note": "",
    }

    id_ticket_field = page.locator("#child_id_1_ticketUserInformationAfterRunCrud_id_ticket")
    try:
        await id_ticket_field.wait_for(state="attached", timeout=8000)
    except Exception:
        print(f"[WARN] Ticket {ticket_id} tidak bisa diakses (form tidak render). Skip.")
        result["final"] = "NOT_ACCESSIBLE"
        result["note"] = "Form ticket tidak render setelah navigasi"
        return result

    inc_number = await id_ticket_field.input_value()
    result["inc_number"] = inc_number

    owner_field = page.locator("#child_id_1_ticketUserInformationAfterRunCrud_owner")
    owner_val_early = (await owner_field.input_value()).strip()
    actsol_val_early = await _read_actual_solution(page)

    if owner_val_early and actsol_val_early:
        result["final"] = "SKIPPED_ALREADY_PROCESSED"
        print(f"[INFO] {inc_number} -> sudah punya Owner & Actual Solution, skip (Bot-1).")
        return result

    owner_action, owner_detail = await _check_owner_status(page, ticket_id)

    if owner_action == "closed":
        result["final"] = "SKIPPED_CLOSED"
        result["note"] = f"ticket_status: {owner_detail}"
        return result
    if owner_action == "other_owner":
        result["final"] = "SKIPPED_OTHER_OWNER"
        result["note"] = f"owner: {owner_detail}"
        return result
    if owner_action == "no_button":
        result["final"] = "SKIPPED_NO_TAKEOWNER_BUTTON"
        result["note"] = owner_detail
        return result
    if owner_action == "failed":
        result["final"] = "TAKEOWNER_FAILED"
        result["note"] = owner_detail
        return result

    # ---- CEK APAKAH TOMBOL IBOOSTER BISA DIINTERAKSI ----
    # FIX: dengan banyak worker paralel, elemen bisa belum sempat
    # ter-render saat count() pertama kali dipanggil (beban server/render
    # naik). Retry pengecekan dengan jeda kecil sebelum benar-benar
    # vonis "unavailable" -- supaya tidak salah deteksi tiket yang
    # sebenarnya normal cuma render-nya telat.
    booster_btn = page.locator("#btnPengukuranBooster")
    booster_count = await booster_btn.count()

    if booster_count == 0:
        for retry_attempt in range(3):
            await page.wait_for_timeout(1500)
            booster_count = await booster_btn.count()
            if booster_count > 0:
                print(f"[INFO] Tombol booster muncul setelah tunggu ({retry_attempt + 1}x retry), lanjut normal.")
                break

    if booster_count == 0:
        print(f"[WARN] Tombol #btnPengukuranBooster tidak ada sama sekali untuk {inc_number}, kemungkinan tiket sudah pada fase akhir (selesai belum close).")
        result["final"] = "SKIPPED_BOOSTER_UNAVAILABLE"
        result["note"] = "Tombol Ibooster tidak ditemukan di DOM"
        return result

    is_disabled = await booster_btn.first.is_disabled()
    if is_disabled:
        print(f"[WARN] Tombol #btnPengukuranBooster disabled untuk {inc_number}, kemungkinan tiket sudah pada fase akhir (selesai belum close).")
        result["final"] = "SKIPPED_BOOSTER_UNAVAILABLE"
        result["note"] = "Tombol Ibooster disabled"
        return result

# ---- TRIGGER IBOOSTER ----
    try:
        clicked = await page.evaluate(
            "() => { const btn = document.querySelector('#btnPengukuranBooster'); if (btn) { btn.click(); return true; } return false; }"
        )
        if not clicked:
            raise Exception("Elemen #btnPengukuranBooster tidak ditemukan di DOM.")
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"[WARN] Trigger klik #btnPengukuranBooster via DOM gagal ({e}), fallback klik langsung.")
        await _click_with_retry(page, "#btnPengukuranBooster", retries=3, click_timeout=10000, wait_between=2000, label="btnPengukuranBooster")

    kategori_ukur, ibooster_vex_error = await _wait_measurement_category_or_vex(page)

    # FIX: kalau hasil pertama kosong total (bukan soal .vex error, murni
    # timeout), kemungkinan besar beban server naik saat mode paralel --
    # coba retrigger booster SEKALI lagi dari awal sebelum menyerah.
    if not kategori_ukur.strip():
        print(f"[WARN] {inc_number}: Kategori Ukur kosong setelah percobaan pertama, retry trigger booster sekali lagi.")
        try:
            clicked = await page.evaluate(
                "() => { const btn = document.querySelector('#btnPengukuranBooster'); if (btn) { btn.click(); return true; } return false; }"
            )
            if not clicked:
                raise Exception("Elemen #btnPengukuranBooster tidak ditemukan di DOM (retry).")
            await page.wait_for_timeout(500)
        except Exception as e:
            print(f"[WARN] Retry trigger booster gagal ({e}).")

        kategori_ukur_retry, ibooster_vex_error_retry = await _wait_measurement_category_or_vex(page)
        if kategori_ukur_retry.strip():
            print(f"[INFO] {inc_number}: Retry berhasil, Kategori Ukur terisi: {kategori_ukur_retry}")
            kategori_ukur = kategori_ukur_retry
            ibooster_vex_error = ibooster_vex_error_retry
        else:
            print(f"[WARN] {inc_number}: Retry tetap gagal, lanjut dengan nilai kosong.")

    if ibooster_vex_error is not None:
        if _is_benign_vex_message(ibooster_vex_error):
            print(f"[INFO] Ibooster untuk {inc_number} sempat lempar dialog dikenal (diabaikan).")
        else:
            print(f"[WARN] Ibooster gagal untuk {inc_number}: \"{ibooster_vex_error}\".")

    status_ont_raw = await page.locator("#child_id_1_ticketUserInformationAfterRunCrud_status_ont").input_value()
    onu_rx_raw = await page.locator("#child_id_1_ticketUserInformationAfterRunCrud_onu_rx").input_value()
    status_ont_val = status_ont_raw.split("|")[-1].strip() if status_ont_raw else ""
    onu_rx_val = onu_rx_raw.split("|")[-1].strip() if onu_rx_raw else ""

    result["status_ont"] = status_ont_val
    result["onu_rx"] = onu_rx_val
    print(f"[INFO] {inc_number} -> Kategori Ukur = {kategori_ukur} | Status ONT = {status_ont_val} | ONU rx = {onu_rx_val}")

    ibooster_section_missing = (
        not kategori_ukur.strip() and not status_ont_val.strip() and not onu_rx_val.strip()
    )
    if ibooster_section_missing:
        print(f"[WARN] {inc_number}: IBooster Section tidak ada pada ticket tersebut.")
        result["note"] = "IBooster Section tidak ada pada ticket tersebut"

    async def _update_sheet():
        try:
            await update_ticket_fields(worksheet_name, inc_number, {"STATUS ONT": status_ont_val, "ONU RX": onu_rx_val})
        except Exception as e:
            print(f"[ERR] Gagal update {inc_number} di {worksheet_name}: {e}")

    if sheet_lock is not None:
        async with sheet_lock:
            await _update_sheet()
    else:
        await _update_sheet()

    channel = await page.locator("#child_id_1_ticketUserInformationAfterRunCrud_channel").input_value()
    solution_code = SOLUTION_MAP.get(channel)

    is_qualified = (kategori_ukur.strip().upper() == "SPEC" and status_ont_val.strip().upper() == "ONLINE")

    if is_qualified:
        await cancel_work_order(page, ticket_id)

        if solution_code:
            await select_actual_solution(page, solution_code)
        else:
            print(f"[WARN] Channel {channel} tidak dikenali untuk {ticket_id}, skip actual solution.")

        if channel == "28":
            resolved_ok, resolve_error = await set_action_resolved(page)

            if not resolved_ok:
                print(f"[WARN] Resolve gagal untuk {inc_number} (validasi: \"{resolve_error}\"), fallback ke Save biasa.")
                await click_save(page)
                result["final"] = "RESOLVE_VALIDATION_BLOCKED"
                result["note"] = resolve_error
                return result

            await click_save(page)
            result["final"] = "RESOLVED"
            return result

        await click_save(page)
        result["final"] = "ACTUAL_SOLUTION_SAVED"
        return result

    else:
        if solution_code:
            await select_actual_solution(page, solution_code)
        else:
            print(f"[WARN] Channel {channel} tidak dikenali untuk {ticket_id}, skip actual solution.")

        await click_save(page)
        result["final"] = "SAVED_NOT_QUALIFIED"
        return result


async def process_ticket_batch_bot1(page, inc_numbers, worksheet_name):
    """
    Versi sekuensial biasa -- satu page, satu tiket pada satu waktu.
    """
    all_results = []
    for inc_number in inc_numbers:
        print(f"\n=== [Bot-1] Memproses {inc_number} ===")
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except TicketNotFoundError as e:
            print(f"[INFO] {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "TICKET_NOT_FOUND"})
            continue
        except Exception as e:
            print(f"[ERR] Resolve gagal untuk {inc_number}: {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await process_ticket_bot1(page, record_id, worksheet_name)
            print(f"[RESULT] {inc_number} -> {result['final']}")
            all_results.append(result)
        except Exception as e:
            print(f"[ERR] Flow Bot-1 gagal untuk {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue

    return all_results


# ==== BOT-1 PARALLEL: jalankan beberapa worker (page) sekaligus ====

def _split_into_chunks(items, n_chunks):
    """Bagi list jadi n_chunks bagian sedatar mungkin."""
    if n_chunks <= 0:
        return [items]
    k, m = divmod(len(items), n_chunks)
    chunks = []
    start = 0
    for i in range(n_chunks):
        size = k + (1 if i < m else 0)
        chunks.append(items[start:start + size])
        start += size
    return [c for c in chunks if c]  # buang chunk kosong


async def process_ticket_batch_bot1_worker(worker_id, page, inc_numbers, worksheet_name, sheet_lock):
    """
    Sama seperti process_ticket_batch_bot1, tapi:
    - Label log ditandai [Worker-N] supaya gampang dibedakan di terminal.
    - update_ticket_fields dibungkus sheet_lock supaya tidak bentrok
      dengan worker lain yang menulis ke worksheet yang sama bersamaan.
    """
    all_results = []
    for inc_number in inc_numbers:
        print(f"\n=== [Bot-1][Worker-{worker_id}] Memproses {inc_number} ===")
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except TicketNotFoundError as e:
            print(f"[INFO][Worker-{worker_id}] {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "TICKET_NOT_FOUND"})
            continue
        except Exception as e:
            print(f"[ERR][Worker-{worker_id}] Resolve gagal untuk {inc_number}: {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await process_ticket_bot1(page, record_id, worksheet_name, sheet_lock=sheet_lock)
            print(f"[RESULT][Worker-{worker_id}] {inc_number} -> {result['final']}")
            all_results.append(result)
        except Exception as e:
            print(f"[ERR][Worker-{worker_id}] Flow Bot-1 gagal untuk {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue

    return all_results


async def process_ticket_batch_bot1_parallel(pages, inc_numbers, worksheet_name):
    """
    Jalankan Bot-1 dengan beberapa page (worker) sekaligus. `pages` harus
    berasal dari CONTEXT yang sama (share cookie/sesi login), bukan
    context terpisah, supaya tidak perlu login ulang per page.

    inc_numbers dibagi rata ke tiap page, lalu semua worker jalan
    bersamaan lewat asyncio.gather.
    """
    n_workers = len(pages)
    chunks = _split_into_chunks(inc_numbers, n_workers)

    print(f"[Bot-1][Parallel] {len(inc_numbers)} tiket dibagi ke {len(chunks)} worker: "
          f"{[len(c) for c in chunks]}")

    sheet_lock = asyncio.Lock()

    tasks = [
        process_ticket_batch_bot1_worker(i + 1, pages[i], chunks[i], worksheet_name, sheet_lock)
        for i in range(len(chunks))
    ]

    results_per_worker = await asyncio.gather(*tasks)

    all_results = []
    for r in results_per_worker:
        all_results.extend(r)

    print(f"\n[Bot-1][Parallel] Selesai {len(all_results)} tiket.")
    return all_results


# ==== BOT-2: cuma cek kategori ukur/status ont/onu rx untuk SEMUA tiket, loop 30 menit ====

async def check_measurement_only(page, ticket_id, worksheet_name, sheet_lock=None):
    """
    Bot-2: buka ticket, trigger update Ibooster, baca hasilnya, simpan ke
    sheet -- TIDAK take owner, TIDAK ubah WO, TIDAK ubah Actual Solution,
    TIDAK save/resolve apapun. Murni cek & catat.

    sheet_lock (opsional): dipakai saat dijalankan paralel supaya
    update_ticket_fields tidak bentrok antar worker.
    """
    result = {"ticket_id": ticket_id, "inc_number": None, "status_ont": None, "onu_rx": None, "final": "PENDING"}

    id_ticket_field = page.locator("#child_id_1_ticketUserInformationAfterRunCrud_id_ticket")
    try:
        await id_ticket_field.wait_for(state="attached", timeout=8000)
    except Exception:
        print(f"[WARN] Ticket {ticket_id} tidak bisa diakses (form tidak render). Skip.")
        result["final"] = "NOT_ACCESSIBLE"
        return result

    inc_number = await id_ticket_field.input_value()
    result["inc_number"] = inc_number

    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass
    await page.wait_for_timeout(1000)

    try:
        clicked = await page.evaluate(
            "() => { const btn = document.querySelector('#btnPengukuranBooster'); if (btn) { btn.click(); return true; } return false; }"
        )
        if not clicked:
            raise Exception("Elemen #btnPengukuranBooster tidak ditemukan.")
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"[WARN] Trigger Ibooster gagal ({e}), fallback klik langsung.")
        await _click_with_retry(page, "#btnPengukuranBooster", retries=3, click_timeout=10000, wait_between=2000, label="btnPengukuranBooster")

    kategori_ukur, ibooster_vex_error = await _wait_measurement_category_or_vex(page)

    if not kategori_ukur.strip():
        print(f"[WARN] Kategori Ukur kosong setelah percobaan pertama, retry trigger booster sekali lagi.")
        try:
            clicked = await page.evaluate(
                "() => { const btn = document.querySelector('#btnPengukuranBooster'); if (btn) { btn.click(); return true; } return false; }"
            )
            if not clicked:
                raise Exception("Elemen #btnPengukuranBooster tidak ditemukan (retry).")
            await page.wait_for_timeout(500)
        except Exception as e:
            print(f"[WARN] Retry trigger booster gagal ({e}).")

        kategori_ukur_retry, ibooster_vex_error_retry = await _wait_measurement_category_or_vex(page)
        if kategori_ukur_retry.strip():
            print(f"[INFO] Retry berhasil, Kategori Ukur terisi: {kategori_ukur_retry}")
            kategori_ukur = kategori_ukur_retry
            ibooster_vex_error = ibooster_vex_error_retry
        else:
            print(f"[WARN] Retry tetap gagal, lanjut dengan nilai kosong.")

    if ibooster_vex_error is not None:
        if _is_benign_vex_message(ibooster_vex_error):
            print(f"[INFO] Ibooster untuk {inc_number} sempat lempar dialog dikenal (diabaikan).")
        else:
            print(f"[WARN] Ibooster gagal untuk {inc_number}: \"{ibooster_vex_error}\".")

    status_ont_raw = await page.locator("#child_id_1_ticketUserInformationAfterRunCrud_status_ont").input_value()
    onu_rx_raw = await page.locator("#child_id_1_ticketUserInformationAfterRunCrud_onu_rx").input_value()
    status_ont_val = status_ont_raw.split("|")[-1].strip() if status_ont_raw else ""
    onu_rx_val = onu_rx_raw.split("|")[-1].strip() if onu_rx_raw else ""

    result["status_ont"] = status_ont_val
    result["onu_rx"] = onu_rx_val
    print(f"[INFO] [Bot-2] {inc_number} -> Kategori Ukur = {kategori_ukur} | Status ONT = {status_ont_val} | ONU rx = {onu_rx_val}")

    async def _update_sheet():
        try:
            await update_ticket_fields(worksheet_name, inc_number, {"STATUS ONT": status_ont_val, "ONU RX": onu_rx_val})
        except Exception as e:
            print(f"[ERR] Gagal update {inc_number} di {worksheet_name}: {e}")

    if sheet_lock is not None:
        async with sheet_lock:
            await _update_sheet()
    else:
        await _update_sheet()

    result["final"] = "CHECKED"
    return result


async def run_bot2_cycle(page, worksheet_name):
    """
    Satu putaran penuh: cek SEMUA tiket di worksheet_name, dari ticket
    pertama sampai terakhir, murni cek kategori ukur (tanpa aksi lain).
    """
    inc_numbers = await get_all_incs(worksheet_name)
    print(f"\n[Bot-2] Mulai cek {len(inc_numbers)} tiket di {worksheet_name}.")

    results = []
    for inc_number in inc_numbers:
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except Exception as e:
            print(f"[ERR] [Bot-2] Resolve gagal untuk {inc_number}: {e}")
            results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await check_measurement_only(page, record_id, worksheet_name)
            results.append(result)
        except Exception as e:
            print(f"[ERR] [Bot-2] Gagal cek {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue

    print(f"[Bot-2] Selesai satu putaran ({len(results)} tiket dicek).")
    return results


# ==== BOT-2 PARALLEL ====

async def check_measurement_worker(worker_id, page, inc_numbers, worksheet_name, sheet_lock):
    all_results = []
    for inc_number in inc_numbers:
        print(f"\n=== [Bot-2][Worker-{worker_id}] Memproses {inc_number} ===")
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except Exception as e:
            print(f"[ERR][Worker-{worker_id}] Resolve gagal untuk {inc_number}: {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await check_measurement_only(page, record_id, worksheet_name, sheet_lock=sheet_lock)
            all_results.append(result)
        except Exception as e:
            print(f"[ERR][Worker-{worker_id}] Gagal cek {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue
    return all_results


async def run_bot2_cycle_parallel(pages, worksheet_name):
    """Satu putaran Bot-2, dibagi ke beberapa page/worker sekaligus."""
    inc_numbers = await get_all_incs(worksheet_name)
    print(f"\n[Bot-2][Parallel] Mulai cek {len(inc_numbers)} tiket di {worksheet_name}, {len(pages)} worker.")

    sheet_lock = asyncio.Lock()
    chunks = _split_into_chunks(inc_numbers, len(pages))
    tasks = [
        check_measurement_worker(i + 1, pages[i], chunks[i], worksheet_name, sheet_lock)
        for i in range(len(chunks))
    ]
    results_per_worker = await asyncio.gather(*tasks)

    all_results = []
    for r in results_per_worker:
        all_results.extend(r)

    print(f"[Bot-2][Parallel] Selesai satu putaran ({len(all_results)} tiket dicek).")
    return all_results


async def run_bot2_forever(page, worksheet_name, sleep_seconds=1800):
    """
    Bot-2 jalan terus: cek semua tiket, selesai -> sleep 30 menit -> ulangi.
    """
    while True:
        await run_bot2_cycle(page, worksheet_name)
        print(f"[Bot-2] Sleep {sleep_seconds // 60} menit sebelum putaran berikutnya...\n")
        await asyncio.sleep(sleep_seconds)


# ==== BOT-3: auto Take Owner saja untuk SEMUA tiket, lintas Database/Database2/Database3 ====

async def process_ticket_bot3(page, ticket_id, worksheet_name):
    """
    Bot-3: HANYA ambil ownership kalau owner masih kosong. Tidak ada
    Ibooster, tidak ada Actual Solution, tidak ada Save/Resolve -- murni
    take owner lalu selesai.

    PENTING: kolom "OWNER" di sheet diupdate LANGSUNG per-ticket lewat
    update_ticket_fields (sama seperti Status ONT/ONU rx di Bot-1) --
    supaya data di sheet real-time mengikuti aksi take-owner di website,
    tidak perlu menunggu scrape penuh berikutnya untuk 800+ tiket.
    """
    result = {"ticket_id": ticket_id, "inc_number": None, "final": "PENDING", "note": ""}

    id_ticket_field = page.locator("#child_id_1_ticketUserInformationAfterRunCrud_id_ticket")
    try:
        await id_ticket_field.wait_for(state="attached", timeout=8000)
    except Exception:
        print(f"[WARN] Ticket {ticket_id} tidak bisa diakses (form tidak render). Skip.")
        result["final"] = "NOT_ACCESSIBLE"
        return result

    inc_number = await id_ticket_field.input_value()
    result["inc_number"] = inc_number

    owner_action, owner_detail = await _check_owner_status(page, ticket_id)

    if owner_action == "ours":
        result["final"] = "SKIPPED_ALREADY_OURS"
        # owner sudah kita -- tetap sinkronkan ke sheet, jaga-jaga kalau
        # sheet belum pernah tercatat owner-nya sama sekali.
        try:
            await update_ticket_fields(worksheet_name, inc_number, {"OWNER": owner_detail})
        except Exception as e:
            print(f"[ERR] Gagal update OWNER {inc_number} di {worksheet_name}: {e}")
        return result

    if owner_action == "closed":
        result["final"] = "SKIPPED_CLOSED"
        result["note"] = f"ticket_status: {owner_detail}"
        return result
    if owner_action == "other_owner":
        result["final"] = "SKIPPED_OTHER_OWNER"
        result["note"] = f"owner: {owner_detail}"
        try:
            await update_ticket_fields(worksheet_name, inc_number, {"OWNER": owner_detail})
        except Exception as e:
            print(f"[ERR] Gagal update OWNER {inc_number} di {worksheet_name}: {e}")
        return result
    if owner_action == "no_button":
        result["final"] = "SKIPPED_NO_TAKEOWNER_BUTTON"
        result["note"] = owner_detail
        return result
    if owner_action == "failed":
        result["final"] = "TAKEOWNER_FAILED"
        result["note"] = owner_detail
        return result

    # owner_action == "taken" -- baru saja berhasil take owner
    result["final"] = "TAKEN"
    result["note"] = f"owner: {owner_detail}"

    try:
        await update_ticket_fields(worksheet_name, inc_number, {"OWNER": owner_detail})
        print(f"[INFO] Sheet {worksheet_name} langsung terupdate: {inc_number} -> OWNER = {owner_detail}")
    except Exception as e:
        print(f"[ERR] Gagal update OWNER {inc_number} di {worksheet_name}: {e}")

    return result


async def run_bot3_worksheet(page, worksheet_name):
    """
    Jalankan Bot-3 untuk SATU worksheet -- dipanggil berulang oleh
    run_bot3_all_worksheets untuk Database, Database2, Database3.
    """
    inc_numbers = await get_all_incs(worksheet_name)
    print(f"\n[Bot-3] Mulai take owner untuk {len(inc_numbers)} tiket di {worksheet_name}.")

    results = []
    for inc_number in inc_numbers:
        print(f"\n=== [Bot-3] Memproses {inc_number} ({worksheet_name}) ===")
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except TicketNotFoundError as e:
            print(f"[INFO] {e}")
            results.append({"ticket_id": None, "inc_number": inc_number, "final": "TICKET_NOT_FOUND"})
            continue
        except Exception as e:
            print(f"[ERR] Resolve gagal untuk {inc_number}: {e}")
            results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await process_ticket_bot3(page, record_id, worksheet_name)
            print(f"[RESULT] {inc_number} -> {result['final']}")
            results.append(result)
        except Exception as e:
            print(f"[ERR] Flow Bot-3 gagal untuk {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue

    print(f"[Bot-3] Selesai {worksheet_name} ({len(results)} tiket diproses).")
    return results


async def run_bot3_all_worksheets(page, worksheet_names=("Database", "Database2", "Database3")):
    """
    Bot-3 lintas beberapa worksheet sekaligus -- beda dari Bot-1/Bot-2 yang
    cuma jalan di Database3.
    """
    all_results = {}
    for ws in worksheet_names:
        all_results[ws] = await run_bot3_worksheet(page, ws)
    return all_results


# ==== BOT-3 PARALLEL ====

async def process_ticket_bot3_worker(worker_id, page, inc_numbers, worksheet_name):
    all_results = []
    for inc_number in inc_numbers:
        print(f"\n=== [Bot-3][Worker-{worker_id}] Memproses {inc_number} ({worksheet_name}) ===")
        try:
            record_id = await resolve_inc_to_record_id(page, inc_number)
        except TicketNotFoundError as e:
            print(f"[INFO][Worker-{worker_id}] {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "TICKET_NOT_FOUND"})
            continue
        except Exception as e:
            print(f"[ERR][Worker-{worker_id}] Resolve gagal untuk {inc_number}: {e}")
            all_results.append({"ticket_id": None, "inc_number": inc_number, "final": "RESOLVE_FAILED"})
            await recover_to_find_incident_page(page)
            continue

        try:
            result = await process_ticket_bot3(page, record_id, worksheet_name)
            print(f"[RESULT][Worker-{worker_id}] {inc_number} -> {result['final']}")
            all_results.append(result)
        except Exception as e:
            print(f"[ERR][Worker-{worker_id}] Flow Bot-3 gagal untuk {inc_number}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({"ticket_id": record_id, "inc_number": inc_number, "final": "FLOW_ERROR"})
            await recover_to_find_incident_page(page)
            continue
    return all_results


async def run_bot3_worksheet_parallel(pages, worksheet_name):
    """Take owner SATU worksheet, dibagi ke beberapa page/worker sekaligus."""
    inc_numbers = await get_all_incs(worksheet_name)
    print(f"\n[Bot-3][Parallel] {len(inc_numbers)} tiket di {worksheet_name}, {len(pages)} worker.")

    chunks = _split_into_chunks(inc_numbers, len(pages))
    tasks = [
        process_ticket_bot3_worker(i + 1, pages[i], chunks[i], worksheet_name)
        for i in range(len(chunks))
    ]
    results_per_worker = await asyncio.gather(*tasks)

    all_results = []
    for r in results_per_worker:
        all_results.extend(r)

    print(f"[Bot-3][Parallel] Selesai {worksheet_name} ({len(all_results)} tiket diproses).")
    return all_results


async def run_bot3_all_worksheets_parallel(pages, worksheet_names=("Database", "Database2", "Database3")):
    """Bot-3 paralel, lintas worksheet (tiap worksheet diproses berurutan,
    tapi DI DALAM tiap worksheet tiketnya dibagi ke beberapa worker)."""
    all_results = {}
    for ws in worksheet_names:
        all_results[ws] = await run_bot3_worksheet_parallel(pages, ws)
    return all_results