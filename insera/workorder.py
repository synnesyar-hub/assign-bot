# insera/workorder.py

import asyncio, traceback

async def find_wo(inc_list, page):
    
    find_inc = page.locator('#findIncidentGlobal')
    await find_inc.wait_for(timeout=8000)

    for inc_number in inc_list:
        print(f'[FIND] {inc_number}...')

        try:
            await find_inc.fill(inc_number)
            await find_inc.press("Enter")

            await page.wait_for_load_state("networkidle")
            await page.locator(".page-loader").wait_for(state="hidden")

            try:
                loader = page.locator('div.page-loader')
                if await loader.is_visible(timeout=2000):
                    print('  → Loading...')
                    await loader.wait_for(state="hidden", timeout=30000)
            except:
                pass

            try:
                dialog = page.locator('form.vex-dialog-form')
                await dialog.wait_for(state="visible", timeout=5000)
                message = await page.locator('div.vex-dialog-message').inner_text()
                if "Ticket Not Found" in message:
                    print(f'  → ALERT - {message}')
                    await page.locator('button.vex-dialog-button-primary').click()
                    return False
                print(f'  → ALERT - {message}')
            except:
                pass
            
            

        
        except Exception as e:
            traceback.print_exc()
            print(f'[ERR] Ticket {inc_number}: {e}')

async def create_wo():
    # TODO:
    pass