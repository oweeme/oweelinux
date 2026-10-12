def report(tag):
    import os
    d = {}
    for l in open("/proc/self/smaps_rollup"):
        k, _, v = l.partition(":")
        if k in ("Rss", "Pss", "Private_Clean", "Private_Dirty", "Pss_Anon"): d[k] = int(v.split()[0]) / 1024
    uss = d.get("Private_Clean", 0) + d.get("Private_Dirty", 0)
    print(f"RESULT {tag}: Rss={d['Rss']:.0f} Pss={d['Pss']:.0f} USS={uss:.0f} MB", flush=True)
