# services/gsheet_service.py

import time
import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

CREDENTIALS_FILE = "gsheet_credentials.json"
SPREADSHEET_ID = "1Eyhq2rEvmFbj15_GOmvlDZXzN-hr3uYhYiLAzCT2yy8"

_client = None
_worksheets = {}


def _with_retry(func, *args, max_retries=5, base_delay=3, **kwargs):
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "Quota exceeded" in str(e)
            if is_rate_limit and attempt < max_retries:
                delay = base_delay * attempt
                print(f"[WARN] Rate limit Google Sheets (percobaan {attempt}/{max_retries}), tunggu {delay}s.")
                time.sleep(delay)
                continue
            raise


def get_worksheet(worksheet_name: str):
    global _client

    if worksheet_name in _worksheets:
        return _worksheets[worksheet_name]

    if _client is None:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)

    spreadsheet = _client.open_by_key(SPREADSHEET_ID)
    ws = spreadsheet.worksheet(worksheet_name)
    _worksheets[worksheet_name] = ws
    return ws


def get_existing_incs(worksheet_name: str) -> set:
    ws = get_worksheet(worksheet_name)
    col_values = ws.col_values(1)
    return set(col_values[1:])


def write_header_if_needed(worksheet_name: str, headers: list[str]):
    ws = get_worksheet(worksheet_name)
    first_row = ws.row_values(1)
    if not first_row:
        _ensure_col_capacity(worksheet_name, len(headers))
        ws.append_row(headers)


def _ensure_col_capacity(worksheet_name: str, needed_total_cols: int):
    """
    Pastikan worksheet punya cukup kolom fisik. Google Sheets punya batas
    default (biasanya 26 atau 80 tergantung template) yang harus di-expand
    dulu sebelum menulis ke kolom di luar batas itu.
    """
    ws = get_worksheet(worksheet_name)
    if ws.col_count < needed_total_cols:
        ws.add_cols(needed_total_cols - ws.col_count)


def append_tickets(tickets: list[dict], worksheet_name: str):
    if not tickets:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket untuk ditambahkan.")
        return

    headers = list(tickets[0].keys())
    write_header_if_needed(worksheet_name, headers)

    existing_incs = get_existing_incs(worksheet_name)

    ws = get_worksheet(worksheet_name)
    rows_to_add = []

    for ticket in tickets:
        inc_number = ticket.get("INCIDENT", "")
        if inc_number in existing_incs:
            continue

        row = [ticket.get(h, "") for h in headers]
        rows_to_add.append(row)

    if rows_to_add:
        ws.append_rows(rows_to_add)
        print(f"[OK] [{worksheet_name}] {len(rows_to_add)} tiket baru ditambahkan.")
    else:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket baru.")


def upsert_tickets(tickets: list[dict], worksheet_name: str):
    """
    Seperti append_tickets, tapi kalau INCIDENT sudah ada di sheet,
    HANYA kolom yang ada di data scrape (tickets[0].keys()) yang ditimpa --
    kolom lain seperti STATUS ONT / ONU RX hasil auto-resolve TIDAK disentuh.
    Ticket yang belum ada tetap di-append seperti biasa.
    """
    if not tickets:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket untuk diproses.")
        return

    scrape_headers = list(tickets[0].keys())
    write_header_if_needed(worksheet_name, scrape_headers)

    ws = get_worksheet(worksheet_name)
    full_header = ws.row_values(1)
    header_col_map = {name: idx for idx, name in enumerate(full_header)}  # 0-based

    inc_col_values = ws.col_values(1)
    inc_to_row = {val: idx + 1 for idx, val in enumerate(inc_col_values) if idx > 0}

    batch_updates = []
    rows_to_append = []

    for ticket in tickets:
        inc_number = ticket.get("INCIDENT", "")
        if not inc_number:
            continue

        if inc_number in inc_to_row:
            row_idx = inc_to_row[inc_number]
            # Update SATU CELL per kolom scrape saja -- kolom lain di baris ini
            # (mis. STATUS ONT, ONU RX hasil auto-resolve) tidak disentuh.
            for field_name in scrape_headers:
                if field_name not in header_col_map:
                    continue
                col_idx_1based = header_col_map[field_name] + 1
                cell_a1 = gspread.utils.rowcol_to_a1(row_idx, col_idx_1based)
                batch_updates.append({"range": cell_a1, "values": [[ticket.get(field_name, "")]]})
        else:
            row_values = [ticket.get(h, "") for h in full_header]
            rows_to_append.append(row_values)

    if batch_updates:
        ws.batch_update(batch_updates)
        updated_inc_count = len(set(inc for inc in inc_to_row if inc in [t.get("INCIDENT") for t in tickets]))
        print(f"[OK] [{worksheet_name}] Data ticket lama diperbarui (kolom scrape saja, kolom lain dipertahankan).")

    if rows_to_append:
        ws.append_rows(rows_to_append)
        print(f"[OK] [{worksheet_name}] {len(rows_to_append)} tiket baru ditambahkan.")

    if not batch_updates and not rows_to_append:
        print(f"[INFO] [{worksheet_name}] Tidak ada perubahan.")


