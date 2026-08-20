# automation/modal.py

from playwright.async_api import expect
from utils.slug import slugify

async def modal_handler(page, timeout=15000, required=True):

    modal = page.locator(".swal2-popup")

    if required:
        await modal.wait_for(state="visible", timeout=timeout)
    else:
        # FIX: sebagian aksi (mis. Take Owner) kadang sukses langsung tanpa
        # modal konfirmasi muncul sama sekali. Kalau required=False, jangan
        # lempar exception -- kembalikan status "no_modal" supaya caller
        # bisa cek kondisi lain (mis. field yang seharusnya terisi).
        try:
            await modal.wait_for(state="visible", timeout=timeout)
        except Exception:
            return "no_modal", "", ""

    modal_class = await modal.get_attribute("class") or ""
    modal_title = ""
    modal_desc = ""

    if await modal.locator("#swal2-title").is_visible():
        modal_title = await modal.locator("#swal2-title").inner_text()
    
    if await modal.locator("#swal2-html-container").is_visible():
        modal_desc = await modal.locator("#swal2-html-container").inner_text()
    
    if "swal2-loading" in modal_class or "Loading" in modal_title:
        status = "loading"
    elif "swal2-icon-success" in modal_class:
        status = True
    elif any(c in modal_class for c in ("swal2-icon-error", "swal2-icon-warning")):
        status = False
    else:
        status = None
    
    if status == "loading":
        print("   → ALERT - Loading...")
    else:
        print(f"   → ALERT - {modal_title.strip()} - {modal_desc.strip()}")
    
    return status, modal_title.strip(), modal_desc.strip()

async def modal_confirm(page, button, timeout=15000):

    await button.click()

    status, title, desc = await modal_handler(page, timeout)

    if status == "loading":
        for _ in range(30):
            await page.wait_for_timeout(1000)
            status, title, desc = await modal_handler(page, timeout)
            if status != "loading":
                break

    if status is True or status is False or status is None:
        btn_confirm = page.locator(".swal2-confirm.swal2-styled")
        btn_cancel = page.locator(".swal2-cancel.swal2-styled")
        btn_deny = page.locator(".swal2-deny.swal2-styled")

        if await btn_confirm.is_visible():
            text_btn = (await btn_confirm.inner_text()).strip()
            print(f'   → ALERT - "{text_btn}" clicking.')
            await btn_confirm.click()
        else:
            if await btn_cancel.is_visible():
                text_btn = (await btn_cancel.inner_text()).strip()
                print(f'   → ALERT - "{text_btn}" clicking.')
                await btn_cancel.click()
            else:
                if await btn_deny.is_visible():
                    text_btn = (await btn_deny.inner_text()).strip()
                    print(f'   → ALERT - "{text_btn}" clicking.')
                    await btn_deny.click()
        
        await page.locator(".swal2-container").wait_for(state="hidden", timeout=timeout)
        await page.wait_for_load_state("load")

        return status, title, desc