import sqlite3

class UniqueException(Exception):
    pass

class QueryFailed(Exception):
    pass

class DatabaseConnectionException(Exception):
    pass


class Weather(): # geniunely no idea what i'm doing
    __DB_LOCATION = "main.db"
    def __init__(self):
        # Initialize variable instances
        # They're all private shhh
        try:
            self.__db_connection = sqlite3.connect(self.__DB_LOCATION)
            self.__cur = self.__db_connection.cursor()
        except Exception as e:
            raise DatabaseConnectionException("Could not create connection to the database")

        #self.__db_connection.set_trace_callback(print) # for debugging
        self.__db_connection.set_trace_callback(None)

        # Create initial model, if doesn't exist
        self.__cur.execute("CREATE TABLE IF NOT EXISTS weather (discordID TEXT NOT NULL UNIQUE, discordUsername TEXT NOT NULL, location TEXT NOT NULL)")

    def __enter__(self):
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        # Handle exceptions properly when using context managers
        self.__cur.close()
        if isinstance(exc_value, Exception): # If an exception occured (?)
            self.__db_connection.rollback() # Rollback
        else:
            self.__db_connection.commit() # Else, commit and close
        self.__db_connection.close()

    def __del__(self):
        self.__db_connection.close()

    """ Create the initial database """
    # def create_model(self):
    #     self.__cur.execute('''CREATE TABLE IF NOT EXISTS weather
    #         (discordID TEXT NOT NULL UNIQUE, discordUsername TEXT NOT NULL, location TEXT NOT NULL)
    #     ''')

    """ Insert data into database """
    def insert_data(self, discordID, discordUsername, location):
        # Sanitize SQL input. The database is small, but this is good security practice
        # discordID must be 18 characters and only numbers
        if not str(discordID).isdecimal() and len(discordID) is not 18:
            raise Exception
        # discordUsername - yes, people might be able to input SQL injection queries in their username
        # sqlBadChars = [";", "'", "=", "\\"]
        # for badChar in sqlBadChars:
        #     discordUsername.replace(badChar, "")

        if None not in (discordID, discordUsername, location): # probably irrelevant
            try:
                self.__cur.execute("INSERT INTO weather VALUES (?, ?, ?)", (discordID, discordUsername, location)) # POSSIBLE SQL INJECTION VULN HERE. Sanitizing this input above
            except sqlite3.IntegrityError:
                raise UniqueException("Unique constraint failed, user already exists")
            print(f"[@] Inserted {discordID}, {discordUsername}, {location}")
        else:
            raise QueryFailed("Could not insert data. Parameters were null")

    def update_data(self, discordID, discordUsername, location):
        # Sanitize SQL input. The database is small, but this is good security practice
        # discordID must be 18 characters and only numbers
        if not str(discordID).isdecimal() and len(discordID) is not 18:
            raise Exception

        if None not in (discordID, discordUsername, location): # probably irrelevant
            self.__cur.execute("UPDATE weather SET discordUsername = ?, location = ? WHERE discordID = ?", (discordUsername, location, discordID)) # POSSIBLE SQL INJECTION VULN HERE. Sanitizing this input above
            print(f"[@] Updated {discordID}, {discordUsername}, {location}")
        else:
            raise QueryFailed("Could not update data. Parameters were null")

    """ Select data from the database """
    def select_data(self, discordID):
        self.__cur.execute("SELECT location FROM weather WHERE discordID=?", (discordID,))
        try:
            row = self.__cur.fetchall()[0]
        except IndexError:
            raise QueryFailed("Value does not exist")
            return
        return row[0]
