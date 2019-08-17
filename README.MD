# BoneMeal
## Description
*BoneMeal is a python 3 script which pulls the latest stock list from http://freetrade.io/stock-universe, grabs all associated dividend data from Yahoo Finance and then allows the user to produce default and custom csv files containing stocks based of filters relating to dividend yeild, average dividend growth rate and PE ratio.*
***
## ChangeLog
### **Version 1.2**
#### Auto-Update DataStore
 - BoneMeal will check for updates to the freetrade stock universe when opened and, if neccessary, will refresh the dividend data for all stocks following any changes in the stock universe
### **Version 1.1**
#### Major Bugfixes
 - Fixed crash during initialisation which prevented datastore files being created
 - Fixed bug which prevented initial creation of list storage file, which disabled the edit lists functionality
 - Fixed bug in edit filter function which prevented progression past entering a new name for a pre-existing filter
### **Version 1.0**
#### Initial release
 - Loads and stores latest stock and dividend data and gives option to refresh stock and dividend data
 - Allows outputting of default filter lists
    - Dividend growth list - List of all stocks deemed to be dividend growth stocks
    - High Yield - List of all stock with a high dividend yield
    - High yield growth - List of a stocks with a high yield and high average dividend growth
    - Cream - List of stocks with reasonable to high yield, stable dividend growth and a relatively low PE ratio
 - Allows custom lists to be added, edited, removed and cleared so that they can be stored and produced
 - Option for one off custom lists to be produced via custom search 
 - Menu GUI
 - Loading bar with adaptive ETA during initialisation
 ***