from barcode import UPCA, EAN13
from barcode.writer import ImageWriter
import random
import sqlite3

# print to an actual file:

test_num = random.randint(10000000000, 99999999999)
test_num = str(test_num)

def make_barcode_image(item_name):
    string_test = "{}.jpeg".format(item_name)
    with open(string_test, 'wb') as f:
        UPCA(test_num, writer=ImageWriter()).write(f)


# to convert the barcode image to binary data

def convertToBinaryData(filename):

    with open(filename, 'rb') as file:
        blobData = file.read()

    return blobData

# convertToBinaryData("milk.jpeg")

# inserting the barcode into the table

def insertBLOB(empId, name, barcode):
    try:
        sqliteConnection = sqlite3.connect('test.db')
        cur = sqliteConnection.cursor()
        print("Connected to SQLite")
        sqlite_insert_blob_query = """ INSERT INTO new_employee
                                        (empId, name, barcode) VALUES (?, ?, ?)"""

        empBarcode = convertToBinaryData(barcode)

        # Convert data into tuple format

        data_tuple = (empId, name, empBarcode)
        cur.execute(sqlite_insert_blob_query, data_tuple)
        sqliteConnection.commit()
        print("Successful insert")
        cur.close()

    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)

    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("the sqlite connection is closed")




# insertBLOB(2, "Andrea", "bubbie.jpeg")
