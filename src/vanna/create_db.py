import sqlite3

# Connect to the database (it will be created if it doesn't exist)
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Create a customers table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        address TEXT
    )
''')

# Create a sales table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        sale_date DATE NOT NULL,
        customer_id INTEGER,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
''')

# Create an orders table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_date DATE NOT NULL,
        customer_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
''')

# Insert sample data into customers table
customers_data = [
    ('Alice Johnson', 'alice@example.com', '123-456-7890', '123 Maple Street'),
    ('Bob Smith', 'bob@example.com', '987-654-3210', '456 Oak Avenue'),
    ('Charlie Brown', 'charlie@example.com', '555-555-5555', '789 Pine Road')
]

# Check for existing emails before inserting data
def insert_unique_data(cursor, table, columns, data):
    # 自动检测唯一字段（如 email）并跳过重复
    unique_col = None
    # 优先使用 email 字段
    if 'email' in columns:
        unique_col = 'email'
        unique_idx = columns.index('email')
    else:
        # 默认使用第一个字段
        unique_col = columns[0]
        unique_idx = 0
    for row in data:
        query = f"SELECT COUNT(*) FROM {table} WHERE {unique_col} = ?"
        cursor.execute(query, (row[unique_idx],))
        if cursor.fetchone()[0] == 0:
            insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(row))})"
            cursor.execute(insert_query, row)

# Insert unique data into customers table
customers_columns = ['name', 'email', 'phone', 'address']
insert_unique_data(cursor, 'customers', customers_columns, customers_data)

# Insert additional sample data into customers table
customers_data = [
    ('Diana Prince', 'diana@example.com', '111-222-3333', '101 Amazon Way'),
    ('Eve Adams', 'eve@example.com', '222-333-4444', '202 Elm Street'),
    ('Frank Castle', 'frank@example.com', '333-444-5555', '303 Birch Lane'),
    ('Grace Hopper', 'grace@example.com', '444-555-6666', '404 Cedar Court'),
    ('Hank Pym', 'hank@example.com', '555-666-7777', '505 Spruce Drive')
]

insert_unique_data(cursor, 'customers', customers_columns, customers_data)

# Insert additional sample data into customers table
customers_data = [
    ('Ivy Green', 'ivy@example.com', '666-777-8888', '606 Willow Street'),
    ('Jack White', 'jack@example.com', '777-888-9999', '707 Aspen Lane'),
    ('Karen Black', 'karen@example.com', '888-999-0000', '808 Redwood Drive'),
    ('Leo Blue', 'leo@example.com', '999-000-1111', '909 Cypress Avenue'),
    ('Mona Gray', 'mona@example.com', '000-111-2222', '1010 Fir Street'),
    ('Nina Silver', 'nina@example.com', '111-222-3333', '1111 Palm Court'),
    ('Oscar Gold', 'oscar@example.com', '222-333-4444', '1212 Poplar Road'),
    ('Pauline Violet', 'pauline@example.com', '333-444-5555', '1313 Magnolia Blvd'),
    ('Quincy Amber', 'quincy@example.com', '444-555-6666', '1414 Dogwood Circle'),
    ('Rita Crimson', 'rita@example.com', '555-666-7777', '1515 Hickory Lane'),
    ('Steve Indigo', 'steve@example.com', '666-777-8888', '1616 Juniper Way'),
    ('Tina Jade', 'tina@example.com', '777-888-9999', '1717 Sycamore Street'),
    ('Uma Ruby', 'uma@example.com', '888-999-0000', '1818 Alder Drive'),
    ('Victor Emerald', 'victor@example.com', '999-000-1111', '1919 Birchwood Court'),
    ('Wendy Sapphire', 'wendy@example.com', '000-111-2222', '2020 Maplewood Avenue'),
    ('Xander Topaz', 'xander@example.com', '111-222-3333', '2121 Elmwood Drive'),
    ('Yara Opal', 'yara@example.com', '222-333-4444', '2222 Cedarwood Lane'),
    ('Zane Quartz', 'zane@example.com', '333-444-5555', '2323 Pinewood Street')
]

insert_unique_data(cursor, 'customers', customers_columns, customers_data)

# Insert sample data into sales table
sales_data = [
    ('Laptop', 5, 1200.00, '2023-01-15', 1),
    ('Mouse', 20, 25.50, '2023-01-16', 2),
    ('Keyboard', 15, 45.00, '2023-01-17', 3),
    ('Monitor', 8, 300.00, '2023-01-18', 1),
    ('Laptop', 3, 1200.00, '2023-01-20', 2),
    ('Headphones', 10, 80.00, '2023-01-21', 3),
    ('Tablet', 12, 350.00, '2023-02-01', 4),
    ('Smartphone', 25, 800.00, '2023-02-02', 5),
    ('Printer', 7, 150.00, '2023-02-03', 6),
    ('Scanner', 5, 200.00, '2023-02-04', 7),
    ('Camera', 10, 500.00, '2023-02-05', 8),
    ('Speaker', 20, 100.00, '2023-02-06', 9),
    ('Router', 15, 120.00, '2023-02-07', 10)
]

cursor.executemany('''
    INSERT INTO sales (product_name, quantity, price, sale_date, customer_id)
    VALUES (?, ?, ?, ?, ?)
