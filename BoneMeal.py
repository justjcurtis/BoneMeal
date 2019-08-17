import requests
import subprocess
from pathlib import Path
import os
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

try:
    from tabulate import tabulate
except:
    pip(['install', '--user', 'tabulate'])
finally:
    from tabulate import tabulate

try:
    from progressbar import ProgressBar
except:
    pip(['install', '--user', 'progressbar'])
finally:
    from progressbar import ProgressBar, AdaptiveETA, Bar, Percentage
DataStore = "DataStore"
OutputStore = "Output"
sheetName = os.path.join(DataStore, 'FreeTradeStockUniverse.csv')
mainStore = os.path.join(DataStore, 'DataStore.csv')
rejectStore = os.path.join(DataStore, "rejected.csv")
listStore = os.path.join(DataStore, "listStore.csv")
StockListURL = 'http://freetrade.io/stock-universe'
sheetUrl = 'https://docs.google.com/spreadsheets/d/1-5eYQWyWLyRCiqgHpiqjSmCayLjODvDvVEHWRjW5VjM/export?format=csv&id=1-5eYQWyWLyRCiqgHpiqjSmCayLjODvDvVEHWRjW5VjM'
sheetData = ''
listData = []
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


class FilterType:
    def __init__(self, name, dYield=None, dGrowthRate=None, peRatio=None):
        self.name = name
        self.dYield = dYield
        self.dGrowthRate = dGrowthRate
        self.peRatio = peRatio
        self.outputName = name + ".csv"


defaultListData = [
    FilterType("cream", 0.03, 0.04, 25),
    FilterType("highYield", 0.05, None, None),
    FilterType("highYieldGrowth", 0.05, 0.04, 25),
    FilterType("dividendGrowth", 0.024, 0.035, 40)
]

clear = lambda: subprocess.call('cls||clear', shell=True)

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
    if(len(divs) < 2):
        return 'skip'
    growth_rate = np.mean(np.exp(np.diff(np.log(divs))) - 1)
    return growth_rate


def init():
    global sheetData
    global DividendStockListStored
    global rejectedStockList
    clear()
    print("Initialising BoneMeal...")
    if not (Path.exists(Path(DataStore))):
        os.mkdir(DataStore)
    if not (Path.exists(Path(OutputStore))):
        os.mkdir(OutputStore)
    try:
        with open(sheetName, 'r') as sheetCurrentHandle:
            print("Checking for updates to Freetrade Stock Universe...")
            try:
                sheetCurrent = sheetCurrentHandle.read().replace('\r\n', '\n')
                sheet = getSheet().replace('\r\n', '\n')
                if not (sheetCurrent == sheet):
                    print("Update found!")
                    print("Applying update..")
                    saveCsv(sheet, sheetName)
                    if(Path.exists(Path(mainStore))):
                        os.remove(mainStore)
                    print("Update applied!")
            except:
                print("Couldn't get new sheet, skipping update")
    except:
        print("FreeTrade Stock Uninverse not found")
        print("getting it...")
        sheet = getSheet()
        saveCsv(sheet, sheetName)
        if(Path.exists(Path(mainStore))):
            os.remove(mainStore)
    finally:
        print("Got FreeTrade Stock Universe!")
        sheetHandle = open(sheetName, 'r')
        sheetData = sheetHandle.read()
        sheetHandle.close()


    try:
        _ = open(mainStore, 'r')
        _ = open(rejectStore, "r")
    except:
        if(Path.exists(Path(mainStore))):
            os.remove(mainStore)
        if(Path.exists(Path(rejectStore))):
            os.remove(rejectStore)
        print("Dividend data for stocks not found")
        print("getting it...")
        stockList = sheetToStockList(sheetName)
        dividendStockList(stockList)
    finally:
        print("Got dividend data for stocks!")
        DividendStockListStored = outputSheetToStockList(mainStore)
        rejectedStockList = outputSheetToStockList(rejectStore)

    print("Initialisation complete!")


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
        if(dGrowthRate == 'skip'):
            return 'skip'
    except:
        return 'skip'

    try:
        peRatio = stock.yfData.info['trailingPE']
    except:
        peRatio = '?'

    return {'dYield': dYield, 'dGrowthRate': dGrowthRate, 'peRatio': peRatio, 'ticker': ticker}


