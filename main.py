import asyncio
import os
import re
from typing import List

import requests
from bs4 import BeautifulSoup
from telegram import Bot, InputMediaPhoto

from models import check_unique, insert_car, update_car_price, create_table, get_stored_car, get_all_old_car_id, \
    delete_old_car_id, make_all_car_old, make_car_new

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PHOTO_NUMBER = 10
PARAMS = {
    'category_id': 1,  # Легкові
    'brand.id[0]': 79,  # Toyota
    'model.id[0]': "2104",  # Sequoia
    'damage.not': 0,
    'country.import.usa.not': 0,
    'size': 999
}
TELEGRAM_MESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
SEARCH_URL = "https://auto.ria.com/uk/search/?"

bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def notify_telegram(car: dict, add_info=""):
    """
    function to send telegram message to user
    :param car: dictionary with car data
    :param add_info: additional information to the message
    :return:
    """
    price = car["price"].split(";")  # split price to usd and uah

    message = (f"{add_info}Марка автомобіля: {car['brand']}\n"
               f"Ціна: {price[0]}$ - {price[1]}грн\n"
               f"<a href='{car['link']}'>Посилання на автомобіль</a>")

    photos = car["photos"]

    if isinstance(photos, str):
        photos = photos.split(";")

    media = [InputMediaPhoto(convert_photo_to_byte(photo)) for photo in photos]

    response = requests.get(TELEGRAM_MESSAGE_URL)
    if response.status_code != 200:
        print(response)

    # get all telegram bot members
    telegram_channels_id = set()
    for result in response.json()["result"]:
        if "message" in result and (
                result["message"]["chat"]["type"] == "group" or result["message"]["chat"]["type"] == "private"):
            telegram_channels_id.add(result["message"]["chat"]["id"])

    for telegram_channel in telegram_channels_id:
        try:
            await bot.send_media_group(chat_id=telegram_channel, media=media, parse_mode="html", caption=message)
        except Exception as e:
            print(e)


def get_photos(soup: BeautifulSoup) -> List[str]:
    """
    Get photos from html page
    :param soup: A data structure representing a parsed HTML document
    :return: List of photos TELEGRAM_MESSAGE_URL
    """
    gallery = soup.find("div", "gallery-order")
    carousel_photo = gallery.findAll("div", "photo-620x465")

    photos = []
    for photo in carousel_photo[:PHOTO_NUMBER]:

        img_url = photo.find("img")['src']
        # change image to full size
        separated_string = img_url.split(".")
        separated_string[-2] = separated_string[-2][:-1] + "f"
        img = ".".join(separated_string)

        if img[:5] == "https" and img[-3:] != "svg":
            photos.append(img)

    return photos


def convert_photo_to_byte(photo: str) -> bytes:
    """
    Convert a photo to byte
    :param photo: photo SEARCH_URL
    :return: bytes representation of photo
    """
    response = requests.get(photo, stream=True)
    return response.content


def get_car_data(car: BeautifulSoup) -> dict:
    """
    get car data from html page
    :param car: A data structure representing a parsed HTML document of car
    :return: return brand, SEARCH_URL to car, photos
    """
    car_metadata_class = car.find("div", "hide")

    brand = car_metadata_class.get('data-mark-name')

    car_link = car.find("a", class_="m-link-ticket").get("href")
    response = requests.get(car_link, params=PARAMS)
    soup = BeautifulSoup(response.text, 'html.parser')

    photos = get_photos(soup)

    auction_link = get_auction_link(brand)  # Function to get auction link

    return {'brand': brand, 'link': car_link, 'auction_link': auction_link, 'photos': photos}


async def scrape_auto_ria():

    response = requests.get(SEARCH_URL, params=PARAMS)
    soup = BeautifulSoup(response.text, 'html.parser')
    cars = soup.find_all('section', class_='ticket-item')

    for car in cars:
        car_id = int(car.get('data-advertisement-id'))

        price = (car.find('div', class_='price-ticket').text.strip())
        # remove unnecessary characters from parsed price
        price = re.sub("\xa0грн| ", "", price).replace("$•", ";")

        # Checking if the car is unique
        if check_unique(car_id):

            car_metadata = get_car_data(car)
            car_metadata["price"] = price
            car_metadata["car_id"] = car_id

            await notify_telegram(car_metadata, "Новий автомобіль\n")
            insert_car(car_metadata)

        else:
            # If the car is not unique, check for price updates
            stored_car = get_stored_car(car_id)
            # change bool column for checking if car is sold
            make_car_new(car_id)

            if stored_car['price'] != price:
                update_car_price(car_id, price)

                del stored_car["id"]
                await notify_telegram(stored_car, "Увага! Змінена ціна на один із автомобілів\n")

    # get all sold car
    old_car = get_all_old_car_id()
    for car_id in old_car:
        stored_car = get_stored_car(car_id[0])
        await notify_telegram(stored_car, "Увага!\n Цей автомобіль був проданий\n")
        response = delete_old_car_id(car_id[0])
        if response[1] != 200:
            print(response[0])

    response = make_all_car_old()
    if response[1] != 200:
        print(response[0])


def get_auction_link(car_id):
    return f"https://example_auction.com/{car_id}"


async def main():
    create_table()

    while True:
        await scrape_auto_ria()
        await asyncio.sleep(600)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
