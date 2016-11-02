import json
import multiprocessing.dummy as multiprocessing
from datetime import datetime
import requests
import yaml
import time
import sys

data = {}
bad_sites = {}

slack_icon_mapping = {
    "internal_error":":interrobang:",
    "timeout":":timer_clock:",
    "bad_status":":skull_and_crossbones:"
}

def slack(url, channel, username, type, message):
    #print(username, type, message)
    requests.post(url, json={"channel": channel, "icon_emoji": slack_icon_mapping[type], "username": "Monitoring: %s"%username, "text": message})

def cycle_actions(actions, username, type, msg):
    global data
    for action in actions:
        if data["triggers"][action]["type"] == "slack":
            print("Sending slack %s"%msg)
            slack(data["triggers"][action]["url"], data["triggers"][action]["channel"], username, type, msg)

def on_error(reason, type, item):
    global data
    global bad_sites
    msg = "<%s|%s> is unavailable!\n%s"%(item["url"], item["name"], reason)
    now = datetime.now()
    if "ignore_hours" in item and now.hour in item["ignore_hours"]:
        print("Ignoring errors for %s because they occured within range of ignore_hours"%item['name'])
        return

    if item["url"] not in bad_sites:
        bad_sites[item["url"]]= {"origin":now, "last_alarm":now}
    else:
        downtime = datetime.now()-bad_sites[item["url"]]["origin"]
        msg += "\nHas been down for %s"%pretty_date(downtime)

    time_since_alarm = now-bad_sites[item["url"]]["last_alarm"]
    frequency = item.get("trigger_frequency", data["trigger_frequency"])
    if time_since_alarm.seconds == 0 or time_since_alarm.seconds > frequency:
        cycle_actions(item["on_error"], item['name'], type, msg)
        bad_sites[item["url"]]["last_alarm"] = now

def ping(key):
    global data, bad_sites
    item = data["monitors"][key]
    while True:
        try:
            res = requests.get(item["url"], timeout=3)
            print("%s response: %s"%(item["url"], res.status_code))
            if res.status_code == 200:
                #  check if we are back to normal
                if item["url"] in bad_sites:
                    print("Back to normal")
                    downtime = datetime.now()-bad_sites[item["url"]]["origin"]
                    msg = "%s is back (after %s of downtime)"%(item["name"], pretty_date(downtime))
                    cycle_actions(item["on_error"], item['name'], ":innocent:", msg)
                    del bad_sites[item["url"]]
            else:
                on_error("Status code %s"%res.status_code, "bad_status", item)
        except requests.exceptions.Timeout as e:
            on_error("Timed out", "timeout", item)
        except Exception as e:
            print("Exception ",e)
            on_error("Unknown Internal Error", "internal_error", item)
        except KeyboardInterrupt:
            print("keyboard interrupt")
            return
        interval = item.get("interval", data["interval"])
        time.sleep(interval)
def run():
    global data, bad_sites
    data = yaml.load(open("./config.yml", "r+").read())
    pool = multiprocessing.Pool(len(data["monitors"]))
    while True:
        try:
            pool.map_async(ping, data["monitors"]).get(9999999) # for keyboard interrupt
        except KeyboardInterrupt:
            print("Exiting")
            sys.exit()

def pretty_date(delta):
    d = delta.days
    h, s = divmod(delta.seconds, 3600)
    m, s = divmod(s, 60)
    labels = ['day', 'hour', 'minute', 'second']
    dhms = ['%s %s%s' % (i, lbl, 's' if i != 1 else '') for i, lbl in zip([d, h, m, s], labels)]
    for start in range(len(dhms)):
        if not dhms[start].startswith('0'):
            break
    for end in range(len(dhms)-1, -1, -1):
        if not dhms[end].startswith('0'):
            break
    return ', '.join(dhms[start:end+1])

if __name__ == "__main__":
    print("Starting monitoring")
    run()
