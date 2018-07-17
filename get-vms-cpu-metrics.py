#!/usr/bin/env python3
from multiprocessing import Queue
import time
import csv
import subprocess
import argparse
from datetime import datetime, timedelta
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import json
#from multiprocessing.pool import ThreadPool



"""
parameters:
    queue -- queue where we put vm metrics results
    vmId -- vmId to work with
    interval -- the interval in In ISO 8601 duration format, e.g. PT1M\". Default PT1H
    days -- how many days of metrics we gather
"""
def getVMMetrics(queue, vmId, interval, days):
    print("Getting metrics for %s" % vmId)
    metrics_start_time = (datetime.today() - timedelta(days = days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    metrics = json.loads(subprocess.check_output(["az", "monitor", "metrics", "list", "--start-time", metrics_start_time, "--interval", interval, "--resource", vmId]).decode('utf-8'))
    queue.put((vmId, metrics))

    print ("Done processing vm %s" % vmId)

def isAnyJobAlive(jobs):
    for j in jobs:
        if not j.done():
            return True
    return False

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--interval", help="Interval of metrics detalization. In ISO 8601 duration format, eg \"PT1M\".", default="PT1H", nargs='?')
    parser.add_argument("--max-workers", help="How much parallel queries to run. Lower the value to reduce memory consumption", default=50, nargs='?', type=int)
    parser.add_argument("--days", help="How many days of metrics we will gather per VM", default=30, nargs='?', type=int)
    args = parser.parse_args()
    print ('Getting vms list')
    vms_list = json.loads(subprocess.check_output(["az", "vm", "list"]).decode('utf-8'))
    print ('Starting processing')
    pool = ThreadPoolExecutor(max_workers=args.max_workers)
    q = Queue()
    vms = {}
    for vm in vms_list:
        vms[vm['id']] = vm
    results = []
    try:
        for vm in vms_list:
            f = pool.submit(getVMMetrics, q, vm['id'], args.interval, args.days)
            results.append(f)

        headerWritten = False

        with open('vms_metrics.csv', 'w') as outfile:
            csv_w = csv.writer( outfile )
            while not q.empty() or isAnyJobAlive(results):
                while not q.empty():

                    (vmId, metrics) = q.get()
                    timeseries = metrics['value'][0]['timeseries']
                    metrics = timeseries[0]['data'] if len(timeseries) > 0 else []
                    if not metrics:
                        continue
                    for m in metrics:
                        m['vmName'] = vms[vmId]['name']
                        if m['average'] is None:
                            m['average'] = 0

                    if not headerWritten:
                        csv_w.writerow( metrics[0].keys() )
                        headerWritten = True

                    for m in metrics:
                        csv_w.writerow( m.values() )

    except subprocess.CalledProcessError as e:
        print(e.output)

    q.close()
    q.join_thread()


if __name__ == "__main__":
    main()
