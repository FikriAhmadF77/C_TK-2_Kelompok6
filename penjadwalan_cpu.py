#!/usr/bin/env python3
"""
penjadwalan_cpu.py
Simulator sederhana algoritma penjadwalan CPU: FCFS, SJF (non-preemptive),
SRTF (preemptive), Priority (non-preemptive), dan Round Robin (RR).

Tugas Kelompok K-2 - Sistem Operasi (USA-WP2260110) - Kelas C
Konteks: penjadwalan tugas pembacaan sensor, kontrol pompa irigasi, dan
pengiriman data pada gateway IoT (srv-iot-<NIM>).

Dataset kelas:
    P1(0,3,1)  P2(0,6,3)  P3(2,4,2)  P4(3,8,4)  P5(4,2,1)
Format: (arrival, burst, priority); priority kecil = prioritas tinggi
Quantum Round Robin: 2 dan 3

Cara menjalankan (lewat SSH ke VM gateway):
    ssh -p 2222 mhs@127.0.0.1
    python3 penjadwalan_cpu.py

Hanya memakai pustaka standar Python 3 (tidak perlu pip install apa pun),
sehingga dapat dijalankan langsung di VM Ubuntu Server lewat SSH.
"""

from collections import deque

# (nama, arrival, burst, priority)
PROCESSES = [
    ("P1", 0, 3, 1),
    ("P2", 0, 6, 3),
    ("P3", 2, 4, 2),
    ("P4", 3, 8, 4),
    ("P5", 4, 2, 1),
]


def hitung_metrik(gantt, order, arrival, burst, completion, start_first):
    """Menghitung turnaround, waiting, dan response time tiap proses."""
    rows = []
    tt_sum = wt_sum = rt_sum = 0
    for name in order:
        a, b, c, s = arrival[name], burst[name], completion[name], start_first[name]
        tt = c - a          # turnaround time = completion - arrival
        wt = tt - b         # waiting time   = turnaround - burst
        rt = s - a          # response time  = start pertama - arrival
        tt_sum += tt
        wt_sum += wt
        rt_sum += rt
        rows.append((name, a, b, c, tt, wt, rt))
    n = len(order)
    return rows, tt_sum / n, wt_sum / n, rt_sum / n


def fcfs(procs):
    order = sorted(procs, key=lambda p: (p[1], procs.index(p)))
    t, completion, start_first, gantt = 0, {}, {}, []
    for name, a, b, pr in order:
        s = max(t, a)
        start_first[name] = s
        e = s + b
        gantt.append((name, s, e))
        completion[name] = e
        t = e
    return gantt, [p[0] for p in order], completion, start_first


def sjf_non_preemptive(procs):
    t, completion, start_first, gantt, done = 0, {}, {}, [], set()
    while len(done) < len(procs):
        avail = [p for p in procs if p[0] not in done and p[1] <= t]
        if not avail:
            t = min(p[1] for p in procs if p[0] not in done)
            continue
        name, a, b, pr = min(avail, key=lambda p: (p[2], p[1], procs.index(p)))
        s = t
        start_first[name] = s
        e = s + b
        gantt.append((name, s, e))
        completion[name] = e
        t = e
        done.add(name)
    return gantt, [g[0] for g in gantt], completion, start_first


def srtf_preemptive(procs):
    rem = {p[0]: p[2] for p in procs}
    arrival = {p[0]: p[1] for p in procs}
    t, completion, start_first, gantt, done = 0, {}, {}, [], set()
    cur_name, seg_start = None, None
    max_time = sum(p[2] for p in procs) + max(p[1] for p in procs) + 5
    while len(done) < len(procs) and t < max_time:
        avail = [p[0] for p in procs if p[0] not in done and p[1] <= t and rem[p[0]] > 0]
        if not avail:
            t += 1
            continue
        pick = min(avail, key=lambda n: (rem[n], arrival[n], n))
        if pick not in start_first:
            start_first[pick] = t
        if pick != cur_name:
            if cur_name is not None:
                gantt.append((cur_name, seg_start, t))
            seg_start, cur_name = t, pick
        rem[pick] -= 1
        t += 1
        if rem[pick] == 0:
            completion[pick] = t
            done.add(pick)
            gantt.append((cur_name, seg_start, t))
            cur_name = None
    return gantt, [p[0] for p in procs], completion, start_first


