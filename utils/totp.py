# utils/totp.py

import pyotp
import time
from config import INS_OTP_SECRET

def get_totp():
    totp = pyotp.TOTP(INS_OTP_SECRET)
    code = totp.now()
    remaining = 30 - int(time.time()) % 30
    return code, remaining