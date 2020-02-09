# Scan Stooq.com database of daily stocks/ETFs prices and calculate winner stocks by certain metrics
# AG @ 2020
import os
import sys
import traceback
import logging
import datetime

logging.basicConfig(filename="debug.log", filemode='a', format='%(asctime)s %(levelname)s %(funcName)s() - %(message)s', level=logging.DEBUG)

# Metric : ratio of recent maximum to previous maximum
class MetricRecentPeakRatio():
    def __init__(self, *args, **kwds):
        self.totalDays = kwds.pop("totalDays", 365) # only consider how stock performed during last N days
        self.peakedPastDays = kwds.pop("peakedPastDays", 10) # recent maximum time window in days
        self.showTop = kwds.pop("showTop", 20) # show top N winners
        self.scores, self.pastMax, self.recentMax = {}, {}, {}

    def add(self, ticker, daysAgo, priceClose):
        if ticker not in self.pastMax:
            self.pastMax[ticker] = self.recentMax[ticker] = 0
        if daysAgo <= self.totalDays: # skip older data
            if daysAgo > self.peakedPastDays:
                self.pastMax[ticker] = max(self.pastMax[ticker], priceClose)
            else:
                self.recentMax[ticker] = max(self.recentMax[ticker], priceClose)

    def printResults(self):
        print(f"\n\n** Metric - Recent Peak Ratio **\n")
        print(f"totalDays = {self.totalDays}")
        print(f"peakedPastDays = {self.peakedPastDays}\n")
        for ticker in self.recentMax:
            if self.pastMax[ticker] > 0:
                self.scores[ticker] = self.recentMax[ticker] / self.pastMax[ticker]
                logging.debug(f"RecentPeakRatio {ticker}: {self.recentMax[ticker]:.3f} / {self.pastMax[ticker]:.3f} = {self.scores[ticker]:.3f}")
        for place, ticker in zip(range(self.showTop), sorted(self.scores, key=self.scores.get, reverse=True)[:self.showTop]):
            print(f"#{place+1}: {ticker} - {self.scores.get(ticker, 0):.3f}")

# Metric : trend line angle
class MetricTrendlineAngle():
    def __init__(self, *args, **kwds):
        self.totalDays = kwds.pop("totalDays", 365) # only consider how stock performed during last N days
        self.showTop = kwds.pop("showTop", 20) # show top N winners
        self.scores, self.beta, self.xy, self.x, self.y, self.x2, self.n = {}, {}, {}, {}, {}, {}, {}

    def add(self, ticker, daysAgo, priceClose):
        if ticker not in self.xy:# and daysAgo >= self.totalDays: # don't count stocks that don't have enough history
            self.xy[ticker] = self.x[ticker] = self.y[ticker] = self.x2[ticker] = self.n[ticker] = 0
        if ticker in self.xy and daysAgo <= self.totalDays: # skip older data
            x, y = -daysAgo, priceClose
            self.xy[ticker] += x*y
            self.x[ticker] += x
            self.y[ticker] += y
            self.x2[ticker] += x*x
            self.n[ticker] += 1

    def printResults(self):
        print(f"\n\n** Metric - Trend Line Angle **\n")
        print(f"totalDays = {self.totalDays}\n")
        for ticker in self.xy:
            divisor = self.n[ticker]*self.x2[ticker] - self.x[ticker]*self.x[ticker]
            if divisor != 0:
                self.scores[ticker] = (self.n[ticker]*self.xy[ticker] - self.x[ticker]*self.y[ticker]) / divisor
                self.beta[ticker] = (self.y[ticker] - self.scores[ticker]*self.x[ticker]) / self.n[ticker]
                logging.debug(f"TrendlineAngle {ticker}: {self.scores[ticker]:.3f} x = {self.x[ticker]} y = {self.y[ticker]} beta = {self.beta[ticker]:.3f}")
        for place, ticker in zip(range(self.showTop), sorted(self.scores, key=self.scores.get, reverse=True)[:self.showTop]):
            print(f"#{place+1}: {ticker} - {self.scores[ticker]:.3f} - baseline: {self.beta[ticker]:.1f}")

# MAIN
if len(sys.argv) < 1:
    print("\nUsage: " + os.path.basename(sys.argv[0]) + " <InputFolder>\n")
    print("Example: " + os.path.basename(sys.argv[0]) + " daily")
    exit()

# Variables
fileCounter = 0
totalFiles = 0
processedDays = 0
endDate = None
folderIn = sys.argv[1]
procStart = datetime.datetime.now()

# Metrics
metric1 = MetricRecentPeakRatio(totalDays = 365, peakedPastDays = 10, showTop = 20)
metric2 = MetricTrendlineAngle(totalDays = 5*365, showTop = 20)
metric2.add("AA", 2, 3)
metric2.add("AA", 1, 5)
metric2.add("AA", 0, 6.5)
metric2.printResults()
exit()

# Determine total amount of files and database end date
for path, subdirs, files in os.walk(folderIn):
    totalFiles += len(files)
    for file in files:
        if not endDate:
            # Read contents of file with prices
            with open(path + "\\" + file, "r") as fileIn:
                for line in fileIn:
                    if line[0] == 'D': continue # skip the header that starts with "Date"
                    sdate = line.split(",")[0]
                    endDate = datetime.date(int(sdate[:4]), int(sdate[4:6]), int(sdate[6:8])) # fast date parser

print(f"\nStocks/ETFs in the database: {totalFiles}")
print(f"Detected End Date: {endDate:%Y-%m-%d}\n")

# Walk through Stooq database folder structure
for path, subdirs, files in os.walk(folderIn):
    # Every file is a stock or ETF
    for file in files:
        fileCounter += 1
        sys.stdout.write('\rProcessing #' + str(fileCounter) + ' - ' + str(int(100*fileCounter/totalFiles)) + '% ...')
        (name, ext) = os.path.splitext(file) # extract stock name/ticker
        ticker = name.upper()
        try:
            # Read contents of file with prices
            with open(path + "\\" + file, "r") as fileIn:
                for line in fileIn:
                    if line[0] == 'D': continue # skip the header that starts with "Date"
                    (sdate,sopen,shigh,slow,sclose,svolume,sopenint) = line.split(",") # parsing the day line
                    processedDays += 1
                    
                    date = datetime.date(int(sdate[:4]), int(sdate[4:6]), int(sdate[6:8])) # fast date parser
                    daysAgo = (endDate - date).days
                    priceClose = float(sclose)
                    
                    if ticker == "BRK-A.US": priceClose /= 1000 # workaround to prevent strange results when price is too high (Berkshire Hathaway)
                    
                    metric1.add(ticker, daysAgo, priceClose)
                    metric2.add(ticker, daysAgo, priceClose)

        except KeyboardInterrupt: raise
        except: print(f"Exception when processing {ticker}: {traceback.format_exc()}")

metric1.printResults()
metric2.printResults()
timeElapsed = datetime.datetime.now() - procStart
print(f"\nTotal days processed: {processedDays}")
print(f"Time Elapsed: {timeElapsed.total_seconds():.2f} sec")
