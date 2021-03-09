# Scan Stooq.com database of daily stocks/ETFs prices and calculate winner stocks by certain metrics
# AG @ 2020
import os
import sys
import traceback
import logging
import datetime

logging.basicConfig(filename="debug.log", filemode='a', format='%(asctime)s %(levelname)s %(funcName)s() - %(message)s', level=logging.DEBUG)

leveragedETFs = {"TQQQ", "SSO", "QLD", "FLGE", "FIHD", "NUGT", "FBGX", "FRLG", "UPRO", "FAS", "TECL", "SPXL", "TVIX", "FIYY", "SOXL", "JNUG", "UYG", "TNA", "UWT", "UGAZ", "UVXY", "UCO", "UDOW", "BRZU", "ROM", "LABU", "YINN", "TMF", "MRRL", "DDM",
                 "USLV", "MORL", "UGLD", "FNGU", "ERX", "AGQ", "OILU", "EDC", "UWM", "GUSH", "BIB", "REML", "UGL", "URE", "CURE", "CEFL", "MVV", "CHAU", "DGP", "PFFA", "CEFZ", "BDCL", "EUO", "RXL", "LBDC", "USD", "MLPQ", "UBT", "FNGO", "NAIL",
                 "URTY", "CWEB", "RUSL", "DIG", "INDL", "DRN", "UST", "DFEN", "SMHB", "GASL", "BOIL", "PFFL", "YCS", "UYM", "MIDU", "SMHD", "DVYL", "UPW", "NRGO", "XPP", "PPLC", "BNKO", "FIEE", "HDLB", "BDCY", "DPST", "UBIO", "BNKU", "SAA",
                 "EURL", "UCC", "NRGU", "EET", "LMLB", "TYD", "DVHL", "LMLP", "WTIU", "KORU", "UXI", "HDLV", "FEUL", "UBOT", "SDYL", "UMDD", "MLPZ", "FINU", "UTSL", "JPNL", "DZK", "LBJ", "AMJL", "SPUU", "DRR", "MEXX", "MJO", "PILL", "UGE",
                 "RETL", "FFEU", "WEBL", "PPSC", "CROC", "DTYL", "DTUL", "NEED", "EUFL", "DFVL", "WANT", "ULE", "UBR", "UJB", "EFO", "EZJ", "UPV", "TPOR", "DLBR", "HIBL", "LRET", "TAWK", "HOML", "YCL", "SMLL", "DUSL", "UGBP", "LTL", "FLEU",
                 "DEUR", "UCOM", "XCOM", "UEUR", "DAUD", "PPMC", "UCHF", "PPDM", "DGBP", "UJPY", "PPEM", "DJPY", "DCHF", "UAUD", "URR"}

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
            print(f"#{place+1:<3}: {ticker:<8} - {self.scores.get(ticker, 0):.3f}")

# Metric : portfolio value trend line angle
class MetricPortfolioTrendlineAngle():
    def __init__(self, *args, **kwds):
        self.totalDays = kwds.pop("totalDays", 365) # only consider how stock performed during last N days
        self.origInvestment = kwds.pop("origInvestment", 10000) # USD
        self.showTop = kwds.pop("showTop", 20) # show top N winners
        self.scores, self.numStocks, self.xy, self.x, self.y, self.x2, self.n = {}, {}, {}, {}, {}, {}, {}

    def add(self, ticker, daysAgo, priceClose):
        if ticker not in self.xy and daysAgo >= self.totalDays: # don't count stocks that don't have enough history
            self.xy[ticker] = self.x[ticker] = self.y[ticker] = self.x2[ticker] = self.n[ticker] = 0
        if ticker in self.xy and daysAgo <= self.totalDays: # skip older data
            if ticker == "BRK-A.US": priceClose /= 1000 # workaround to prevent strange results when price is too high (Berkshire Hathaway)
            if ticker not in self.numStocks:
                self.numStocks[ticker] = self.origInvestment / priceClose # initialize portfolio on the first day
            x, y = self.totalDays - daysAgo, self.numStocks[ticker]*priceClose
            self.xy[ticker] += x*y
            self.x[ticker] += x
            self.y[ticker] += y
            self.x2[ticker] += x*x
            self.n[ticker] += 1

    def printResults(self):
        print(f"\n\n** Metric - Portfolio Trend Line Angle **\n")
        print(f"totalDays = {self.totalDays}")
        print(f"origInvestment = {self.origInvestment}\n")
        for ticker in self.xy:
            divisor = self.n[ticker]*self.x2[ticker] - self.x[ticker]*self.x[ticker]
            if divisor != 0:
                self.scores[ticker] = (self.n[ticker]*self.xy[ticker] - self.x[ticker]*self.y[ticker]) / divisor
                logging.debug(f"PortfolioTrendlineAngle {ticker}: {self.scores[ticker]:.3f}, numStocks = {self.numStocks[ticker]:.1f}")
        for place, ticker in zip(range(self.showTop), sorted(self.scores, key=self.scores.get, reverse=True)[:self.showTop]):
            print(f"#{place+1:<3}: {ticker:<8} - {self.scores[ticker]:.3f}")
        if "SPY.US" in self.scores:
            print(f"#BENCHMARK SPY - {self.scores['SPY.US']:<6.3f}")