def dividendStockList(stockList):
    widgets = [Percentage(),
                ' ', Bar(),
                ' ', AdaptiveETA()]
    pBar = ProgressBar(widgets=widgets)
    dStockList = []
    print("populating stocks with dividend data..")
    rejectedStockList = []
    for stock in pBar(stockList):
        data = getYDGPEforStock(stock)
        if(data == 'skip'):
            rejectedStockList.append(stock)
        else:
            stock.dYield = data['dYield']
            stock.dGrowthRate = data['dGrowthRate']
            stock.peRatio = data['peRatio']
            stock.ticker = data['ticker']
            dStockList.append(stock)
    writeOuputCsv(dStockList, mainStore, isDataStore=True)
    writeOuputCsv(rejectedStockList, rejectStore, isDataStore=True)
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


def writeOuputCsv(stockList, filename, isDataStore=False):
    csvList = stockListToCsvList(stockList)
    if(isDataStore):
        outPath = filename
    else:
        outPath = os.path.join(OutputStore, filename)
    with open(outPath, 'w', newline='') as myfile:
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
    try:
        dYield = float(dYield)
    except:
        dYield = None
    try:
        dGrowthRate = float(dGrowthRate)
    except:
        dGrowthRate = None
    try:
        peRatio = float(peRatio)
    except:
        peRatio = None

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

def CustomSearch():
    print("Enter custom filter options")
    print("Leave blank to ignore option")
    dYield = input("Dividend Yield >= : ")
    if(dYield == ""):
        dYield = None
    dGrowthRate = input("Dividend Growth Rate >= : ")
    if(dGrowthRate == ""):
        dGrowthRate = None
    peRatio = input("PE Ratio <= : ")
    if(peRatio == ""):
        peRatio = None
    name = input("Name for output file : ")
    if(name == ""):
        name = round(time.time())
    name = str(name)+".csv"
    writeOuputCsv(filterStocklist(DividendStockListStored, dYield=dYield, dGrowthRate=dGrowthRate, peRatio=peRatio), name)


def fullRefresh():
    if(Path.exists(Path(sheetName))):
        os.remove(sheetName)
    try:
        init()
    except:
        pass



def produceLists(filterList):
    for f in filterList:
        out = filterStocklist(DividendStockListStored, dYield=f.dYield, dGrowthRate=f.dGrowthRate, peRatio=f.peRatio)
        writeOuputCsv(out, f.outputName)


def saveListData():
    global listData
    csvData = []
    for f in listData:
        csvData.append([f.name, f.dYield, f.dGrowthRate, f.peRatio])

    with open(listStore, 'w', newline='') as lsHandle:
        wr = csv.writer(lsHandle, quoting=csv.QUOTE_ALL)
        for row in csvData:
            wr.writerow(row)


