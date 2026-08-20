# automation/log_utils.py

import builtins
import re

# Kode warna ANSI. Pakai 256-color untuk oranye & pink karena warna
# standar 8/16 tidak punya varian itu.
COLOR_INFO = "\033[38;5;25m"    # biru tua
COLOR_OK = "\033[32m"           # hijau
COLOR_WARN = "\033[38;5;208m"   # oranye
COLOR_ERR = "\033[38;5;213m"    # merah muda
COLOR_RESET = "\033[0m"

_PREFIX_PATTERN = re.compile(r"^(\[INFO\]|\[OK\]|\[WARN\]|\[ERR\])")

_PREFIX_COLORS = {
    "[INFO]": COLOR_INFO,
    "[OK]": COLOR_OK,
    "[WARN]": COLOR_WARN,
    "[ERR]": COLOR_ERR,
}

_original_print = builtins.print
_enabled = False


def _colored_print(*args, **kwargs):
    if not args or not isinstance(args[0], str):
        return _original_print(*args, **kwargs)

    text = args[0]
    # Buang newline/spasi di depan dulu (banyak print pakai "\n=== ...")
    # supaya prefix tetap terdeteksi meski ada whitespace di depannya.
    stripped = text.lstrip("\n \t")
    match = _PREFIX_PATTERN.match(stripped)

    if not match:
        return _original_print(*args, **kwargs)

    color = _PREFIX_COLORS[match.group(1)]
    leading_ws = text[: len(text) - len(stripped)]
    colored_text = f"{leading_ws}{color}{stripped}{COLOR_RESET}"

    new_args = (colored_text,) + args[1:]
    return _original_print(*new_args, **kwargs)


def enable_colored_logs():
    """Aktifkan pewarnaan otomatis untuk print() dengan prefix [INFO]/[OK]/
    [WARN]/[ERR]. Panggil sekali di awal entry-point file. Aman dipanggil
    berkali-kali (tidak dobel patch)."""
    global _enabled
    if _enabled:
        return

    # Windows Terminal modern & VS Code terminal sudah dukung ANSI. Untuk
    # cmd.exe lama, aktifkan virtual terminal processing dulu.
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

    builtins.print = _colored_print
    _enabled = True