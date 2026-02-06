from bestbuy import BestbuySource


if __name__ == "__main__":
    bb = BestbuySource()

    import logging
    logger = logging.getLogger()
    print(bb.fetch_raw(6376563, logger))