def _ensure_columns_exist(worksheet_name: str, new_columns: list[str]) -> dict:
    ws = get_worksheet(worksheet_name)
    header = _with_retry(ws.row_values, 1)

    col_map = {name: idx + 1 for idx, name in enumerate(header)}

    missing = [c for c in new_columns if c not in col_map]
    if missing:
        needed_total_cols = len(header) + len(missing)
        _ensure_col_capacity(worksheet_name, needed_total_cols)

        start_col = len(header) + 1
        end_col = start_col + len(missing) - 1
        cell_range = f"{gspread.utils.rowcol_to_a1(1, start_col)}:{gspread.utils.rowcol_to_a1(1, end_col)}"
        _with_retry(ws.update, cell_range, [missing])

        for i, name in enumerate(missing):
            col_map[name] = start_col + i

    return col_map


def update_ticket_fields(worksheet_name: str, inc_number: str, fields: dict):
    ws = get_worksheet(worksheet_name)
    col_map = _ensure_columns_exist(worksheet_name, list(fields.keys()))

    inc_col_values = _with_retry(ws.col_values, 1)
    row_index = None
    for i, val in enumerate(inc_col_values, start=1):
        if val == inc_number:
            row_index = i
            break

    if row_index is None:
        print(f"[WARN] [{worksheet_name}] INC {inc_number} tidak ditemukan, skip update.")
        return False

    batch_data = []
    for field_name, value in fields.items():
        col_index = col_map[field_name]
        cell_a1 = gspread.utils.rowcol_to_a1(row_index, col_index)
        batch_data.append({"range": cell_a1, "values": [[value]]})

    _with_retry(ws.batch_update, batch_data)
    return True

def sync_tickets(tickets: list[dict], worksheet_name: str):
    if not tickets:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket hasil scrape, skip sync (tidak menghapus apa pun).")
        return

    upsert_tickets(tickets, worksheet_name)

    current_incs = set(t.get("INCIDENT", "") for t in tickets if t.get("INCIDENT"))

    ws = get_worksheet(worksheet_name)
    inc_col_values = ws.col_values(1)

    rows_to_delete = []
    for idx, inc in enumerate(inc_col_values):
        if idx == 0:
            continue
        if inc and inc not in current_incs:
            rows_to_delete.append(idx + 1)

    if rows_to_delete:
        # FIX: hapus semua baris dalam SATU batch request, bukan loop delete_rows()
        requests = []
        for row_idx in sorted(rows_to_delete, reverse=True):
            requests.append({
                "deleteDimension": {
                    "range": {
                        "sheetId": ws.id,
                        "dimension": "ROWS",
                        "startIndex": row_idx - 1,
                        "endIndex": row_idx,
                    }
                }
            })
        ws.spreadsheet.batch_update({"requests": requests})
        print(f"[OK] [{worksheet_name}] {len(rows_to_delete)} tiket dihapus karena sudah tidak relevan dengan filter.")
    else:
        print(f"[INFO] [{worksheet_name}] Tidak ada tiket yang perlu dihapus.")

    return True

def get_all_incs(worksheet_name: str) -> list[str]:
    
    ws = get_worksheet(worksheet_name)
    col_values = _with_retry(ws.col_values, 1)
    return [v for v in col_values[1:] if v.strip()]