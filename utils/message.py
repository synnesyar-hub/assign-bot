# utils/message.py

from job_queue_pkg.job_queue import get_jobs_msg
from utils.mapping import lower_status

FINAL_STATUS = {"FINALCHECK", "RESOLVED", "MEDIACARE", "SALAMSIM", "CLOSED"}

async def reply_done_message(client, chat_id, msg_id):
    jobs = get_jobs_msg(chat_id, msg_id)

    labor_not_found = [j for j in jobs if j.get("labor_status", "").upper() == "NOT_FOUND"]
    if labor_not_found:
        lines = [f"{job['labor']} labor not found" for job in labor_not_found]
        await client.send_message(chat_id, "\n".join(lines), reply_to=msg_id)
        return

    if all(j.get("status", "").upper() == "NOT_FOUND" for j in jobs):
        lines = [f"{job['inc']} not found" for job in jobs]
        await client.send_message(chat_id, "\n".join(lines), reply_to=msg_id)
        return

    has_pending = any(
        j["status"].upper() == "PENDING"
        and j.get("wo_status", "").upper() != "CANCELED"
        for j in jobs
    )
    if has_pending:
        return

    done_jobs = [
        j for j in jobs
        if j["status"].upper() == "DONE"
        or j.get("inc_status", "").upper() in FINAL_STATUS
    ]
    total_done = len(done_jobs)

    wo_canceled = [
        j for j in jobs 
        if j.get("wo_status", "").upper() == "CANCELED"
        and j.get("status", "").upper() != "CLOSED"
        and j.get("inc_status", "").upper() not in FINAL_STATUS
    ]

    if len(jobs) == 1:
        j = jobs[0]
        status_u = j.get("status", "").upper()
        inc_status_u = j.get("inc_status", "").upper()
        wo_status_u = j.get("wo_status", "").upper()

        if status_u == "NOT_FOUND":
            await client.send_message(chat_id, f"{job['inc']} not found", reply_to=msg_id)
            return
        
        if status_u == "DONE" or inc_status_u in FINAL_STATUS or status_u == "CLOSED":
            text = "/done #assign"
            if status_u == "CLOSED" or inc_status_u in FINAL_STATUS:
                text += f"\n\n{j['inc']} {lower_status(inc_status_u or status_u)}"
            await client.send_message(chat_id, text, reply_to=msg_id)
            return
        
        if wo_status_u == "CANCELED" and status_u != "CLOSED" and inc_status_u not in FINAL_STATUS:
            await client.send_message(chat_id, f"{j['inc']} wo canceled", reply_to=msg_id)
            return

        inc_status = inc_status_u or status_u
        await client.send_message(chat_id, f"{job['inc']} {lower_status(inc_status)}", reply_to=msg_id)
        return

    sub_msgs = []

    for job in wo_canceled:
        sub_msgs.append(f"{job['inc']} wo canceled")

    for job in jobs:
        status_u = job.get("status", "").upper()
        inc_status_u = job.get("inc_status", "").upper()

        if status_u == "NOT_FOUND":
            sub_msgs.append(f"{job['inc']} not found")
            continue

        if (inc_status_u in FINAL_STATUS or (status_u == "CLOSED")):
            sub_msgs.append(f"{job['inc']} {lower_status(inc_status_u or status_u)}")
            continue

        if job not in done_jobs and job not in wo_canceled:
            inc_status = inc_status_u or status_u
            sub_msgs.append(f"{job['inc']} {lower_status(inc_status)}")

    if len(wo_canceled) == len(jobs):
        await client.send_message(chat_id, "\n".join(sub_msgs), reply_to=msg_id)
        return

    if total_done > 0:
        text = "/done #assign" if total_done == 1 else f"/done #assign{total_done}"
        if sub_msgs:
            text += "\n\n" + "\n".join(sub_msgs)
        await client.send_message(chat_id, text, reply_to=msg_id)