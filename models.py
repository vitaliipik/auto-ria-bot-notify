import sqlite3

# Init database SQLite3
conn = sqlite3.connect('auto_db.sqlite')
cursor = conn.cursor()


def create_table():
    """
    create a table if it doesn't exist'
    :return:
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id INTEGER,
            brand TEXT,
            price INTEGER,
            link TEXT,
            auction_link TEXT,
            photos TEXT,
            is_old_value BOOL,
            unique(car_id)
        )
    ''')
    conn.commit()


def check_unique(car_id: str):
    """
    check if car is already stored in database
    :param car_id: id of car to check
    :return: true if car is already and false otherwise
    """
    cursor.execute('SELECT id FROM cars WHERE car_id = ?', (car_id,))
    return cursor.fetchone() is None


def insert_car(car_data: dict) -> None:
    """
    insert car into the database
    :param car_data: dict of car data
    """
    car_data["photos"] = ";".join(car_data["photos"])

    cursor.execute('''
        INSERT INTO cars (car_id, brand, price, link, auction_link, photos,is_old_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (car_data["car_id"], car_data['brand'], car_data["price"], car_data["link"], car_data["auction_link"],
          car_data["photos"], False))
    conn.commit()


def update_car_price(car_id: str, new_price: str):
    """
    update car price
    :param car_id: car id to update
    :param new_price:
    :return:
    """
    cursor.execute('UPDATE cars SET price = ? WHERE car_id = ?', (new_price, car_id))
    conn.commit()


def get_stored_car(car_id: str) -> dict:
    """
    get stored car
    :param car_id: car id to retrieve
    :return: dict of car data
    """
    cursor.execute('SELECT * FROM cars WHERE car_id = ?', (car_id,))
    return dict(zip(['id', 'car_id', 'brand', 'price', 'link', 'auction_link', 'photos'], cursor.fetchone()))


def get_all_old_car_id():
    """
    get all sold car
    :return:
    """
    cursor.execute("SELECT car_id FROM cars WHERE is_old_value = TRUE")
    return cursor.fetchall()


def delete_old_car_id(car_id: str):
    """
    delete car by id
    :param car_id: car id to delete
    :return: message with info about deleted car
    """
    try:
        cursor.execute('DELETE FROM cars WHERE car_id = ?', (car_id,))
        conn.commit()
    except sqlite3.Error as error:
        return {"message": f"Error while deleting: {error}", "status_code": 400}, 400
    return {"message": "Successes", "status_code": 200}, 200


def make_all_car_old():
    """
    make all car old
    :return: message with info
    """
    try:
        cursor.execute('UPDATE cars SET is_old_value = TRUE')
        conn.commit()
    except sqlite3.Error as error:
        return {"message": f"Error while updating: {error}", "status_code": 400}, 400
    return {"message": "Successes", "status_code": 200}, 200


def make_car_new(car_id: str):
    """
    make new car
    :param car_id: car id to update
    :return: message with info
    """
    try:
        cursor.execute('UPDATE cars SET is_old_value = FALSE WHERE car_id = ?', (car_id,))
        conn.commit()
    except sqlite3.Error as error:
        return {"message": f"Error while updating: {error}", "status_code": 400}, 400
    return {"message": "Successes", "status_code": 200}, 200
