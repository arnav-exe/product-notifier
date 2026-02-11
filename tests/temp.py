import responses
import re

from src.sources.bestbuy import BestbuySource


BB_200_RES = {'orderable': 'Available', 'name': 'Apple - AirPods\xa0Pro\xa03, Wireless Active Noise Cancelling Earbuds with Heart Rate Sensing Feature - White', 'onSale': False, 'regularPrice': 249.99, 'salePrice': 249.99, 'dollarSavings': 0.0, 'percentSavings': '0.0', 'priceUpdateDate': '2026-02-03T00:01:00', 'url': 'https://api.bestbuy.com/click/-/6376563/pdp'}

BB_403_RES = {"errorCode": "403", "errorMessage": "The provided API Key has reached the per second limit allotted to it.", "help": "https://developer.bestbuy.com/legal#operationalPolicy"}


@responses.activate
def bestbuy_200(identifier: str):
    responses.get(
        re.compile(r"https://api.bestbuy.com/v1/products/.*\.json"),
        json=BB_200_RES,
        status=200
    )


@responses.activate
def bestbuy_403(identifier: str):
    responses.get(
        re.compile(r"https://api.bestbuy.com/v1/products/.*\.json"),
        json=BB_403_RES,
        status=403
    )



def test_bb():
    bestbuy_403("6643145")

    bb = BestbuySource()

    data = bb.fetch_raw(6643145)

    print(data.staus_code)

    assert data.status_code == 403


test_bb()
