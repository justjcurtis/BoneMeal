import requests
from pathlib import Path
import numpy as np
import csv
import time
from pip._internal import main as pip
try:
    import yfinance as yf
except:
    pip(['install', '--user', 'yfinance'])
finally:
    import yfinance as yf

sheetName = 'FreeTradeStockUniverse.csv'
mainStore = 'DataStore.csv'
StockListURL = 'http://freetrade.io/stock-universe'
sheetUrl = 'https://docs.google.com/spreadsheets/d/1-5eYQWyWLyRCiqgHpiqjSmCayLjODvDvVEHWRjW5VjM/export?format=csv&id=1-5eYQWyWLyRCiqgHpiqjSmCayLjODvDvVEHWRjW5VjM'
sheetData = ''
DividendStockListStored = []
rejectedStockList = []

class Stock:
    def __init__(self, name, shortDescription, ticker, assetClass, currency, isin, longDescription, dYield=None, dGrowthRate=None, peRatio=None):
        self.name = name
        self.shortDescription = shortDescription
        self.ticker = ticker
        self.assetClass = assetClass
        self.currency = currency
        self.isin = isin
        self.longDescription = longDescription
        self.dYield = dYield
        self.dGrowthRate = dGrowthRate
        self.peRatio = peRatio
        try:
            self.yfData = yf.Ticker(ticker)
        except:
            self.yfData = 0


def getSheet():
    response = requests.get(sheetUrl)
    assert response.status_code == 200, 'Wrong status code'
    return response.content.decode("utf-8")


def saveCsv(content, name):
    sheetHandle = open(name, 'w')
    sheetHandle.write(content)
    sheetHandle.close()