''', sales_data)

# Insert additional sample data into sales table
sales_data = [
    ('Tablet', 12, 350.00, '2023-02-01', 4),
    ('Smartphone', 25, 800.00, '2023-02-02', 5),
    ('Printer', 7, 150.00, '2023-02-03', 6),
    ('Scanner', 5, 200.00, '2023-02-04', 7),
    ('Camera', 10, 500.00, '2023-02-05', 8),
    ('Speaker', 20, 100.00, '2023-02-06', 9),
    ('Router', 15, 120.00, '2023-02-07', 10)
]

cursor.executemany('''
    INSERT INTO sales (product_name, quantity, price, sale_date, customer_id)
    VALUES (?, ?, ?, ?, ?)
''', sales_data)

# Insert additional sample data into sales table
sales_data = [
    ('Smartwatch', 30, 250.00, '2023-03-01', 11),
    ('Gaming Console', 15, 400.00, '2023-03-02', 12),
    ('VR Headset', 10, 600.00, '2023-03-03', 13),
    ('Drone', 8, 1200.00, '2023-03-04', 14),
    ('Electric Scooter', 5, 800.00, '2023-03-05', 15),
    ('Fitness Tracker', 25, 150.00, '2023-03-06', 16),
    ('Digital Camera', 12, 700.00, '2023-03-07', 17),
    ('Bluetooth Speaker', 20, 120.00, '2023-03-08', 18),
    ('Wireless Earbuds', 50, 80.00, '2023-03-09', 19),
    ('Portable Charger', 40, 50.00, '2023-03-10', 20),
    ('Smartphone Case', 100, 20.00, '2023-03-11', 21),
    ('Laptop Stand', 30, 45.00, '2023-03-12', 22),
    ('External Hard Drive', 15, 100.00, '2023-03-13', 23),
    ('Memory Card', 60, 25.00, '2023-03-14', 24),
    ('USB Hub', 35, 30.00, '2023-03-15', 25),
    ('Wireless Mouse', 40, 25.00, '2023-03-16', 26),
    ('Mechanical Keyboard', 20, 80.00, '2023-03-17', 27),
    ('Gaming Chair', 10, 300.00, '2023-03-18', 28),
    ('Monitor Arm', 15, 70.00, '2023-03-19', 29),
    ('Desk Lamp', 25, 40.00, '2023-03-20', 30)
]

cursor.executemany('''
    INSERT INTO sales (product_name, quantity, price, sale_date, customer_id)
    VALUES (?, ?, ?, ?, ?)
''', sales_data)

# Insert sample data into orders table
orders_data = [
    ('2023-01-15', 1, 6000.00),
    ('2023-01-16', 2, 510.00),
    ('2023-01-17', 3, 675.00),
    ('2023-02-01', 4, 4200.00),
    ('2023-02-02', 5, 20000.00),
    ('2023-02-03', 6, 1050.00),
    ('2023-02-04', 7, 1000.00),
    ('2023-02-05', 8, 5000.00),
    ('2023-02-06', 9, 2000.00),
    ('2023-02-07', 10, 1800.00)
]

cursor.executemany('''
    INSERT INTO orders (order_date, customer_id, total_amount)
    VALUES (?, ?, ?)
''', orders_data)

# Insert additional sample data into orders table
orders_data = [
    ('2023-03-01', 11, 7500.00),
    ('2023-03-02', 12, 6000.00),
    ('2023-03-03', 13, 6000.00),
    ('2023-03-04', 14, 9600.00),
    ('2023-03-05', 15, 4000.00),
    ('2023-03-06', 16, 3750.00),
    ('2023-03-07', 17, 8400.00),
    ('2023-03-08', 18, 2400.00),
    ('2023-03-09', 19, 4000.00),
    ('2023-03-10', 20, 2000.00),
    ('2023-03-11', 21, 2000.00),
    ('2023-03-12', 22, 1350.00),
    ('2023-03-13', 23, 1500.00),
    ('2023-03-14', 24, 1500.00),
    ('2023-03-15', 25, 1050.00),
    ('2023-03-16', 26, 1000.00),
    ('2023-03-17', 27, 1600.00),
    ('2023-03-18', 28, 3000.00),
    ('2023-03-19', 29, 1050.00),
    ('2023-03-20', 30, 1000.00)
]

cursor.executemany('''
    INSERT INTO orders (order_date, customer_id, total_amount)
    VALUES (?, ?, ?)
''', orders_data)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database 'your_database.db' updated successfully with unique data.")