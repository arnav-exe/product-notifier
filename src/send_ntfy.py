import requests
from dotenv import load_dotenv
import os

load_dotenv()


def post_ntfy(body, product_url, retailer_name, retailer_logo_url, ntfy_topic):
    requests.post(
        ntfy_topic,
        data=body,
        headers={
            "Title": f"{retailer_name} Alert",
            "Priority": "default",
            "Tags": "loudspeaker",
            "Icon": retailer_logo_url,
            "Markdown": "yes",
            # "Actions": f"copy, Copy URL, product_url, clear=true", # not implemented yet bomboclaart - wait for v1.23 android release
        }
    )


def ntfy_delete(topic: str, sequence_id: str):  # feature still in development
    return requests.delete(f"https://ntfy.sh/{topic}/{sequence_id}")


if __name__ == "__main__":
    from .ntfy_templates import on_sale, below_max_price, in_stock
    from .schema import Product
    import time

    product = Product(
        "B0FQFB8FMG",
        "airpods pro 3",
        True,
        True,
        199.99,
        249.99,
        "https://amazon.com/dp/airpods-pro-3",
        "amazon",
        "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
    )

    on_sale_body = on_sale(product, 225)
    below_max_price_body = below_max_price(product, 225)
    in_stock_body = in_stock(product)

    ntfy_topic = os.getenv("NTFY_TOPIC_URL")

    post_ntfy(on_sale_body, ntfy_topic)

    time.sleep(2)

    post_ntfy(below_max_price_body, ntfy_topic)

    time.sleep(2)

    post_ntfy(in_stock_body, ntfy_topic)
