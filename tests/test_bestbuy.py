from src.sources.bestbuy import BestbuySource


bb = BestbuySource()


# test that bestbuy class object source_name == "bestbuy"
def test_source_name():
    assert bb.source_name == "bestbuy"


def test_raw_output():
    import logging
    logger = logging.getLogger()

    print(bb.fetch_raw("amazon", logger))

    # assert that returned json contains following keys:

