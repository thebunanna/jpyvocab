import sqlite3
import csv 
from datetime import datetime, timezone, timedelta
from fsrs import FSRS, Card, Rating, ReviewLog

con = sqlite3.connect("jpy.db")
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS card (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    due TIMESTAMP NOT NULL,
    stability FLOAT NOT NULL,
    difficulty FLOAT NOT NULL,
    elapsed_days INT NOT NULL,
    scheduled_days INT NOT NULL,
    reps INT NOT NULL,
    lapses INT NOT NULL,
    state INT NOT NULL,
    last_review TIMESTAMP,
    vocab_id INT NOT NULL,
    FOREIGN KEY (vocab_id) REFERENCES vocab(id)

);""")
cur.execute("""CREATE TABLE IF NOT EXISTS vocab (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(255) NOT NULL,
    hira VARCHAR(255) NOT NULL,
    translated TEXT NOT NULL
);""")
cur.execute("""CREATE TABLE IF NOT EXISTS sentence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sentence TEXT NOT NULL,
    word_id INT NOT NULL,
    FOREIGN KEY (word_id) REFERENCES word(id)
);""")

with open('n5_randomized.csv', 'r') as file:
    csv_reader = csv.reader(file)
    for ind, x in enumerate (csv_reader):
        # cur.execute("INSERT INTO card VALUES (:id, :due, :stability, :difficulty, :elapsed_days, :scheduled_days, :reps, :lapses, :state, :last_review)", 
        #             {"id": ind, **(Card(due=datetime.now() + timedelta(days=ind / 5), last_review=datetime.now()).to_dict())})
        cur.execute("INSERT INTO vocab (word, hira, translated) VALUES (?, ?, ?)", 
                    (x[0], x[1], x[2]))
cur.execute("INSERT INTO card (due, stability, difficulty, elapsed_days, scheduled_days, reps, lapses, state, last_review, vocab_id) \
            VALUES (:due, :stability, :difficulty, :elapsed_days, :scheduled_days, :reps, :lapses, :state, :last_review, :vocab_id)", 
                    {**(Card(due=datetime.now(timezone.utc), last_review=datetime.now(timezone.utc)).to_dict()), 'vocab_id' : 1 })
con.commit()
res = cur.execute("SELECT * FROM vocab")
print (res.fetchone())
con.close()