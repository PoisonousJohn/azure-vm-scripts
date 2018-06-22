#!/usr/bin/env python3
from multiprocessing import Queue
import time
import csv
import subprocess
from datetime import datetime, timedelta
from threading import Thread
import json
#from multiprocessing.pool import ThreadPool



def getVMMetrics(queue, vmId):
    print("Getting metrics for %s" % vmId)
    metrics_start_time = (datetime.today() - timedelta(days = 60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    metrics = json.loads(subprocess.check_output(["az", "monitor", "metrics", "list", "--start-time", metrics_start_time, "--interval", "P1D", "--resource", vmId]).decode('utf-8'))
    queue.put((vmId, metrics))

    print ("Done processing vm %s" % vmId)


def main():
    print ('Getting vms list')
    vms_list = json.loads(subprocess.check_output(["az", "vm", "list"]).decode('utf-8'))
    print ('Starting processing')
    #pool = ThreadPool()
    q = Queue()
    vms = {}
    metrics_per_vm = {}
    for vm in vms_list:
        vms[vm['id']] = vm
    results = []
    try:
        for vm in vms_list:
            t = Thread(target=getVMMetrics, args=(q, vm['id']))
            results.append(t)
            t.start()

        for result in results:
            result.join()

        all_metrics = []
        columns = []

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

            all_metrics.extend(metrics)

        if not all_metrics:
            print("No results found")
            return

        with open('vms_metrics.csv', 'w') as outfile:
            csv_w = csv.writer( outfile )
            columns = all_metrics[0].keys()
            csv_w.writerow( columns )
            for metric in all_metrics:
                csv_w.writerow( metric.values() )

    except subprocess.CalledProcessError as e:
        print(e.output)

if __name__ == "__main__":
    main()