# Metric : Portfolio Appreciation Stability Peak Adjusted = Growth Ratio * Maximum Experienced Decline Ratio
class MetricPortfolioStabilityPeak():
    def __init__(self, *args, **kwds):
        self.totalDays = kwds.pop("totalDays", 365) # only consider how stock performed during last N days
        self.ignorePriceBelow = kwds.pop("ignorePriceBelow", 5) # don't consider stocks that cost below X on start
        self.showTop = kwds.pop("showTop", 20) # show top N winners
        self.scores, self.start, self.finish, self.localHigh, self.maxLossSoFar = {}, {}, {}, {}, {}

    def add(self, ticker, daysAgo, priceClose):
        if ticker not in self.localHigh and daysAgo >= self.totalDays: # don't count stocks that don't have enough history
            self.localHigh[ticker], self.maxLossSoFar[ticker] = 0, 1
        if ticker in self.localHigh and daysAgo <= self.totalDays: # skip older data
            if ticker not in self.start:
                if priceClose < self.ignorePriceBelow:
                    del self.localHigh[ticker] # stops processing of this ticker
                    return
                else:
                    self.start[ticker] = priceClose # capture first day
            self.finish[ticker] = priceClose # will capture last day
            if self.localHigh[ticker] < priceClose: # update local price maximum if found
                self.localHigh[ticker] = priceClose
            else:
                self.maxLossSoFar[ticker] = min(self.maxLossSoFar[ticker], priceClose / self.localHigh[ticker]) # update maximum encountered loss so far

    def printResults(self):
        print(f"\n\n** Metric - Portfolio Appreciation Stability Peak Adjusted (PASPA) **\n")
        print(f"totalDays = {self.totalDays}")
        print(f"ignorePriceBelow = {self.ignorePriceBelow}\n")
        for ticker in self.start:
            if self.start[ticker] != 0:
                self.scores[ticker] = self.maxLossSoFar[ticker] * self.finish[ticker] / self.start[ticker]
                logging.debug(f"PortfolioStabilityPeak {ticker}: {self.scores[ticker]:.3f}, start = {self.start[ticker]:.2f}, finish = {self.finish[ticker]:.2f}, maxLossSoFar = {self.maxLossSoFar[ticker]:.2f}")
        for place, ticker in zip(range(self.showTop), sorted(self.scores, key=self.scores.get, reverse=True)[:self.showTop]):
            print(f"#{place+1:<3}: {ticker:<8} - {self.scores[ticker]:<6.3f}  = Growth {self.finish[ticker] / self.start[ticker]:<6.3f} * Stability {self.maxLossSoFar[ticker]:.3f}")
        if "SPY.US" in self.scores:
            print(f"#BENCHMARK SPY - {self.scores['SPY.US']:<6.3f}  = Growth {self.finish['SPY.US'] / self.start['SPY.US']:<6.3f} * Stability {self.maxLossSoFar['SPY.US']:.3f}")
            
