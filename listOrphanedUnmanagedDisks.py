#!/usr/bin/env python3
from multiprocessing import Queue
import time
import csv
import subprocess
from threading import Thread
import json
#from multiprocessing.pool import ThreadPool

def flattenjson( b, delim ):
    val = {}
    for i in b.keys():
        if isinstance( b[i], dict ):
            get = flattenjson( b[i], delim )
            for j in get.keys():
                val[ i + delim + j ] = get[j]
        else:
            val[i] = b[i]

    return val

def processContainer(queue, acc, acc_key, container):
    print ('Checking container %s/%s' % (acc['name'], container['name']))
    blobs_list = json.loads(subprocess.check_output(["az", "storage", "blob", "list", "--account-name", acc['name'], "--account-key", acc_key, "-c", container['name'], "--query", "[?ends_with(name, '.vhd') && properties.lease.status=='unlocked']"]))
    for x in blobs_list:
        x['path'] = '/'.join([acc['resourceGroup'], acc['name'], container['name'], x['name']])
    print ('Done checking container %s/%s' % (acc['name'], container['name']))
    queue.put(blobs_list)


def processAcc(queue, acc):
    print ('Getting key for acc %s' % acc['name'])
    acc_key = json.loads(subprocess.check_output(["az", "storage", "account", "keys", "list", "-g", acc['resourceGroup'], "--account-name", acc['name']]))[0]['value']
    print ('Using acc: %s' % acc['name'])
    container_list = json.loads(subprocess.check_output(["az", "storage", "container", "list", "--account-name", acc['name'], "--account-key", acc_key]))
    print ('Getting containers list')
    blobs_list = []
    results = []
    for container in container_list:
        t = Thread(target=processContainer, args=(queue, acc, acc_key, container))
        results.append(t)
        t.start()
    for result in results:
        result.join()

    print ("Done processing acc %s" % acc['name'])


def main():
    print ('Getting accounts list')
    acc_list = json.loads(subprocess.check_output(["az", "storage", "account", "list"]))
    print ('Starting processing')
    #pool = ThreadPool()
    disks_list = []
    q = Queue()
    results = []
    try:
        for acc in acc_list:
            t = Thread(target=processAcc, args=(q, acc))
            results.append(t)
            t.start()

        for result in results:
            result.join()

        while not q.empty():
            blob_list = q.get()
            disks_list.extend(blob_list)
        with open('unmanaged_disks.txt', 'w') as outfile:
            blob_list = disks_list
            blob_list = map( lambda x: flattenjson( x, "." ), json.loads(json.dumps(blob_list)) )
            blob_list = list(blob_list)
            columns = [ x for row in blob_list for x in row.keys() ]
            columns = list( set( columns ) )
            csv_w = csv.writer( outfile )
            csv_w.writerow( columns )

            for i_r in blob_list:
                row = map( lambda x: i_r.get( x, "" ), columns )
                csv_w.writerow( row )

    except subprocess.CalledProcessError as e:
        print(e.output)

if __name__ == "__main__":
    main()
