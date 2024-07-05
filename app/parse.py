import time
import csv
from dataclasses import dataclass
from urllib.parse import urljoin
from typing import List

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def setup_driver() -> webdriver.Chrome:
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")
    driver = webdriver.Chrome(options=options)
    return driver


def accept_cookies(driver: webdriver.Chrome) -> None:
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "cookie-banner"))
        )
        accept_button.click()
    except Exception as e:
        print("Cookies accept button not found or not clickable:", e)


def parse_product(element: webdriver.remote.webelement.WebElement) -> Product:
    title = element.find_element(By.CLASS_NAME, "title").text
    description = element.find_element(By.CLASS_NAME, "description").text
    price = float(
        element.find_element(By.CLASS_NAME, "price").text.replace("$", "")
    )
    rating = len(
        element.find_elements(By.CLASS_NAME, "ratings")
    )  # Number of stars
    num_of_reviews = int(
        element.find_element(By.CLASS_NAME, "ratings").text.split(" ")[0]
    )
    return Product(title, description, price, rating, num_of_reviews)


def parse_page(
    driver: webdriver.Chrome, url: str, with_pagination: bool = False
) -> List[Product]:
    driver.get(url)
    accept_cookies(driver)

    products: List[Product] = []
    while True:
        time.sleep(2)  # Wait for the page to load
        product_elements = driver.find_elements(By.CLASS_NAME, "thumbnail")
        for elem in product_elements:
            product = parse_product(elem)
            products.append(product)

        if with_pagination:
            try:
                more_button = driver.find_element(
                    By.CLASS_NAME, "btn.btn-primary.btn-lg.btn-block"
                )
                more_button.click()
            except Exception as e:
                print(
                    "No more pages to load or unable to click more button:", e
                )
                break  # No more pages to load
        else:
            break

    return products


def save_to_csv(filename: str, products: List[Product]) -> None:
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Title", "Description", "Price", "Rating", "Number of Reviews"]
        )
        for product in products:
            writer.writerow(
                [
                    product.title,
                    product.description,
                    product.price,
                    product.rating,
                    product.num_of_reviews,
                ]
            )


def get_all_products() -> None:
    driver = setup_driver()

    pages_info = [
        ("home.csv", urljoin(BASE_URL, "test-sites/e-commerce/more/"), False),
        (
            "computers.csv",
            urljoin(BASE_URL, "test-sites/e-commerce/computers/"),
            False,
        ),
        (
            "laptops.csv",
            urljoin(BASE_URL, "test-sites/e-commerce/computers/laptops/"),
            True,
        ),
        (
            "tablets.csv",
            urljoin(BASE_URL, "test-sites/e-commerce/computers/tablets/"),
            True,
        ),
        (
            "phones.csv",
            urljoin(BASE_URL, "test-sites/e-commerce/phones/"),
            False,
        ),
        (
            "touch.csv",
            urljoin(BASE_URL, "test-sites/e-commerce/phones/touch/"),
            True,
        ),
    ]

    for filename, url, with_pagination in tqdm(
        pages_info, desc="Scraping pages"
    ):
        products = parse_page(driver, url, with_pagination)
        save_to_csv(filename, products)

    driver.quit()


if __name__ == "__main__":
    get_all_products()
