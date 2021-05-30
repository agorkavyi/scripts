#!/usr/bin/env python
# Parse JSON order history from GOG.com with titles and prices and save it to .csv
# AG @ 2021
#
# TODO: implement GOG login and download
#
import argparse
import glob
import json

parser = argparse.ArgumentParser(description='<< Parse GOG.com orders history >> v1.0\n\n' +
    'To use login to GOG first and download all JSONs of completed orders using URL with page numbers 1-N:\n'
    '  https://www.gog.com/account/settings/orders/data?canceled=0&completed=1&in_progress=0&not_redeemed=0&pending=0&redeemed=0&page=1',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('inputMask', help='mask of JSON input files, for example \'data*.json\'')
parser.add_argument('outputFile', help='name of CSV output file, for example \'gogOrders.csv\'')
args = parser.parse_args()

try:
    for filename in glob.glob(args.inputMask):
        with open(filename, 'r') as f:
            gog = json.loads(f.read())
            orderCount = len(gog['orders'])
            print(f'{filename} contains {orderCount} orders, parsing ...')
except Exception as e:
    print(f'Error happened on {filename} - {str(e)}')

'''try:
    page = 1
    while True:
        req = urllib.request.Request(getOrdersURL % page)
        resp = urllib.request.urlopen(req)
        respData = resp.read().decode('utf-8')
        print(getOrdersURL % page)
        if 'html' in respData[:25]: # if it looks like HTML page
            print('Please login to GOG.com first ...')
            time.sleep(2)
            webbrowser.open(resp.geturl())
            break
        print(respData)
        resp.close()
        break
except Exception as e:
    print('Error happened ' + str(e))'''