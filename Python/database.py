import sqlite3
from datetime import datetime, timezone

#Database name if it does not exist it will be created
DB_NAME = "airs_app.db"

def create_connection(database_name):
    """
    Create a connection to the database determined in the parameter.
    :param database_name: Database to generate the connection. (string)
    :return: Connection to the database.
    """
    connection = sqlite3.connect(database_name)
    #Foregin Keys need to be enabled in SQL lite
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

#Create tables
def create_tables(connection):
    """
    Create all needed tables for the database.
    :param connection: Connection to the database.
    :return: None
    """
    cursor = connection.cursor()
    cursor.executescript(""" 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            grade REAL NOT NULL,
            time_attempt TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
        
        CREATE TABLE IF NOT EXISTS user_progress(
            user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            average_grade REAL DEFAULT 0,
            attempt_count INTEGER DEFAULT 0,
            last_attempt TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, exercise_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
    """)
    connection.commit()
    cursor.close()

#Insertion operations
def add_user(connection, name):
    """
    Adds a new user passing the name and getting the time it was created and adds it to the database.
    :param connection: Connection to the database.
    :param name: Name of the user. (string)
    :return: None
    """
    try:
        cursor = connection.cursor()
        #So datetime.utcnow is going to be removed at some point so better to use the following code
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO users (name, created_at) VALUES (?, ?)",
                       (name, date))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Database Error: {err}")
    finally:
        #Cursors need to be closed, breaking news
        cursor.close()

def add_exercise(connection, name, description):
    """
    Adds a new exercise passing the name and a description of it to the database
    :param connection: Connection to the database.
    :param name: Name of the exercise. (string)
    :param description: Description of the exercise. (string)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO exercises (name, description) VALUES (?, ?)",
                       (name, description))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()

def add_grade(connection, user_id, exercise_id, grade):
    """
    Add a new grade as a result of an exercise for the desired user and updates the user progression.
    :param connection: Connection to the database.
    :param user_id: User id of the owner of the grade. (integer)
    :param exercise_id: Exercise id of the exercise attempted. (integer)
    :param grade: Grade obtained by the user. (float)
    :return: None
    """
    try:
        cursor = connection.cursor()
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO grades (user_id, exercise_id, grade, time_attempt) VALUES (?, ?, ?, ?)",
                    (user_id, exercise_id, grade, date))
        connection.commit()
        update_user_progression(connection, user_id, exercise_id, grade)
    except sqlite3.Error as err:
        print(f"Database Error: {err}")
    finally:
        cursor.close()

#SELECT operations
def get_users(connection):
    """
    Get all users from the database.
    :param connection: Connection to the database.
    :return: List containing the rows of the users table, otherwise an empty list if an error
    is encountered.
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()
    except sqlite3.Error as err:
        print(f"Error getting the users: {err}")
        return []
    finally:
        cursor.close()