# Metric : Portfolio Appreciation Stability Total Adjusted = Growth Ratio - Avg Total Declines per Year
class MetricPortfolioStabilityTotal():
    def __init__(self, *args, **kwds):
        self.totalDays = kwds.pop("totalDays", 365) # only consider how stock performed during last N days
        self.ignorePriceBelow = kwds.pop("ignorePriceBelow", 5) # don't consider stocks that cost below X on start
        self.declinesWeight = kwds.pop("declinesWeight", 1) # 0 - declines have no effect, >1 - declines have extra weight
        self.showTop = kwds.pop("showTop", 20) # show top N winners
        self.scores, self.start, self.finish, self.declines, self.prevClose = {}, {}, {}, {}, {}

    def add(self, ticker, daysAgo, priceClose):
        if ticker not in self.declines and daysAgo >= self.totalDays: # don't count stocks that don't have enough history
            self.declines[ticker] = 0
        if ticker in self.declines and daysAgo <= self.totalDays: # skip older data
            if ticker not in self.start:
                if priceClose < self.ignorePriceBelow:
                    del self.declines[ticker] # stops processing of this ticker
                    return
                else:
                    self.start[ticker] = priceClose # capture first day
            self.finish[ticker] = priceClose # will capture last day
            if ticker in self.prevClose:
                if self.prevClose[ticker] > priceClose: # decline detected, add it up
                    self.declines[ticker] += (self.prevClose[ticker] - priceClose) / self.prevClose[ticker]
            self.prevClose[ticker] = priceClose

    def printResults(self):
        print(f"\n\n** Metric - Portfolio Appreciation Stability Total Adjusted (PASTA) **\n")
        print(f"totalDays = {self.totalDays}")
        print(f"ignorePriceBelow = {self.ignorePriceBelow}")
        print(f"declinesWeight = {self.declinesWeight}\n")
        for ticker in self.start:
            if self.start[ticker] != 0:
                self.declines[ticker] *= self.declinesWeight * 365/self.totalDays # trying to decrease effect of declines
                self.scores[ticker] = self.finish[ticker] / self.start[ticker] - self.declines[ticker]
                logging.debug(f"PortfolioStabilityTotal {ticker}: {self.scores[ticker]:.3f}, start = {self.start[ticker]:.2f}, finish = {self.finish[ticker]:.2f}, yearly.declines = {self.declines[ticker]:.2f}")
        for place, ticker in zip(range(self.showTop), sorted(self.scores, key=self.scores.get, reverse=True)[:self.showTop]):
            print(f"#{place+1:<3}: {ticker:<8} - {self.scores[ticker]:<6.3f}  = Growth {self.finish[ticker] / self.start[ticker]:<6.3f} - YearlyDeclines {self.declines[ticker]:.3f}")
        if "SPY.US" in self.scores:
            print(f"#BENCHMARK SPY - {self.scores['SPY.US']:<6.3f}  = Growth {self.finish['SPY.US'] / self.start['SPY.US']:<6.3f} - YearlyDeclines {self.declines['SPY.US']:.3f}")

# Metric : largest difference between two trading(!) dates (startDate - endDate), used to find cheap stocks
class MetricLargestDiffBetween():
    def __init__(self, *args, **kwds):
        self.startDate = kwds.pop("startDate", datetime.date.today()) # if startDate is before endDate then look for drops, otherwise for rises
        self.endDate = kwds.pop("endDate", datetime.date.today())     #
        self.grewLongerThanDays = kwds.pop("grewLongerThanDays", None)   # exclude stocks that didn't grow N days before the drop/rise happened
        self.grewMoreThanPercent = kwds.pop("grewMoreThanPercent", 1) # exclude stocks that didn't grow at least X% during those N days
        self.ignorePriceBelow = kwds.pop("ignorePriceBelow", 10) # exclude stocks that cost below X
        self.ignoreLeveragedETFs = kwds.pop("ignoreLeveragedETFs", True) # exclude leveraged ETFs
        self.showTop = kwds.pop("showTop", 20) # show top N winners
        self.minDate = min(self.startDate, self.endDate)
        self.grewCoeff = 1.0 + self.grewMoreThanPercent/100
        self.nDaysBackFromStart = self.minDate + datetime.timedelta(days = -self.grewLongerThanDays) if self.grewLongerThanDays else None
        self.scores, self.start, self.end, self.priceNDaysBack = {}, {}, {}, {}

    def add(self, ticker, date, priceClose):
        if self.nDaysBackFromStart and date <= self.nDaysBackFromStart:
            self.priceNDaysBack[ticker] = priceClose
        elif date == self.startDate:
            self.start[ticker] = priceClose
        elif date == self.endDate:
            self.end[ticker] = priceClose

    def printResults(self):
        print(f"\n\n** Metric - Largest % Difference Between Two Dates **\n")
        print(f"startDate = {self.startDate}")
        print(f"endDate = {self.endDate}")
        print(f"grewLongerThanDays = {self.grewLongerThanDays}")
        print(f"grewMoreThanPercent = {self.grewMoreThanPercent}")
        print(f"ignoreLeveragedETFs = {self.ignoreLeveragedETFs}")
        print(f"ignorePriceBelow = {self.ignorePriceBelow}\n")
        drops = (self.startDate < self.endDate)
        for ticker in self.start:
            if ticker in self.end and (ticker == "SPY.US" or \
            self.start[ticker] >= self.ignorePriceBelow and \
            self.end[ticker] >= self.ignorePriceBelow and \
            (self.ignoreLeveragedETFs == False or ticker.split('.')[0] not in leveragedETFs) and \
            (self.nDaysBackFromStart == None or (self.start[ticker] if drops else self.end[ticker])/self.priceNDaysBack.get(ticker, sys.maxsize) >= self.grewCoeff)):
                self.scores[ticker] = 100*(self.start[ticker] / self.end[ticker] - 1)
                logging.debug(f"LargestDiffBetween {ticker}: {self.scores[ticker]:.3f}, start = {self.start[ticker]:.2f}, end = {self.end[ticker]:.2f}, priceNDaysBack = {self.priceNDaysBack.get(ticker, -1)}")
        for place, ticker in zip(range(self.showTop), sorted(self.scores, key=self.scores.get, reverse=True)[:self.showTop]):
            print(f"#{place+1:<3}: {ticker:<8} - {self.scores[ticker]:<6.3f}  = {self.start[ticker]:<6.3f} > {self.end[ticker]:<6.3f}")
        if "SPY.US" in self.scores:
            print(f"#BENCHMARK SPY - {self.scores['SPY.US']:<6.3f}  = {self.start['SPY.US']:<6.3f} > {self.end['SPY.US']:<6.3f}")
            
