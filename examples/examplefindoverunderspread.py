from pathlib import Path
import logging

import betfairlightweight

from betfairlightweight import filters

from betfairlightweight.filters import price_projection

# setup logging
logging.basicConfig(level=logging.INFO)  # change to DEBUG to see log all updates

# create trading instance

trading = betfairlightweight.APIClient("", "", app_key="", certs='')

# login
trading.login()

# event_types = trading.betting.list_event_types()

# print([event["eventType"]["name"] for event in event_types])
# print([event["eventType"]["id"] for event in event_types])


# soccer_event_type = next((et for et in event_types if et.event_type.name == 'Soccer'), None)

# # Check if we found the soccer event and print the ID
# if soccer_event_type:
#     print('Soccer Event Type ID:', soccer_event_type.event_type.id)
# else:
#     print('Soccer event type not found')

market_filter = filters.market_filter(
    event_type_ids=['1'],  # Soccer
    competition_ids=['12531088'],  # Assuming '210' is the ID for Euro 2024
    market_type_codes=['CORRECT_SCORE','OVER_UNDER_05','OVER_UNDER_15','OVER_UNDER_25','OVER_UNDER_35','OVER_UNDER_45'],  # Check the exact code for "Under 3.5 Goals"
)

# print(market_filter)

market_catalogues = trading.betting.list_market_catalogue(
    filter=market_filter,
    market_projection=['MARKET_START_TIME', 'RUNNER_DESCRIPTION', 'EVENT'],
    max_results='1000'
)

price_proj = price_projection(
    price_data=['EX_ALL_OFFERS', 'EX_TRADED', 'EX_BEST_OFFERS'],  # includes all available offers, traded prices, and the best offers
    virtualise=True,
    # ex_best_offers_overrides={
    #     'best_prices_depth': 0  # Depth of prices to return, e.g., top 3 available prices
    # }
)

class Events:
    def __init__(self):
        self.events = {}
    def addRunner(self, eventName, runnerName, price):
        if eventName in self.events:
            event = self.events[eventName]
        else: 
            event = {}
        event[runnerName] = price
        self.events[eventName] = event
    def getEvents(self):
        return self.events
    def getEvent(self, name):
        return self.events[name]

events = Events()
# Optionally, fetch market books to get results
for market_catalogue in market_catalogues:
    print(f"-------------- {market_catalogue['event']['name']} --- {market_catalogue['marketName']} --------------------")
    id_to_name = {}
    for runner in market_catalogue.runners:
        id_to_name[runner['selectionId']] = runner['runnerName'] 
    # print(id_to_name)
    market_books = trading.betting.list_market_book(market_ids=[market_catalogue.market_id], price_projection=price_proj)
    for market_book in market_books:
        for runner in market_book.runners:
            name = id_to_name[runner.selection_id]
            if len(runner.ex['availableToBack']) > 0 and len(runner.ex['availableToLay']) > 0:
                print(f"Runner Name: {name}, Status: {runner.status}, Last Price Traded: {runner.last_price_traded},  Available to back {runner.ex['availableToBack'][0]}, Available to lay {runner.ex['availableToLay'][0]}")
                events.addRunner(market_catalogue['event']['name'], name, runner.ex['availableToBack'][0].price)
            else:
                print("NOTHING TO BACK OR LAY")
print("--------------------------------------------------------------------")

def d_to_p(decimal_odds):
    probability = 1.0 / decimal_odds
    return probability

def odd_reverse(odd):
    return 1.0/(1.0-(1.0/odd))


