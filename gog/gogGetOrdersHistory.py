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

with open(args.outputFile, "w", encoding="utf-8") as csvOut:
    csvOut.write(f'Title, PricePaid, PriceBase\n')
    totalOrderCount, totalPricePaid, totalPriceBase = 0, 0, 0
    try:
        for filename in glob.glob(args.inputMask):
            with open(filename, 'r') as f:
                gog = json.loads(f.read())
                orderCount = len(gog['orders'])
                totalOrderCount += orderCount
                print(f'{filename} contains {orderCount} orders, parsing ...')
                for order in gog['orders']:
                    for product in order['products']:
                        title = product['title']
                        pricePaid = product['price']['amount']
                        priceBase = product['price']['baseAmount']
                        totalPricePaid += float(pricePaid)
                        totalPriceBase += float(priceBase)
                        csvOut.write(f'"{title}", {pricePaid}, {priceBase}\n')
    except Exception as e:
        print(f'Error happened on {filename} - {str(e)}')
    print(f'Total {totalOrderCount} orders, paid ${totalPricePaid:.2f} for products worth ${totalPriceBase:.2f}')
    csvOut.close()
