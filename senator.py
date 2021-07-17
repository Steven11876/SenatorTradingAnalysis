import requests
import yfinance
import math
import pandas
from datetime import date

def get_data():
    """Downloads the raw data and creates a list from it"""
    url = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"

    r = requests.get(url, allow_redirects=True)

    open('senate.txt', 'wb').write(r.content)

    file = open('senate.txt', "r")

    comprehensive = file.read()
    comprehensive = comprehensive[1:]
    comprehensive = comprehensive[:-1]
    created = []

    while comprehensive.find("{") != -1:
        dict = {}
        point = comprehensive.find("}")
        snip = comprehensive[0:point+1]
        comprehensive=comprehensive[point+3:]
        snip = snip[1:]
        snip = snip[:-1]

        while snip.find(":") != -1:
            snip = snip[1:]
            secondquote = snip.find('"')
            key = snip[:secondquote]
            snip = snip[secondquote+4:]
            fourthquote = snip.find('"')
            word = snip[:fourthquote]
            snip = snip[fourthquote+3:]
            dict[key] = word

        created.append(dict)

    return created


def unscientize(number):
    """Helper function for converting numbers in scientific form to numerical form"""
    point = number.find("e")
    if point == -1:
        return float(number)
    sign = number[point+1]
    exponent = number[point+2:]
    while exponent[0]== "0":
        exponent = exponent[1:]
    if sign == "+":
        exponent = int(exponent)
    elif sign == "-":
        exponent = int(exponent) * -1
    number = float(number[:point])
    number = number * (10 ** exponent)
    return number


def filter_by_availability(initial_list):
    """Filters the list of trades to only those that have non-hand-written entries"""
    new_list = []
    for a in initial_list:
        if a["ticker"] != "N/A" and a["ticker"] != "--":
            new_list.append(a)

    return new_list


def filter_by_date(initial_list):
    """Prompts the user for a date to begin analysis on. Ends on present date"""
    global year
    global month
    global day
    year = input("Enter the number of the earliest year (2012-2021):")
    month = input("Enter the date of the month (01-12)(Please enter 0 before if single digit):")
    day = input("Enter the date of the day (01-31)(Please enter 0 before if single digit):")
    return_list= []
    for a in initial_list:
        if a['transaction_date'][-4:]> year:
            return_list.append(a)
        elif a['transaction_date'][-4:]== year:
            if a['transaction_date'][0:2]> month:
                return_list.append(a)
            elif a['transaction_date'][0:2]== month:
                if a['transaction_date'][-7:-5] >= day:
                    return_list.append(a)
                else:
                    return return_list
            else:
                return return_list
        else:
            return return_list


def filter_by_purchase(initial_list):
    """Filters the list to only purchases"""
    new_list = []
    for a in initial_list:
        if a["type"] == "Purchase":
            new_list.append(a)
    return new_list


def filter_by_sale(initial_list):
    """Filters the list to only sales"""
    new_list = []
    for a in initial_list:
        if a["type"] != "Purchase":
            new_list.append(a)
    return new_list


def all_senators(adapted_list):
    """Returns a dictionary with all the senator names"""
    senate_dict = {}

    for a in adapted_list:
        try:
            if a["senator"] not in senate_dict:
                senate_dict[a["senator"]] = 1
            else:
                senate_dict[a["senator"]] += 1
        except:
            continue
    return senate_dict


def filter_by_senator(initial_list):
    """Allows the user to filter the list by a specific senator"""
    new_list = []
    senate_dict = all_senators(initial_list)
    for key, value in senate_dict.items():
        print(key)
    senator = input("Please copy one senator above to analyze:")
    print (senator)
    for a in initial_list:
        try:
            if a["senator"] == senator:
                new_list.append(a)
        except:
            continue
    return new_list


def analyze_all_senators(initial_list):
    """Returns a dictionary with the results for every single senator"""
    dict_of_results = {}
    senate_dict = all_senators(initial_list)
    for key, value in senate_dict.items():
        new_list = []
        for a in initial_list:
            try:
                if a["senator"] == key:
                    new_list.append(a)
            except:
                continue
        dict_of_results[key] = hypothetical_growth(new_list)

    sorted_dict = sorted(dict_of_results.items(), key=lambda x: x[1], reverse=True)

    return sorted_dict


def find_total_value(adapted_list):
    """Finds the total value of trades in the list"""
    value_dict = {}
    for a in adapted_list:
        if a["amount"] not in value_dict:
            value_dict[a["amount"]] = 1
        else:
            value_dict[a["amount"]] += 1

    total_value = 0
    total_value += (value_dict.get("$1,001 - $15,000", 0))*8000 + (value_dict.get("$15,001 - $50,000", 0))*32500 + (value_dict.get("$50,001 - $100,000", 0))*75000 + (value_dict.get("$100,001 - $250,000", 0))*175000 + (value_dict.get("$250,001 - $500,000", 0))*375000 + (value_dict.get("$500,001 - $1,000,000", 0))*750000 + (value_dict.get("$1,000,001 - $5,000,000", 0))*3000000 + (value_dict.get("$5,000,001 - $25,000,000", 0))*15000000 + (value_dict.get("$25,000,001 - $50,000,000", 0))*37500000 + (value_dict.get("Over $50,000,000", 0))*50000000

    return total_value


