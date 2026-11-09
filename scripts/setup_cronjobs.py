#!/usr/bin/env python3
"""
CRMNuggets - set up the cron-job.org jobs (Part C, "trial is ON" case).

What it does
  - Deletes the job that calls cron/send_trial_reminders.php
  - Creates or updates send_trial_sequence.php        daily 09:00 Africa/Lagos
  - Creates or updates send_corporate_lagos_sequence.php daily 11:00 Africa/Lagos
  - (optional, --city-push) send_city_push.php        every 10 minutes Africa/Lagos
  - Every job URL ends with ?key=<your CRON_SECRET_KEY>

Run it on YOUR computer, not on the server. Python 3.8+, no extra packages.

  export CRONJOB_API_KEY="..."      # cron-job.org > Settings > API > create key
  export CRON_SECRET_KEY="..."      # the value defined in config/database.php

  python3 setup_cronjobs.py                 # preview only, changes nothing
  python3 setup_cronjobs.py --apply         # make the changes
  python3 setup_cronjobs.py --apply --city-push

Trial removed later? Use:  python3 setup_cronjobs.py --apply --trial-off
(deletes all three trial jobs instead, per step 11).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.cron-job.org"
SITE = "https://crmnuggets.com"
TZ = "Africa/Lagos"

APPLY = "--apply" in sys.argv
CITY_PUSH = "--city-push" in sys.argv
TRIAL_OFF = "--trial-off" in sys.argv

api_key = os.environ.get("CRONJOB_API_KEY", "").strip()
secret = os.environ.get("CRON_SECRET_KEY", "").strip()
if not api_key or not secret:
    sys.exit("Set CRONJOB_API_KEY and CRON_SECRET_KEY environment variables first.")


def call(method, path, body=None):
    time.sleep(1.2)  # cron-job.org rate-limits the API; stay well under it
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode() or "{}"
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        sys.exit("API error %s on %s %s: %s" % (e.code, method, path, e.read().decode()))


def schedule(hours, minutes):
    # -1 means "every" in the cron-job.org schedule format
    return {"timezone": TZ, "expiresAt": 0, "hours": hours, "minutes": minutes,
            "mdays": [-1], "months": [-1], "wdays": [-1]}


def url_for(script, extra=""):
    return "%s/cron/%s?key=%s%s" % (SITE, script, urllib.parse.quote(secret, safe=""), extra)


WANTED = [
    ("send_trial_sequence.php", "CRMNuggets trial sequence", schedule([9], [0])),
    ("send_corporate_lagos_sequence.php", "CRMNuggets City sequence", schedule([11], [0])),
]
if CITY_PUSH:
    WANTED.append(("send_city_push.php", "CRMNuggets city push",
                   schedule([-1], [0, 10, 20, 30, 40, 50])))

TRIAL_SCRIPTS = ["send_trial_reminders.php", "send_trial_sequence.php",
                 "send_corporate_lagos_sequence.php"]

jobs = call("GET", "/jobs").get("jobs", [])
print("Found %d existing job(s) in your cron-job.org account.\n" % len(jobs))


def find(script):
    return [j for j in jobs if "/cron/" + script in j.get("url", "")]


def delete_all(script):
    for j in find(script):
        print("DELETE  #%s  %s" % (j["jobId"], j.get("title", script)))
        if APPLY:
            call("DELETE", "/jobs/%s" % j["jobId"])
    if not find(script):
        print("(none)  no job found for %s" % script)


if TRIAL_OFF:
    for s in TRIAL_SCRIPTS:
        delete_all(s)
else:
    delete_all("send_trial_reminders.php")
    for script, title, sched in WANTED:
        job = {"url": url_for(script), "title": title, "enabled": True,
               "saveResponses": True, "requestTimeout": 60, "schedule": sched}
        existing = find(script)
        if existing:
            print("UPDATE  #%s  %s" % (existing[0]["jobId"], script))
            if APPLY:
                call("PATCH", "/jobs/%s" % existing[0]["jobId"], {"job": job})
        else:
            print("CREATE  %s" % script)
            if APPLY:
                call("PUT", "/jobs", {"job": job})

print("\n" + ("Done." if APPLY else "Preview only. Re-run with --apply to make these changes."))
if CITY_PUSH and not TRIAL_OFF:
    print("Tip: open send_city_push.php?key=...&dry=1 in a browser once before trusting it.")
