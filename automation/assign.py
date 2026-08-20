# automation/assign.py

from playwright.async_api import async_playwright, expect
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import traceback, asyncio

from utils.session import load_session
from job_queue_pkg.job_queue import update_job_status
from .auth import login, ensure_logged_in
from .modal import modal_handler, modal_confirm
from config import WFM_URL
from settings import settings

async def find_inc(inc_list, labor_number, chat_id, msg_id, page):

    login_ok = await ensure_logged_in(page)

    if not login_ok:
        print(f"[ERR] Not Login. >> {page.url}")
        return False
    
    search_inc = page.locator("#searchInc")
    await search_inc.wait_for(state="visible", timeout=30000)

    for inc_number in inc_list:
        print(f"[ASSIGN] Process: {inc_number} - {labor_number} ...")

        try:
            prev_url = page.url
            
            await search_inc.fill(inc_number)
            await page.keyboard.press("Enter")

            status, title, desc = await modal_handler(page)

            await page.locator(".swal2-container").wait_for(state="hidden", timeout=8000)
            
            if status is False:
                update_job_status(inc_number, chat_id, msg_id, 
                                  inc_status="NOT_FOUND", wo_status="NOT_FOUND", 
                                  status="NOT_FOUND")
                print(f"   → {inc_number} Not Found.")
                continue
            
            if status is True:
                try:
                    await page.wait_for_function(
                        """(prev) => location.href !== prev || document.querySelector('input[name="external_id"]')""",
                        arg=prev_url,
                        timeout=15000
                    )
                    await page.wait_for_load_state("load")
                except:
                    print(f"[WARN] There is no URL change for {inc_number}")
                    
                await page.wait_for_load_state("load")
                
                inc_status, wo_status, job_status, labor_status = await get_assign(page, inc_number, labor_number)

                update_job_status(inc_number, chat_id, msg_id, 
                                  inc_status=inc_status, 
                                  wo_status=wo_status, 
                                  status=job_status, 
                                  labor_status=labor_status)
                
        except Exception as e:
            traceback.print_exc()
            print(f"[ERR] INC={inc_number}: {e}")


async def get_assign(page, inc_number, labor_number, max_retries=3):

    loc_ticket = page.locator('input[name="external_id"]')
    loc_owner = page.locator('input[name="owner"]')
    loc_owner_group = page.locator('input[name="owner_group"]')
    loc_status = page.locator('.status-item:has(.status-oval.active) .status-text')
    btn_takeowner = page.locator('#btn_takeOwner')
    
    val_ticket_id = await loc_ticket.input_value()
    val_owner_group = await loc_owner_group.input_value()
    if val_ticket_id != inc_number or not val_owner_group.strip():
        return "NOT_FOUND", "NOT_FOUND", "NOT_FOUND", "FOUND"

    val_owner = (await loc_owner.input_value()) or ""
    inc_status = await loc_status.inner_text()
    
    wo_status = "NOT_FOUND"
    for i in range(max_retries):
        wo_status = await wo_check(page)
        if wo_status not in ("NOT_FOUND", "IS_EMPTY"):
            break
        print(f"   → Retry WO table {i+1}/{max_retries} - status: {wo_status}.")
        await asyncio.sleep(2)

    labor_status = "FOUND"

    print(f"   → {inc_number} progress: {inc_status}")

    if inc_status in ("NEW", "DRAFT", "ANALYSIS", "PENDING"):
        return inc_status, wo_status, "PENDING", labor_status
    
    if inc_status == "BACKEND":

        if (not val_owner) or (val_owner != settings.WFM_USERNAME):
            await expect(btn_takeowner).to_be_visible(timeout=10000)
            await modal_confirm(page, btn_takeowner)

            url_target = WFM_URL["edit"]+inc_number+"#"
            await page.wait_for_url(url_target)
            await page.wait_for_load_state("domcontentloaded")

        btn_addwo = page.locator('#button_create_wo')
        if wo_status in ("NOT_FOUND", "IS_EMPTY"):
            await expect(btn_addwo).to_be_visible(timeout=15000)
            await modal_confirm(page, btn_addwo)
            return inc_status, "CREATED", "PENDING", labor_status
        elif wo_status == "CANCELED":
            return inc_status, wo_status, "PENDING", labor_status
        
        assign_table = page.locator("#dummy-data-tableAssignment tbody tr")
        row_count = 0
        for i in range(max_retries):
            row_count = await assign_table.count()
            if row_count > 0:
                break
            print(f"   → Retry assignment table {i+1}/{max_retries}.")
            await asyncio.sleep(2)

        if row_count == 0:
            print("   → Assignment section table not found.")
            return inc_status, wo_status, "PENDING", labor_status
        
        first_row = assign_table.nth(0)
        btn_edit_assign = first_row.locator('button.showModal')
        btn_attr_inc = await btn_edit_assign.get_attribute('data-ticket')

        if btn_attr_inc != inc_number:
            return inc_status, wo_status, "PENDING", labor_status
        
        await btn_edit_assign.click()
        
        modal = page.locator("#dataModalAssignment.show")
        await modal.wait_for(state="visible", timeout=8000)
        
        if await modal.is_visible():
            print("   → Assignment detail showing.")
        else:
            status, title, desc = await modal_handler(page)

        labor_input = modal.locator("#technician_code")
        await labor_input.wait_for(state="visible")

        await labor_input.fill("")
        await labor_input.fill(labor_number)

        modal_labor = page.locator(".swal2-popup")    
        if await modal_labor.is_visible():

            status, title, desc = await modal_handler(page)

            if status is False:
                print(f"   → labor: {labor_number} not found.")

            btn_confirm = page.locator(".swal2-confirm.swal2-styled")
            if await btn_confirm.is_visible():
                await btn_confirm.click()
            
            await page.locator(".swal2-container").wait_for(state="hidden", timeout=15000)

            btn_close = modal.locator(".btn-close")
            if await btn_close.is_visible():
                await btn_close.click()
            
            await modal.wait_for(state="hidden", timeout=15000)

            return inc_status, wo_status, "PENDING", "NOT_FOUND"

        btn_save = modal.locator("#saveButton")
        await btn_save.click()

        status, title, desc = await modal_handler(page)
        
        if status is True:
            print(f"   → {inc_number} DONE Assign.")

        await modal.wait_for(state="hidden", timeout=15000)
        await page.wait_for_load_state("load")
        
        return inc_status, wo_status, "DONE", labor_status

    return inc_status, wo_status, "CLOSED", labor_status
        
async def wo_check(page, timeout=20000):
    
    await page.wait_for_load_state("networkidle")
    await page.locator("#dummy-data-tablewonum tbody").wait_for(state="visible", timeout=timeout)
    
    wo_table = page.locator("#dummy-data-tablewonum tbody tr")
    row_count = await wo_table.count()

    if row_count == 0:
        print("   → WO status not found.")
        return "NOT_FOUND"
    
    first_row = wo_table.nth(0)
    status_cell = first_row.locator("td").nth(1)

    await status_cell.wait_for(state="visible", timeout=5000)
    
    wo_status = (await status_cell.inner_text()).strip().upper()

    if not wo_status:
        print("   → WO status empty.")
        return "IS_EMPTY"
    
    return wo_status


        

                