def priority_non_preemptive(procs):
    t, completion, start_first, gantt, done = 0, {}, {}, [], set()
    while len(done) < len(procs):
        avail = [p for p in procs if p[0] not in done and p[1] <= t]
        if not avail:
            t = min(p[1] for p in procs if p[0] not in done)
            continue
        name, a, b, pr = min(avail, key=lambda p: (p[3], p[1], procs.index(p)))
        s = t
        start_first[name] = s
        e = s + b
        gantt.append((name, s, e))
        completion[name] = e
        t = e
        done.add(name)
    return gantt, [g[0] for g in gantt], completion, start_first


def round_robin(procs, quantum):
    rem = {p[0]: p[2] for p in procs}
    arr_sorted = sorted(procs, key=lambda p: (p[1], procs.index(p)))
    n = len(procs)
    queue = deque()
    completion, start_first, gantt = {}, {}, []
    i = 0
    t = arr_sorted[0][1]
    while i < n and arr_sorted[i][1] <= t:
        queue.append(arr_sorted[i][0])
        i += 1
    while len(completion) < n:
        if not queue:
            t = arr_sorted[i][1]
            while i < n and arr_sorted[i][1] <= t:
                queue.append(arr_sorted[i][0])
                i += 1
            continue
        name = queue.popleft()
        if name not in start_first:
            start_first[name] = t
        run = min(quantum, rem[name])
        run_start, t_end = t, t + run
        while i < n and arr_sorted[i][1] <= t_end:
            queue.append(arr_sorted[i][0])
            i += 1
        rem[name] -= run
        gantt.append((name, run_start, t_end))
        t = t_end
        if rem[name] > 0:
            queue.append(name)
        else:
            completion[name] = t_end
    return gantt, [p[0] for p in procs], completion, start_first


def cetak_gantt(gantt):
    """Mencetak Gantt chart berbasis teks (ASCII)."""
    bar = "|"
    waktu = "0"
    for name, s, e in gantt:
        lebar = max(len(name), len(str(e))) + 2
        bar += f" {name} ".center(lebar, " ") + "|"
        waktu += str(e).rjust(lebar + 1)
    print(bar)
    print(waktu)


def cetak_tabel(rows, avg_tt, avg_wt, avg_rt):
    print(f"{'Proses':<7}{'Arrival':<9}{'Burst':<7}{'Selesai':<9}"
          f"{'Turnaround':<12}{'Waiting':<9}{'Response':<9}")
    for name, a, b, c, tt, wt, rt in rows:
        print(f"{name:<7}{a:<9}{b:<7}{c:<9}{tt:<12}{wt:<9}{rt:<9}")
    print(f"Rata-rata turnaround = {avg_tt:.2f} | "
          f"rata-rata waiting = {avg_wt:.2f} | "
          f"rata-rata response = {avg_rt:.2f}")


def jalankan(nama_algoritma, hasil):
    gantt, order, completion, start_first = hasil
    arrival = {p[0]: p[1] for p in PROCESSES}
    burst = {p[0]: p[2] for p in PROCESSES}
    rows, avg_tt, avg_wt, avg_rt = hitung_metrik(
        gantt, order, arrival, burst, completion, start_first)
    print(f"\n=== {nama_algoritma} ===")
    cetak_gantt(gantt)
    cetak_tabel(rows, avg_tt, avg_wt, avg_rt)
    return avg_tt, avg_wt, avg_rt


def main():
    print("Simulator Penjadwalan CPU - Gateway Smart Farming (Kelas C)")
    print("Dataset:", PROCESSES)

    ringkasan = {}
    ringkasan["FCFS"] = jalankan("FCFS", fcfs(PROCESSES))
    ringkasan["SJF (non-preemptive)"] = jalankan(
        "SJF (non-preemptive)", sjf_non_preemptive(PROCESSES))
    ringkasan["SRTF (preemptive)"] = jalankan(
        "SRTF (preemptive)", srtf_preemptive(PROCESSES))
    ringkasan["Priority (non-preemptive)"] = jalankan(
        "Priority (non-preemptive)", priority_non_preemptive(PROCESSES))
    ringkasan["Round Robin q=2"] = jalankan(
        "Round Robin (quantum=2)", round_robin(PROCESSES, 2))
    ringkasan["Round Robin q=3"] = jalankan(
        "Round Robin (quantum=3)", round_robin(PROCESSES, 3))

    print("\n=== Ringkasan Perbandingan ===")
    print(f"{'Algoritma':<28}{'Avg Turnaround':<16}{'Avg Waiting':<14}{'Avg Response':<14}")
    for nama, (tt, wt, rt) in ringkasan.items():
        print(f"{nama:<28}{tt:<16.2f}{wt:<14.2f}{rt:<14.2f}")


if __name__ == "__main__":
    main()
