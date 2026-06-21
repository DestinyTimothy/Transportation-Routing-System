import mysql.connector
import os

# Get the directory where your script is located
basedir = os.path.abspath(os.path.dirname(__file__))

config = {
    'host': 'mysql-2c71e7dd-transportation-routing-system.b.aivencloud.com',
    'user': 'avnadmin',
    'password': 'AVNS_1eMahtoS1R0KOKxtla4',
    'database': 'defaultdb',
    'port': 14688,
    'ssl_ca': os.path.join(basedir, 'ca.pem') # This finds ca.pem wherever your code is running
}

try:
    conn = mysql.connector.connect(**config)
    print("Success! Connected to Aiven database.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")