def hypothetical_growth(adapted_list):
    """Finds the hypothetical growth of the account if the senators trades were copied"""
    total_value = find_total_value(adapted_list)
    total_growth_rate = 0
    today = date.today()
    todaydate = today.strftime("%Y-%m-%d")

    for a in adapted_list:
        print (a)

        beforedate = a["transaction_date"]
        month = beforedate[:2]
        day = beforedate[3:5]
        year = beforedate[6:10]

        yearspassed = float(365* (int(today.strftime("%Y"))-int(year)) + 30 * (int(today.strftime("%m"))-int(month)) + int(today.strftime("%d"))- int(day))/365

        tickerSymbol = a["ticker"]
        print (a["ticker"])
        tickerData = yfinance.Ticker(tickerSymbol)

        info = tickerData.info
        if str(info) == "{'logo_url': ''}":
            if a["amount"] == "$1,001 - $15,000":
                total_value -= 8000
            if a["amount"] == "$15,001 - $50,000":
                total_value -= 32500
            if a["amount"] == "$50,001 - $100,000":
                total_value -= 75000
            if a["amount"] == "$100,001 - $250,000":
                total_value -= 175000
            if a["amount"] == "$250,001 - $500,000":
                total_value -= 375000
            if a["amount"] == "$500,001 - $1,000,000":
                total_value -= 750000
            if a["amount"] == "$1,000,001 - $5,000,000":
                total_value -= 3000000
            if a["amount"] == "$5,000,001 - $25,000,000":
                total_value -= 15000000
            if a["amount"] == "$25,000,001 - $50,000,000":
                total_value -= 37500000
            if a["amount"] == "Over $50,000,000":
                total_value -= 50000000

            continue

        tickerDf = tickerData.history( period='1d', start= (year + '-' + month + '-'+ day), end= todaydate)


        try:
            priorprice = unscientize(str(tickerDf["Open"][0]))
        except:
            if a["amount"] == "$1,001 - $15,000":
                total_value -= 8000
            if a["amount"] == "$15,001 - $50,000":
                total_value -= 32500
            if a["amount"] == "$50,001 - $100,000":
                total_value -= 75000
            if a["amount"] == "$100,001 - $250,000":
                total_value -= 175000
            if a["amount"] == "$250,001 - $500,000":
                total_value -= 375000
            if a["amount"] == "$500,001 - $1,000,000":
                total_value -= 750000
            if a["amount"] == "$1,000,001 - $5,000,000":
                total_value -= 3000000
            if a["amount"] == "$5,000,001 - $25,000,000":
                total_value -= 15000000
            if a["amount"] == "$25,000,001 - $50,000,000":
                total_value -= 37500000
            if a["amount"] == "Over $50,000,000":
                total_value -= 50000000

            continue

        currentprice = unscientize(str(tickerDf["Open"][-1]))

        growthrate= math.log(currentprice/ priorprice)/yearspassed*100
        growthrate = round(growthrate, 3)

        if a["amount"] == "$1,001 - $15,000":
            adjustedgrowthrate = growthrate * 8000
        if a["amount"] == "$15,001 - $50,000":
            adjustedgrowthrate = growthrate * 32500
        if a["amount"] == "$50,001 - $100,000":
            adjustedgrowthrate = growthrate * 75000
        if a["amount"] == "$100,001 - $250,000":
            adjustedgrowthrate = growthrate * 175000
        if a["amount"] == "$250,001 - $500,000":
            adjustedgrowthrate = growthrate * 375000
        if a["amount"] == "$500,001 - $1,000,000":
            adjustedgrowthrate = growthrate * 750000
        if a["amount"] == "$1,000,001 - $5,000,000":
            adjustedgrowthrate = growthrate * 3000000
        if a["amount"] == "$5,000,001 - $25,000,000":
            adjustedgrowthrate = growthrate * 15000000
        if a["amount"] == "$25,000,001 - $50,000,000":
            adjustedgrowthrate = growthrate * 37500000
        if a["amount"] == "Over $50,000,000":
            adjustedgrowthrate = growthrate * 50000000


        if a["type"] == "Purchase":
            total_growth_rate += adjustedgrowthrate
        else:
            total_growth_rate -= adjustedgrowthrate

    return total_growth_rate/total_value


def SandP(year, month, day):
    """Finds the growth of the S and P stock index within the same timeframe"""
    today = date.today()
    todaydate = today.strftime("%Y-%m-%d")

    tickerSymbol = "^GSPC"
    tickerData = yfinance.Ticker(tickerSymbol)
    tickerDf = tickerData.history( period='1d', start= (year + '-' + month + '-'+ day), end= todaydate)
    prices = str(tickerDf.values)
    point = prices.find(" ")
    Bprices = prices[:point]
    Bprices = Bprices[2:]
    priorprice = unscientize(Bprices)


    Cprices = prices
    for i in range(7):
        point = Cprices.rfind(" ")
        Cprices = Cprices[:point]

    point = Cprices.rfind("[")
    Cprices = Cprices[point+1:]
    currentprice = unscientize(Cprices)

    yearspassed = float(365* (int(today.strftime("%Y"))-int(year)) + 30 * (int(today.strftime("%m"))-int(month)) + int(today.strftime("%d"))- int(day))/365

    growthrate= math.log(currentprice/ priorprice)/yearspassed*100
    growthrate = round(growthrate, 3)

    print("The S and P stock index grew by " + str(growthrate) + " percent year-on-year throughout this time period. The average retail investor underperforms this benchmark.")

if __name__ == '__main__':
    senatordata = get_data()
    sorteddata = filter_by_date(senatordata)
    sorteddata = filter_by_availability(sorteddata)
    sorteddata = filter_by_senator(sorteddata)
    SandP(year, month, day)
    b = hypothetical_growth(sorteddata)
    print ("The senator's stocks would've grown by " + str(round(b, 3)) + " percent in the same time period.")