def addFilter():
    global listData
    getting = True
    while getting:
        print("please enter a name for the new filter")
        print("type cancel to cancel")
        name = input("> ")
        if(name == "cancel"):
            return
        if(len(name)>0):
            getting = False
        else:
            print("you must enter a name for a new filter")
            input("press enter to re enter name")


    getting = True
    while getting:
        print("please enter the dividend yield for the new filter")
        print("leave this blank to ignore this filter")
        dYield = input("> ")
        if not (dYield == ""):
            try:
                dYield = float(dYield)
                if(dYield >= 1 or dYield <= 0):
                    print("dividend yield must be a valid decimal between 0 and 1")
                    input("press enter to re enter dividend yield")
                else:
                    getting = False
            except:
                print("dividend yield must be a valid decimal between 0 and 1")
                input("press enter to re enter dividend yield")
        else:
            dYield = None
            getting = False

    getting = True
    while getting:
        print("please enter the dividend growth rate for the new filter")
        print("leave this blank to ignore this filter")
        dGrowthRate = input("> ")
        if not (dGrowthRate == ""):
            try:
                dGrowthRate = float(dGrowthRate)
                if(dGrowthRate >= 1 or dGrowthRate <= 0):
                    print("dividend growth rate must be a valid decimal between 0 and 1")
                    input("press enter to re enter dividend growth rate")
                else:
                    getting = False
            except:
                print("dividend growth rate must be a valid decimal between 0 and 1")
                input("press enter to re enter dividend growth rate")
        else:
            dGrowthRate = None
            getting = False

    getting = True
    while getting:
        print("please enter the PE ratio for the new filter")
        print("leave this blank to ignore this filter")
        peRatio = input("> ")
        if not (peRatio == ""):
            try:
                peRatio = float(peRatio)
                if(peRatio <= 0 or peRatio >= 100):
                    print("PE ratio must be a valid decimal greater than 0 and less than 100")
                    input("press enter to re enter PE ratio")
                else:
                    getting = False
            except:
                print("PE ratio must be a valid decimal greater than 0 and less than 100")
                input("press enter to re enter PE ratio")
        else:
            peRatio = None
            getting = False

    newFilter = FilterType(name, dYield=dYield, dGrowthRate=dGrowthRate, peRatio=peRatio)
    listData.append(newFilter)
    saveListData()

def editFilter():
    global listData
    getting = True
    while getting:
        print("please enter the name of the filter you want to edit")
        print("leave blank to cancel")
        name = input("> ")
        i = 0
        if(len(name)>0):
            for f in listData:
                if(name == f.name):
                    break
                else:
                    i += 1
            if(name == listData[i].name):
                gettingg = True
                while gettingg:
                    print("please enter a new name for " + name)
                    newName = input("> ")
                    if(len(newName)>0):
                        gettingg = False
                    else:
                        print("you must enter a new name for " + name)
                        input("press enter to re enter name")

                gettingg = True
                while gettingg:
                    print("please enter a new dividend yield for " + newName)
                    print("leave this blank to ignore this filter")
                    dYield = input("> ")
                    if not (dYield == ""):
                        try:
                            dYield = float(dYield)
                            if(dYield >= 1 or dYield <= 0):
                                print("dividend yield must be a valid decimal between 0 and 1")
                                input("press enter to re enter dividend yield")
                            else:
                                gettingg = False
                        except:
                            print("dividend yield must be a valid decimal between 0 and 1")
                            input("press enter to re enter dividend yield")
                    else:
                        dYield = None
                        gettingg = False

                gettingg = True
                while gettingg:
                    print("please enter a dividend growth rate for " + newName)
                    print("leave this blank to ignore this filter")
                    dGrowthRate = input("> ")
                    if not (dGrowthRate == ""):
                        try:
                            dGrowthRate = float(dGrowthRate)
                            if(dGrowthRate >= 1 or dGrowthRate <= 0):
                                print("dividend growth rate must be a valid decimal between 0 and 1")
                                input("press enter to re enter dividend growth rate")
                            else:
                                gettingg = False
                        except:
                            print("dividend growth rate must be a valid decimal between 0 and 1")
                            input("press enter to re enter dividend growth rate")
                    else:
                        dGrowthRate = None
                        gettingg = False

                gettingg = True
                while gettingg:
                    print("please enter a new PE ratio for " + newName)
                    print("leave this blank to ignore this filter")
                    peRatio = input("> ")
                    if not (peRatio == ""):
                        try:
                            peRatio = float(peRatio)
                            if(peRatio <= 0 or peRatio >= 100):
                                print("PE ratio must be a valid decimal greater than 0 and less than 100")
                                input("press enter to re enter PE ratio")
                            else:
                                gettingg = False
                        except:
                            print("PE ratio must be a valid decimal greater than 0 and less than 100")
                            input("press enter to re enter PE ratio")
                    else:
                        peRatio = None
                        gettingg = False
                listData[i].name = newName
                listData[i].dYield = dYield
                listData[i].dGrowthRate = dGrowthRate
                listData[i].peRatio = peRatio
                getting = False
            else:
                print("you must enter a name of a filter to edit")
                input("press enter to re enter name")
        else:
            return
    saveListData()