def sheetToStockList(fileName):
    StockList = []
    with open(fileName, 'r') as sheet:
        reader = csv.reader(sheet)
        dumbList = list(reader)
        for row in dumbList:
            if(row[0] == "Name"):
                continue
            StockList.append(Stock(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
    return StockList


def outputSheetToStockList(fileName):
    StockList = []
    with open(fileName, 'r') as sheet:
        reader = csv.reader(sheet)
        dumbList = list(reader)
        for row in dumbList:
            if(row[0] == "Name"):
                continue
            StockList.append(Stock(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))
    return StockList


def dividendGrowthRate(stock):
    divs = stock.yfData.dividends.values
    growth_rate = np.mean(np.exp(np.diff(np.log(divs))) - 1)
    return growth_rate


def init():
    global sheetData
    global DividendStockListStored
    try:
        _ = open(sheetName, 'r')
    except:
        sheet = getSheet()
        saveCsv(sheet, sheetName)
    finally:
        sheetHandle = open(sheetName, 'r')
        sheetData = sheetHandle.read()
        sheetHandle.close()

    try:
        _ = open(mainStore, 'r')
    except:
        stockList = sheetToStockList(sheetName)
        dStockList = dividendStockList(stockList)
        writeOuputCsv(dStockList, mainStore)
    finally:
        DividendStockListStored = outputSheetToStockList(mainStore)


def getYDGPEforStock(stock):
    dYield = 0
    dGrowthRate = 0
    peRatio = 0
    ticker = stock.ticker
    try:
        dYield = stock.yfData.info['trailingAnnualDividendYield']
    except:
        if(stock.currency=='GBP'):
            ticker = stock.ticker+'.L'
            stock.yfData = yf.Ticker(stock.ticker+'.L')
            try:
                dYield = stock.yfData.info['trailingAnnualDividendYield']
            except:
                return 'skip'
        else:
            return 'skip'

    try:
        dGrowthRate = dividendGrowthRate(stock)
    except:
        return 'skip'

    try:
        peRatio = stock.yfData.info['trailingPE']
    except:
        peRatio = '?'

    return {'dYield': dYield, 'dGrowthRate': dGrowthRate, 'peRatio': peRatio, 'ticker': ticker}


def dividendStockList(stockList):
    dStockList = []
    i = 0
    for stock in stockList:
        print(str(round((i/len(stockList))*100, 2)) + "% Complete")
        i += 1
        data = getYDGPEforStock(stock)
        if(data == 'skip'):
            rejectedStockList.append(stock)
        else:
            stock.dYield = data['dYield']
            stock.dGrowthRate = data['dGrowthRate']
            stock.peRatio = data['peRatio']
            stock.ticker = data['ticker']
            dStockList.append(stock)
    writeOuputCsv(rejectedStockList, 'rejected.csv')
    print("100% Complete")
    return dStockList


def stockToList(stock):
    return [stock.name, stock.shortDescription, stock.ticker, stock.assetClass, stock.currency, stock.isin, stock.longDescription, stock.dYield, stock.dGrowthRate, stock.peRatio]


def stockListToCsvList(stockList):
    csvList = []
    header = ["Name", "Short Description", "Ticker", "Asset Class", "Currency", "ISIN", "Long Description", "Yield", "Growth Rate", "PE Ratio"]
    csvList.append(header)
    for stock in stockList:
        csvList.append(stockToList(stock))
    return csvList


def writeOuputCsv(stockList, filename):
    csvList = stockListToCsvList(stockList)
    with open(filename, 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        for row in csvList:
            wr.writerow(row)


def indexOfStock(stockList, isin):
    i = 0
    for stock in stockList:
        if(stock.isin == isin):
            return i
        i += 1
    return -1


def filterStocklist(stockList, dYield=0.01, dGrowthRate=0, peRatio=None):
    filterList = []
    for stock in stockList:
        try:
            if not (dYield is None):
                if(float(stock.dYield) >= float(dYield)):
                    if not (dGrowthRate is None):
                        if(float(stock.dGrowthRate) >= float(dGrowthRate)):
                            if not (peRatio is None):
                                if(float(stock.peRatio) <= float(peRatio)):
                                    filterList.append(stock)
                            else:
                                filterList.append(stock)
                    else:
                        if not (peRatio is None):
                            if(float(stock.peRatio) <= float(peRatio)):
                                filterList.append(stock)
                        else:
                            filterList.append(stock)
            else:
                if not (dGrowthRate is None):
                    if(float(stock.dGrowthRate) >= float(dGrowthRate)):
                        if not (peRatio is None):
                            if(float(stock.peRatio) <= float(peRatio)):
                                filterList.append(stock)
                        else:
                            filterList.append(stock)
                else:
                    if not (peRatio is None):
                        if(float(stock.peRatio) <= float(peRatio)):
                            filterList.append(stock)
                    else:
                        filterList.append(stock)
        except:
            pass

    return filterList


def creamList():
    return filterStocklist(DividendStockListStored, dYield=0.03, dGrowthRate=0.04, peRatio=25)


def highYield():
    return filterStocklist(DividendStockListStored, dYield=0.05)


def highYieldGrowth():
    return filterStocklist(DividendStockListStored, dYield=0.05, dGrowthRate=0.04, peRatio=25)


def dGrowthList():
    return filterStocklist(DividendStockListStored, dYield=0.024, dGrowthRate=0.035, peRatio=40)


def CustomSearch():
    print("Enter custom filter options")
    print("Leave blank to ignore option")
    dYield = input("Dividend Yield >= : ")
    if(dYield == ""):
        dYield = None
    dGrowthRate = input("Dividend Growth Rate >= : ")
    if(dGrowthRate == ""):
        dGrowthRate = None
    peRatio = input("PE Ratio >= : ")
    if(peRatio == ""):
        peRatio = None
    name = input("Name for output file : ")
    if(name == ""):
        name = round(time.time())
    name = str(name)+".csv"
    writeOuputCsv(filterStocklist(DividendStockListStored, dYield=dYield, dGrowthRate=dGrowthRate, peRatio=peRatio), name)
    

def main():
    init()
    writeOuputCsv(creamList(), "cream.csv")
    writeOuputCsv(highYield(), 'highYield.csv')
    writeOuputCsv(highYieldGrowth(), 'highYieldGrowth.csv')
    writeOuputCsv(dGrowthList(), 'dGrowthList.csv')

    while True:
        try:
            CustomSearch()
        except Exception as ex:
            print(ex)


main()
