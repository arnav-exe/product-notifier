# Goal of this refactor
 * separate concerns into 3 distinct categories:
    1. fetching data from src (via api)
    1. normalizing data into internal representation
    1. consuming normalized data


# Internal Representation
```python
ir = {
    "identifier": "str",
    "product_name": "str",
    "in_stock": "bool",
    "on_sale": "bool",
    "sale_price": "float",
    "regular_price": "float",
    "dollar_savings": "float",
    "percent_savings": "float",
    "retailer": "str",
    "product_url": "str",
    "retailer_icon": "str"
}
```

This state will be stored in a python `dataclass`. Dataclasses should be used whenver the class you are defining holds a lot of attributes. Therefore, dataclasses are typically used over regular classes to store state.


# TODO:
 1. get data of an amazon product that is in stock AND NOT on sale (to confirm that if product is not on sale, current_price == before_price) - maybe lgtv
