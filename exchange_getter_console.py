import logging
import sys
from datetime import datetime, timedelta
import platform

import aiohttp
import asyncio

BASE_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='
DEFAULT_CURRENCIES = ['EUR', 'USD']


def set_days_from_chat_massage(msg: str) -> int:
    """This function parses a message from a chat, returns the number of days requested by the user"""
    msg_list = msg.split(" ")
    if len(msg_list) > 1:
        try:
            days = int(msg_list[1].strip().replace(",", ""))
        except ValueError:
            days = 1
    else:
        days = 1
    return days


def set_currencies_from_arguments() -> list[str]:
    
    """parses the console parameters, returns list of additional currencies requested by the user"""
    
    try:
        res = []
        for currency in sys.argv:
            res.append(currency.upper().strip().replace(",", ""))

        return res
    except IndexError:
        return []


def set_days_from_arguments() -> int:
    
    """parses the console parametres, returns the number of days requested by the user"""
    
    try:
        days = int(sys.argv[1].replace(",", ""))
    except ValueError:
        days = 1
    except IndexError:
        days = 1
    if days > 10:
        days = 10
    return days



def get_list_of_urls(amount_days) -> list[str]:
    
    """generates a list of links for an asynchronous request to the bank API"""
    
    urls_list = [BASE_URL + (datetime.now().date() - timedelta(days=delta)).strftime('%d.%m.%Y') for delta in
                 range(amount_days)]

    return urls_list


def formatting_data(data: dict, requested_currencies) -> str:
    
    """formats the data"""
    
    res = [f"Date: {data.get('date')}"]

    try:
        for currency_dict in data['exchangeRate']:
            if currency_dict['currency'].upper() in requested_currencies:
                res.append(
                    f"{currency_dict['currency'].upper()}: sale: {currency_dict['saleRateNB']} purchase: {currency_dict['purchaseRateNB']}")
    except KeyError:
        res.append("Not founded exchange rate")
    return "\n".join(res) + "\n"


async def get_json(session, url, requested_currencies):
    
    """takes data in json format from api bankab returns a dictionary with data on the exchange rate"""
    
    async with session.get(url) as response:
        if response.status == 200:
            res = formatting_data(await response.json(), requested_currencies)
        else:
            logging.error(f"Error status {response.status} for {url}")

    return res


async def main(urls_list, currencies_list):

    async with aiohttp.ClientSession() as session:
        try:
            res = []
            for url in urls_list:
                res.append(get_json(session, url, currencies_list))

            return await asyncio.gather(*res)

        except aiohttp.ClientConnectorError as e:
            logging.error(f"Connection error {url}: {e}")


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    days = set_days_from_arguments()
    urls = get_list_of_urls(days)
    requested_currencies = DEFAULT_CURRENCIES + set_currencies_from_arguments()

    res = asyncio.run(main(urls, requested_currencies))
    
    for currency in res:
        print(currency)