def removeFilter():
    global listData
    getting = True
    while getting:
        print("please enter the name of the filter you want to edit")
        print("leave blank to cancel")
        name = input("> ")
        i = 0
        if(len(name)>0):
            for f in listData:
                if(name == f.name):
                    break
                else:
                    i += 1
            if(name == listData[i].name):
                del listData[i]
                getting = False
            else:
                print("you must enter a name of a filter to remove")
                input("press enter to re enter name")
        else:
            return
    saveListData()


def clearFilters():
    global listData
    listData = []
    saveListData()


def loadFilterList():
    global listData
    listData = []
    if not (Path.exists(Path(listStore))):
        f = open(listStore, 'w')
        f.close()
    with open(listStore, 'r') as ls:
        reader = csv.reader(ls)
        filterList = list(reader)
        for row in filterList:
            listData.append(FilterType(row[0], row[1], row[2], row[3]))
    return listData


def editLists():
    table = [
        ["Select option below"],
        ["s - Show list of custom filters"],
        ["a - Add a new filter to the list"],
        ["e - Edit a filter in the list"],
        ["r - Remove a filter from the list"],
        ["clear - Clear entire filter list"],
        ["x - Exit"]
        ]
    getting = True
    while getting:
        loadFilterList()
        clear()
        print(tabulate(table, headers="firstrow", tablefmt="rst"))
        command = input("> ")
        try:
            command = str.lower(command)
            if(command == "x"):
                clear()
                return
            elif(command == "s"):
                filterList = [
                    ["Name", "Yield", "Growth Rate", "PE Ratio"]
                ]
                for f in listData:
                    filterList.append([f.name, f.dYield, f.dGrowthRate, f.peRatio])

                print(tabulate(filterList, headers="firstrow", tablefmt="rst"))
                input("press enter to reload menu")
                clear()
                continue
            elif(command == "a"):
                addFilter()
            elif(command == "e"):
                editFilter()
            elif(command == "r"):
                removeFilter()
            elif(command == "clear"):
                clearFilters()
            else:
                print("please enter a valid command.")
                input("press enter to reload menu")
                clear()
                continue
        except:
            print("please enter a valid command.")
            input("press enter to reload menu")
            clear()
            continue


def Menu():
    table = [
    ["Select option below"],
    ["1 - Refresh data"],
    ["2 - Produce Lists"],
    ["3 - Produce Default Lists"],
    ["4 - Edit Lists"],
    ["5 - Custom Search"],
    ["x - Exit"]]
    getting = True
    while getting:
        clear()
        print(tabulate(table, headers="firstrow", tablefmt="rst"))
        command = input("> ")
        try:
            if(str.lower(command) == "x"):
                return
            command = int(command)
            if(command > 0 and command < 6):
                if(command == 1):
                    fullRefresh()
                if(command == 2):
                    loadFilterList()
                    produceLists(listData)
                if(command == 3):
                    produceLists(defaultListData)
                if(command == 4):
                    editLists()
                if(command == 5):
                    try:
                        CustomSearch()
                    except Exception as ex:
                        print(ex)
                clear()
                continue
            else:
                print("please enter a valid command.")
                input("press enter to reload menu")
                clear()
                continue
        except:
            print("please enter a valid command.")
            input("press enter to reload menu")
            clear()
            continue


def main():
    init()
    Menu()


main()
