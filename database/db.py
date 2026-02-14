import sqlite3
from config import DATABASE_PATH


def get_connection():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticket_type TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            origin TEXT,
            destination TEXT,
            date TEXT,
            price REAL NOT NULL,
            transaction_id TEXT NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_id TEXT NOT NULL,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    """)

    conn.commit()
    conn.close()


def save_user(name, email, phone, age=None):
    """Insert a new user and return the user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, phone, age) VALUES (?, ?, ?, ?)",
        (name, email, phone, age),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def save_booking(user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id):
    """Insert a new booking and return the booking_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO bookings (user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id),
    )
    conn.commit()
    booking_id = cursor.lastrowid
    conn.close()
    return booking_id


def save_payment(booking_id, amount, transaction_id, status="completed"):
    """Insert a payment record and return the payment_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payments (booking_id, amount, transaction_id, status) VALUES (?, ?, ?, ?)",
        (booking_id, amount, transaction_id, status),
    )
    conn.commit()
    payment_id = cursor.lastrowid
    conn.close()
    return payment_id


def get_booking_by_id(booking_id):
    """Fetch a single booking by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_receipt_data(booking_id):
    """Fetch full receipt data by joining users, bookings, and payments."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            b.id as booking_id, b.ticket_type, b.ticket_id, b.origin, b.destination,
            b.date, b.price, b.transaction_id, b.status, b.created_at,
            u.name as passenger_name, u.email, u.phone, u.age,
            p.amount as payment_amount, p.status as payment_status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        LEFT JOIN payments p ON p.booking_id = b.id
        WHERE b.id = ?
        """,
        (booking_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None
