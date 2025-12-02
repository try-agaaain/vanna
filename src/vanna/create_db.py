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

cursor.executemany('''
    INSERT INTO customers (name, email, phone, address)
    VALUES (?, ?, ?, ?)
''', customers_data)

# Insert sample data into sales table
sales_data = [
    ('Laptop', 5, 1200.00, '2023-01-15', 1),
    ('Mouse', 20, 25.50, '2023-01-16', 2),
    ('Keyboard', 15, 45.00, '2023-01-17', 3),
    ('Monitor', 8, 300.00, '2023-01-18', 1),
    ('Laptop', 3, 1200.00, '2023-01-20', 2),
    ('Headphones', 10, 80.00, '2023-01-21', 3)
]

cursor.executemany('''
    INSERT INTO sales (product_name, quantity, price, sale_date, customer_id)
    VALUES (?, ?, ?, ?, ?)
''', sales_data)

# Insert sample data into orders table
orders_data = [
    ('2023-01-15', 1, 6000.00),
    ('2023-01-16', 2, 510.00),
    ('2023-01-17', 3, 675.00)
]

cursor.executemany('''
    INSERT INTO orders (order_date, customer_id, total_amount)
    VALUES (?, ?, ?)
''', orders_data)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database 'your_database.db' created successfully with comprehensive data.")