# MAIN
if len(sys.argv) < 2:
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
metric1 = MetricRecentPeakRatio(totalDays = 5*365, peakedPastDays = 1, showTop = 20)
metric2 = MetricPortfolioTrendlineAngle(totalDays = 5*365, origInvestment = 10000, showTop = 20)
metric3 = MetricPortfolioStabilityPeak(totalDays = 13*365, ignorePriceBelow = 5, showTop = 20)
metric4 = MetricPortfolioStabilityTotal(totalDays = 13*365, ignorePriceBelow = 5, declinesWeight = 5, showTop = 20)
metric5 = MetricLargestDiffBetween(startDate = datetime.date(2020, 2, 19), \
                                   endDate = datetime.date(2020, 6, 8), \
                                   grewLongerThanDays = 1*365, \
                                   grewMoreThanPercent = 20, \
                                   ignoreLeveragedETFs = True, \
                                   ignorePriceBelow = 15, \
                                   showTop = 40)

# Determine total amount of files and database end date
for path, subdirs, files in os.walk(folderIn):
    totalFiles += len(files)
    for file in files:
        if not endDate:
            # Read contents of file with prices
            with open(path + "\\" + file, "r") as fileIn:
                for line in fileIn:
                    if line[0] == '<': continue # skip the header that starts with "<TICKER>"
                    sdate = line.split(",")[2]
                    endDate = datetime.date(int(sdate[:4]), int(sdate[4:6]), int(sdate[6:8])) # fast date parser

print(f"\nStocks/ETFs in the database: {totalFiles}")
if endDate: print(f"Detected End Date: {endDate:%Y-%m-%d}\n")

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
                    if line[0] == '<': continue # skip the header that starts with "<TICKER>"
                    (ticker,period,sdate,stime,sopen,shigh,slow,sclose,svolume,sopenint) = line.split(",") # parsing the day line
                    processedDays += 1
                    
                    date = datetime.date(int(sdate[:4]), int(sdate[4:6]), int(sdate[6:8])) # fast date parser
                    daysAgo = (endDate - date).days
                    priceClose = float(sclose)
                    
                    metric1.add(ticker, daysAgo, priceClose)
                    #metric2.add(ticker, daysAgo, priceClose)
                    #metric3.add(ticker, daysAgo, priceClose)
                    #metric4.add(ticker, daysAgo, priceClose)
                    #metric5.add(ticker, date, priceClose)

        except KeyboardInterrupt: raise
        except: print(f"Exception when processing {ticker}: {traceback.format_exc()}")

metric1.printResults()
metric2.printResults()
metric3.printResults()
metric4.printResults()
metric5.printResults()
timeElapsed = datetime.datetime.now() - procStart
print(f"\nTotal days processed: {processedDays}")
print(f"Time Elapsed: {timeElapsed.total_seconds():.2f} sec")
