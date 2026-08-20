# automation/auth.py

from config import WFM_URL
from settings import settings
from .modal import modal_handler
from utils.session import save_session

async def ensure_logged_in(page):
    try:
        if await page.locator("#searchInc").is_visible(timeout=2000):
            return True
    except:
        pass

    try:
        if await page.locator('input[name="username"]').is_visible(timeout=2000):
            login_ok = await login(page)
            return login_ok
    except:
        pass

    await page.reload(wait_until="networkidle")
    try:
        if await page.locator("#searchInc").is_visible(timeout=2000):
            return True
    except:
        pass

    return False

async def login(page, max_retries=3):

    for attempt in range(1, max_retries + 1):
        try:
            print("[AUTH] Starting login...")
            await page.locator('input[name="username"]').fill(settings.WFM_USERNAME)
            await page.locator('input[name="password"]').fill(settings.WFM_PASSWORD)
            
            checkbox = page.get_by_role("checkbox", name="Remember Me")
            if await checkbox.is_visible():
                await checkbox.check()
            
            await page.get_by_role("button", name="Log In").click()

            status, title, desc = await modal_handler(page)

            if status is False:
                if attempt < max_retries:
                    print("   → Retrying login, reload page...")
                    await page.reload(wait_until="networkidle")
                    await page.wait_for_timeout(1000)
                    continue
                else:
                    print("   → Login failed after retry.")
                    return False
            
            await get_otp(page)

            link_assr = page.get_by_role("link", name="WORKORDER ASSURANCE")
            if await link_assr.is_visible():
                await link_assr.click()
                
            await page.wait_for_load_state("networkidle")
            await save_session(page.context)

            print(f"   → Login OK, redirect to: {page.url}")

            return True
            
        except Exception as e:
            print("[ERR] login failed : ", e)
            if attempt == max_retries:
                return False
            await page.wait_for_timeout(1000)

    return False

async def get_otp(page):

    while True:
        try:
            await page.wait_for_function(
                "document.location.href.toLowerCase().includes('otp') || document.querySelector('input[name=\"otp\"]')",
                timeout=10000
            )
        except:
            print("   → Tidak ada OTP (URL tidak berubah dan field tidak muncul).")
            return True
        
        print("   → Waiting OTP process...")

        otp_field = page.locator('input[name="otp"]')
        await otp_field.wait_for(state="visible", timeout=15000)

        await fill_submit_otp(page, otp_field)

        status, title, desc = await modal_handler(page)

        if status is False:
            await fill_submit_otp(page, otp_field)
            status, title, desc = await modal_handler(page)
        try:
            await page.wait_for_url(f'{WFM_URL["home"]}', timeout=10000)
            print("   → Welcome to homepage.")
        except:
            print(f"[WARN] Still not on homepage, current url: {page.url}")

        await page.wait_for_load_state("domcontentloaded")
        break
    
    return True

async def fill_submit_otp(page, otp_field):
    otp = input("   → Enter OTP: ")
    await otp_field.fill("")
    await otp_field.fill(otp)
    await page.get_by_role("button", name="Sign In").click()