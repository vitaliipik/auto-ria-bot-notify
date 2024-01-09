import sqlite3

# Ініціалізація бази даних SQLite3
conn = sqlite3.connect('auto_db.sqlite')
cursor = conn.cursor()


def create_table():
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


def check_unique(car_id):
    cursor.execute('SELECT id FROM cars WHERE car_id = ?', (car_id,))
    return cursor.fetchone() is None


def insert_car(car_data):
    car_data["photos"] = ";".join(car_data["photos"])

    cursor.execute('''
        INSERT INTO cars (car_id, brand, price, link, auction_link, photos,is_old_value)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (car_data["car_id"], car_data['brand'], car_data["price"], car_data["link"], car_data["auction_link"],
          car_data["photos"], False))
    conn.commit()


def update_car_price(car_id, new_price):
    cursor.execute('UPDATE cars SET price = ? WHERE car_id = ?', (new_price, car_id))
    conn.commit()


def get_stored_car(car_id):
    cursor.execute('SELECT * FROM cars WHERE car_id = ?', (car_id,))
    return dict(zip(['id', 'car_id', 'brand', 'price', 'link', 'auction_link', 'photos'], cursor.fetchone()))


def get_all_old_car_id():
    cursor.execute("SELECT car_id FROM cars WHERE is_old_value = TRUE")
    return  cursor.fetchall()

def delete_old_car_id(car_id):
    try:
        cursor.execute('DELETE FROM cars WHERE car_id = ?', (car_id,))
        conn.commit()
    except sqlite3.Error as error:
        return {"message":f"Error while deleting: {error}","status_code":400},400
    return {"message":"Successes", "status_code":200},200

def make_all_car_old():
    try:
        cursor.execute('UPDATE cars SET is_old_value = TRUE')
        conn.commit()
    except sqlite3.Error as error:
        return {"message":f"Error while updating: {error}","status_code":400},400
    return {"message":"Successes", "status_code":200},200

def make_car_new(car_id):
    try:
        cursor.execute('UPDATE cars SET is_old_value = FALSE WHERE car_id = ?', (car_id,))
        conn.commit()
    except sqlite3.Error as error:
        return {"message":f"Error while updating: {error}","status_code":400},400
    return {"message":"Successes", "status_code":200},200