def get_exercises(connection):
    """
    Get all exercises from the database.
    :param connection: Connection to the database.
    :return: List containing the rows of the exercises table, otherwise an empty list if an error
    is encountered.
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM exercises")
        return cursor.fetchall()
    except sqlite3.Error as err:
        print(f"Error getting the exercises: {err}")
        return []
    finally:
        cursor.close()

def get_grades_of_user(connection, user_id):
    """
    Get all the grades of the specified user.
    :param connection: Connection to the database.
    :param user_id: User id of the user which the grades are tied to. (integer)
    :return: List containing the grades of the specified user, otherwise an empty list if an error
    is encountered.
    """
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT exercises.name, grades.grade, grades.time_attempt
            FROM grades
            JOIN exercises ON grades.exercise_id = exercises.id
            WHERE grades.user_id = ?
            ORDER BY grades.time_attempt DESC
        """, (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as err:
        print(f"Error getting the grades of the user: {err}")
        return []
    finally:
        cursor.close()

def get_user_progress(connection, user_id):
    """
    Get the user progress.
    :param connection: Connection to the database.
    :param user_id: User id of the user progress being read. (integer)
    :return: Tuple containing the user progress including average grade, number of attempts and date of last attempt.
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, average_grade, attempt_count, last_attempt FROM user_progress WHERE user_id = ?",
                       (user_id,))
        return cursor.fetchone()
    except sqlite3.Error as err:
        print(f"Error getting the user progress: {err}")
        return ()
    finally:
        cursor.close()

#Delete operations
def remove_user(connection, user_id):
    """
    Removes the specified user from the database.
    :param connection: Connection to the database.
    :param user_id: User id of the user to be removed from the database. (integer)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM grades WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error removing user: {err}")
    finally:
        cursor.close()

def remove_exercise(connection, exercise_id):
    """
    Removes the specified exercise from the database.
    :param connection: Connection to the database.
    :param exercise_id: Exercise id of the exercise to be removed from the database. (integer)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM grades WHERE exercise_id = ?", (exercise_id,))
        cursor.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error removing exercise: {err}")
    finally:
        cursor.close()

def remove_grade(connection, grade_id):
    """
    Removes a single grade entry from the database.
    :param connection: Connection to the database.
    :param grade_id: Grade id of the grade to be removed from the database. (integer)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error removing grade: {err}")
    finally:
        cursor.close()

def remove_user_progress(connection, user_id):
    """
    Remove specified user progress.
    :param connection: Connection to the database.
    :param user_id: User ID whose progress is being deleted. (integer)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM user_progress WHERE user_id = ?", (user_id,))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error removing user progress: {err}")
    finally:
        cursor.close()

#Update operations
def update_user(connection, name, user_id):
    """
    Update the user's name.
    :param connection: Connection to the database.
    :param name: New name of the user to be changed in the database. (string)
    :param user_id: ID of the user which will change the name. (integer)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error updating user: {err}")
    finally:
        cursor.close()

def update_exercise(connection, exercise_id, name = None, description = None):
    """
    Update the information of exercise name and/or description.
    :param connection: Connection to the database.
    :param exercise_id: ID of the exercise which will be changed. (integer)
    :param name: New name of the exercise, default None. (string)
    :param description: New description of the exercise, default None. (string)
    :return: None
    """
    try:
        cursor = connection.cursor()
        #It can be done better but for now this works
        if name:
            cursor.execute("UPDATE exercise SET name = ? WHERE id = ?", (name, exercise_id))
        if description:
            cursor.execute("UPDATE exercise SET description = ? WHERE id = ?", (description, exercise_id))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error updating exercise: {err}")
    finally:
        cursor.close()

#So this function may not really need to even exist, but I will leave it just in case
def update_grades(connection, grade_id, grade):
    """
    Update the grade of the grade id specified.
    :param connection: Connection to the database.
    :param grade_id: ID of the grade to be changed. (integer)
    :param grade: New grade to be added. (float)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE grades SET grade = ? WHERE id = ?", (grade, grade_id))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error updating grade: {err}")
    finally:
        cursor.close()

def update_user_progression(connection, user_id, exercise_id, new_grade):
    """
    Update the user progression as a new grade is added.
    :param connection: Connection to the database.
    :param user_id: ID of the user. (integer)
    :param exercise_id: ID of teh exercise. (integer)
    :param new_grade: New grade to be added. (float)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT average_grade, attempt_count FROM user_progress WHERE user_id = ? AND exercise_id = ?",
                    (user_id, exercise_id))
        current_progress = cursor.fetchone()

        new_average, new_attempts = calculate_progress(current_progress, new_grade)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        if current_progress:
            cursor.execute("UPDATE user_progress SET average_grade = ?, attempt_count = ?, last_attempt = ? WHERE user_id = ? AND exercise_id = ?",
                        (new_average, new_attempts, date, user_id, exercise_id))
        else:
            cursor.execute("INSERT INTO user_progress (user_id, exercise_id, average_grade, attempt_count, last_attempt) VALUES (?, ?, ?, ?, ?)",
                        (user_id, exercise_id, new_average, new_attempts, date))
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error updating user progress: {err}")
    finally:
        cursor.close()

#Extra functions
def calculate_progress(progress, new_grade):
    """
    Calculates the new average of grades and new number of attempts according to the information provided.
    :param progress: Tuple that contains the old average and old number of attempts, gained from a query.
    :param new_grade: The new grade to be used in the calculations. (float)
    :return: A new average grade and a new number of attempts. (integer), (float)
    """
    old_average_grade, old_attempts = progress or (0,0) #Default 0 0 if None is passed
    new_attempts = old_attempts + 1
    new_average = ((old_average_grade * old_attempts) + new_grade) / new_attempts
    return new_average, new_attempts

#Debug functions
def drop_all_tables(connection):
    """
    Drop all tables existing in the database.
    :param connection: Connection to the database.
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.executescript("""
            DROP TABLE IF EXISTS grades;
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS exercises;
            DROP TABLE IF EXISTS user_progress;
        """)
        connection.commit()
    except sqlite3.Error as err:
        print(f"Error updating user progress: {err}")
    finally:
        cursor.close()

def debug_script(connection, query, values = None, fetch = False):
    """
    Executes any query desired as long as it is valid.
    :param fetch: If true it returns a fetched. (bool) Optional, defaults False
    :param values: Any values taken as a Tuple. Optional, defaults None
    :param connection: Connection to the database.
    :param query: query to be executed, can be any SQL query. (string)
    :return: None
    """
    try:
        cursor = connection.cursor()
        cursor.execute(query, values or ())
        if fetch:
            return cursor.fetchall #If anyone needs fetchone or fetchmany um just change this idk
    except sqlite3.Error as err:
        print(f"Error updating user progress: {err}")
        return None
    finally:
        cursor.close()

#Simple Testing
if __name__ == '__main__':
    #Creation
    conn = create_connection(DB_NAME)
    create_tables(conn)

    #Adding
    add_user(conn, "John")
    add_exercise(conn, "Test", "Testing insertion")
    add_grade(conn, 1, 1, 59)
    add_grade(conn, 1, 1, 54)
    add_grade(conn, 1, 1, 87)
    add_grade(conn, 1, 1, 45)

    #Print Results
    print("Users: ", get_users(conn))
    print("Exercise: ", get_exercises(conn))
    print("Grade for user 1: ", get_grades_of_user(conn, 1))
    print("User progression: ", get_user_progress(conn, 1))

    #Remove
    remove_grade(conn, 1)
    remove_user_progress(conn, 1)
    remove_exercise(conn, 1)
    remove_user(conn, 1)


    #Print Results
    print("Users: ", get_users(conn))
    print("Exercise: ", get_exercises(conn))
    print("Grade for user 1: ", get_grades_of_user(conn, 1))
    print("User progression: ", get_user_progress(conn, 1))



    conn.close()