for key in events.getEvents():
    print(f"---------- {key} ------------------")
    event = events.getEvent(key)
    ##################### INPUTS ###########################

    ## Over/Under

    under05 = event['Under 0.5 Goals']
    under15 = event['Under 1.5 Goals']
    under25 = event['Under 2.5 Goals']
    under35 = event['Under 3.5 Goals']

    ## Correct Score

    # 0
    s0v0=event['0 - 0']

    # 1
    s0v1=event['0 - 1']
    s1v0=event['1 - 0']

    # 2
    s1v1=event['1 - 1']
    s2v0=event['2 - 0']
    s0v2=event['0 - 2']

    # 3
    s2v1=event['2 - 1']
    s1v2=event['1 - 2']
    s3v0=event['3 - 0']
    s0v3=event['0 - 3']

    ########################################################

    #https://www.wolframalpha.com/input/?i=taylor+series+of+1%2F%281%2Bx%29
    # Small deviations in probability is the same as the decimal odd change since d=1/x is d=1-x under taylor expansion.

    ### 0 Goals
    over_under_0 = d_to_p(under05)
    exact_0      = d_to_p(s0v0)
    diff_0=(over_under_0 - exact_0)
    print("==========0 Goals===============")
    print(f"Over 0 direct: {1 - d_to_p(under05)}")
    print(f"Over/Under prob of 0: {over_under_0} --- Correct Score prob of 0: {exact_0}")
    print(diff_0)
    if(diff_0 > 0):
        print("Bet correct score market")
    else:
        print("Bet over/under market")

    ## 1 Goal
    over_under_1 = (1 - (d_to_p(under05) + d_to_p(odd_reverse(under15))))
    exact_1      = (d_to_p(s1v0) + d_to_p(s0v1))
    over_odd_1   = 1 - (over_under_0 + over_under_1)
    exact_odd_1  = 1 - (exact_0 + exact_1)
    diff_cum_1   = over_odd_1 - exact_odd_1
    diff_1=(over_under_1 - exact_1)
    print("==========1 Goals===============")
    print(f"Over 1 direct: {1 - d_to_p(under15)}")
    print(f"Over/Under prob of 1: {over_under_1} --- Correct Score prob of 1: {exact_1}")
    print(f"Over/Under over 1 prob: {over_odd_1} --- Correct Score over 1 prob: {exact_odd_1}")
    print(f"Over/Under under 1 prob: {1 - over_odd_1} --- Correct Score under 1 prob: {1 - exact_odd_1}")
    print(f"Diff exact: {diff_1}")
    print(f"Diff cum: {diff_cum_1}")
    if(diff_cum_1 > 0):
        print("Bet correct score market")
    else:
        print("Bet over/under market")


    ## 2 Goal
    over_under_2 = (1 - (d_to_p(under15) + d_to_p(odd_reverse(under25))))
    exact_2      = (d_to_p(s1v1) + d_to_p(s2v0) + d_to_p(s0v1))
    over_odd_2   = 1 - (over_under_0 + over_under_1 + over_under_2)
    exact_odd_2  = 1 - (exact_0 + exact_1 + exact_2)
    diff_cum_2   = over_odd_2 - exact_odd_2
    diff_2=(over_under_2 - exact_2)
    print("==========2 Goals===============")
    print(f"Over 2 direct: {1- d_to_p(under25)}")
    print(f"Over/Under prob of 2: {over_under_2} --- Correct Score prob of 2: {exact_2}")
    print(f"Over/Under over 2 prob: {over_odd_2} --- Correct Score over 2 prob: {exact_odd_2}")
    print(f"Over/Under under 2 prob: {1 - over_odd_2} --- Correct Score under 2 prob: {1 - exact_odd_2}")
    print(f"Diff exact: {diff_2}")
    print(f"Diff cum: {diff_cum_2}")
    if(diff_cum_2 > 0):
        print("Bet correct score market")
    else:
        print("Bet over/under market")


    ## 3 Goal
    over_under_3 = (1 - (d_to_p(under25) + d_to_p(odd_reverse(under35))))
    exact_3      = (d_to_p(s2v1) + d_to_p(s1v2) + d_to_p(s3v0) + d_to_p(s0v3))
    over_odd_3   = 1 - (over_under_0 + over_under_1 + over_under_2 + over_under_3)
    exact_odd_3  = 1 - (exact_0 + exact_1 + exact_2 + exact_3)
    diff_cum_3   = over_odd_3 - exact_odd_3
    diff_3=(over_under_3 - exact_3)
    print("==========3 Goals===============")
    print(f"Over 3 direct: {1 - d_to_p(under35)}")
    print(f"Over/Under prob of 3: {over_under_3} --- Correct Score prob of 3: {exact_3}")
    print(f"Over/Under over 3 prob: {over_odd_3} --- Correct Score over 3 prob: {exact_odd_3}")
    print(f"Over/Under under 3 prob: {1 - over_odd_3} --- Correct Score under 3 prob: {1 - exact_odd_3}")
    print(f"Diff exact: {diff_3}")
    print(f"Diff cum: {diff_cum_3}")
    if(diff_cum_3 > 0):
        print("Bet correct score market")
    else:
        print("Bet over/under market")
