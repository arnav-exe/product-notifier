# import responses
# import requests
#
#
# actual_url = "https://api.bestbuy.com/v1/products/6643145.json?show=orderable,name,onSale,regularPrice,salePrice,dollarSavings,percentSavings,priceUpdateDate,url&apiKey=ZMmvNAwrBTuVUkUA0zPOHAlo"
# base_url = "https://api.bestbuy.com/v1/products/6643145.json?"
# good_res = {'orderable': 'Available', 'name': 'Apple - AirPods\xa0Pro\xa03, Wireless Active Noise Cancelling Earbuds with Heart Rate Sensing Feature - White', 'onSale': False, 'regularPrice': 249.99, 'salePrice': 249.99, 'dollarSavings': 0.0, 'percentSavings': '0.0', 'priceUpdateDate': '2026-02-03T00:01:00', 'url': 'https://api.bestbuy.com/click/-/6376563/pdp'}
# bad_res = {"errorCode": "403", "errorMessage": "The provided API Key has reached the per second limit allotted to it.", "help": "https://developer.bestbuy.com/legal#operationalPolicy"}
#
#
# @responses.activate
# def good_response():
#     return responses.add(
#         method=responses.GET,
#         url=actual_url,
#         json=bad_res,
#         status=403
#     )
#
#
#
# if __name__ == "__main__":
#     simulated_response = requests.get(actual_url)
#     print(simulated_response.status_code)


import responses
import requests
import re


@responses.activate
def test_simple():
    responses.get(
        re.compile(r"https://fruityvice.com/api/fruit/.*"),  # only matches till params by default
        json={"message": "mocked"},
        status=404,
    )

    responses.post(
        "http://twitter.com/api/1/foobar",
        json={"type": "post"},
    )

    responses.patch(
        "http://twitter.com/api/1/foobar",
        json={"type": "patch"},
    )

    resp_get = requests.get("https://fruityvice.com/api/fruit/carbohydrates?min=15&max=16")

    print(resp_get.status_code)
    print(resp_get.json())


test_simple()
