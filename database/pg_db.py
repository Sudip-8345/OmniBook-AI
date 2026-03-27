import psycopg2
from psycopg2.extras import DictCursor
from config import DB_CONFIG # Assuming you move to a dict with host, dbname, user, password

def get_connection():
    """Get a Postgres connection with dictionary cursor enabled."""
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    with conn.cursor() as cursor:
        # Use SERIAL for auto-incrementing IDs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                ticket_type TEXT NOT NULL,
                ticket_id TEXT NOT NULL,
                origin TEXT,
                destination TEXT,
                date TEXT,
                price DECIMAL(10, 2) NOT NULL,
                transaction_id TEXT NOT NULL,
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                booking_id INTEGER NOT NULL REFERENCES bookings(id),
                amount DECIMAL(10, 2) NOT NULL,
                transaction_id TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()

def save_user(name, email, phone, age=None):
    """Insert a new user and return the user_id using RETURNING."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (name, email, phone, age) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, email, phone, age),
        )
        user_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return user_id

def save_booking(user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id):
    """Insert a new booking and return the booking_id."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO bookings (user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id),
        )
        booking_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return booking_id

def save_payment(booking_id, amount, transaction_id, status="completed"):
    """Insert a payment record and return the payment_id."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO payments (booking_id, amount, transaction_id, status) VALUES (%s, %s, %s, %s) RETURNING id",
            (booking_id, amount, transaction_id, status),
        )
        payment_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return payment_id

def get_booking_by_id(booking_id):
    """Fetch a single booking by ID as a dictionary."""
    conn = get_connection()
    # Using DictCursor to mimic sqlite3.Row behavior
    with conn.cursor(cursor_factory=DictCursor) as cursor:
        cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_receipt_data(booking_id):
    """Fetch full receipt data by joining users, bookings, and payments."""
    conn = get_connection()
    with conn.cursor(cursor_factory=DictCursor) as cursor:
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
            WHERE b.id = %s
            """,
            (booking_id,),
        )
        row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None