# insera/auth.py

from config import INS_USERNAME, INS_PASSWORD, INS_URL
from utils.session import save_session
from utils.totp import get_totp


async def login_step1(page, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            print(f'[AUTH] Starting login... ({attempt}/{max_retries})')

            # FIX: selalu mulai dari halaman login yang bersih tiap percobaan
            await page.goto(INS_URL["login"], wait_until="load")
            await page.wait_for_timeout(500)

            current_url = page.url
            if current_url.startswith(INS_URL["login"]):
                print(f'  → Try logging in via OSS... >> {current_url}')

                btn_login = page.locator('#openIDLogin')
                if await btn_login.is_visible():
                    print("  → Redirecting to SSO...")
                    await btn_login.click()
                    try:
                        await page.wait_for_url(INS_URL["login-step"], timeout=10000)
                        print(f'  → SSO redirect detected.')
                    except:
                        await page.locator("#fake-username").wait_for(timeout=10000)
                        print(f'  → Inline SSO form detected.')

            print(f'  → Try logging in via SSO... >> {page.url}')
            await page.locator('#fake-username').fill(INS_USERNAME)
            await page.locator('#fake-password').fill(INS_PASSWORD)

            chk_term = page.locator("#acceptTerms")
            if await chk_term.is_visible():
                await chk_term.check(force=True)

            btn_login = page.locator('#fake-login')
            if await btn_login.is_visible():
                print('  → Clicking final login button.')
                await btn_login.click()

            print('  → Waiting for OTP form...')
            otp_frame_loc = page.frame_locator('iframe#jqueryDialogFrame')
            otp_frame = None
            for att in range(6):
                try:
                    await otp_frame_loc.locator('#pin').wait_for(timeout=5000)
                    otp_frame = otp_frame_loc
                    break
                except Exception:
                    print(f'  → OTP form not ready (attempt {att+1}/6)')
                    await page.wait_for_timeout(1000)

            if not otp_frame:
                print('[ERR] Otp form not found after 30s.')
                continue

            print('  → OTP form ready.')
            return True

        except Exception as e:
            print(f'[ERR] Login failed on attempt {attempt}: {e}')
            if attempt == max_retries:
                return False
            await page.wait_for_timeout(2000)

    return False


async def login_step2(page, max_retries=3):
    """
    OTP di-generate OTOMATIS dari INS_OTP_SECRET (TOTP),
    tidak perlu input manual lagi.
    """
    otp_frame = page.frame_locator('iframe#jqueryDialogFrame')

    for attempt in range(1, max_retries + 1):
        try:
            otp_field = otp_frame.locator('#pin')
            await otp_field.wait_for(timeout=10000)

            otp_code, remaining = get_totp()
            print(f'  → Using OTP {otp_code} (valid {remaining}s)')

            await otp_field.fill(otp_code)

            try:
                await otp_frame.get_by_role("button", name="Submit").nth(0).click()
            except:
                await otp_field.press("Enter")

            print('  → OTP submitted, waiting for redirect...')
            await page.wait_for_load_state("networkidle")
            await page.wait_for_url(INS_URL["home"], timeout=15000)

            await save_session(page.context)
            return True

        except Exception as e:
            print(f'[ERR] OTP step failed on attempt {attempt}: {e}')
            if attempt == max_retries:
                return False
            await page.wait_for_timeout(5000)

    return False