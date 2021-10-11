import sqlite3

def create_connection():
    try:
        DB = sqlite3.connect('main.db')
        return DB
    except Exception as e:
        print(e)
        return None
    return None

def create_model():
    if create_connection():
        CUR = create_connection().cursor()
        CUR.execute('''CREATE TABLE IF NOT EXISTS weather
            (discordID TEXT NOT NULL UNIQUE, discordUsername TEXT NOT NULL, location TEXT NOT NULL)
        ''')

        print("[!] DB model created. Commiting and exiting")
        create_connection().commit() # Commit changes and close the database connection
        create_connection().close()

def insert_data(discordID, discordUsername, location):
    # Sanitize SQL input. The database is small, but this is good security practice
    # discordID must be 18 characters and only numbers
    if not str(discordID).isdecimal() and len(discordID) is not 18:
        raise Exception
    # discordUsername - yes, people might be able to input SQL injection queries in their username
    # sqlBadChars = [";", "'", "=", "\\"]
    # for badChar in sqlBadChars:
    #     discordUsername.replace(badChar, "")

    if create_connection():
        CUR = create_connection().cursor()
        if None not in (discordID, discordUsername, location): # probably irrelevant
            try:
                CUR.execute("INSERT INTO weather VALUES (?, ?, ?)", (discordID, discordUsername, location)) # POSSIBLE SQL INJECTION VULN HERE. Sanitizing this input above
            except sqlite3.IntegrityError:
                print("Unique failed")
            print(f"[@] Inserted {discordID}, {discordUsername}, {location}")
        else:
            raise Exception
        create_connection().commit() # Commit changes and close the database connection
        create_connection().close()

def select_data(discordID):
    if create_connection():
        CUR = create_connection().cursor()
        CUR.execute("SELECT location FROM weather WHERE discordID=?", (discordID,))
        row = CUR.fetchall()[0]
        return row
