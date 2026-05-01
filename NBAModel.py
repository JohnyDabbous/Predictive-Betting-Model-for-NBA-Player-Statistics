import numpy as np
import mysql.connector
import sys
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from selenium.webdriver.common.by import By
from seleniumbase import Driver

print("""
Parlay Guesser for over or under on NBA players. This is a basic machine learning model that helps determine over
or under bets on certain stats.  
""")

load_dotenv()
passwordEnv = os.getenv("PASSWORD")
databaseEnv = os.getenv("DATABASE")

playerPts, playerAsts, playerRebs, PR, PA, RA, PRA, gameNum, X = [], [], [], [], [], [], [], [], []

db = mysql.connector.connect(host='localhost', user='root', password=passwordEnv, database=databaseEnv)
mycursor = db.cursor()

player = input("Enter the name of the player: ")
stat = input("Which stat are you going to bet on: Points, Rebounds, Assists, PR, PA, RA, PRA: ").strip()
overUnder = float(input("Enter the number to go over or under on: "))

mycursor.execute(f'DROP TABLE IF EXISTS {player.split()[0].lower()}')
mycursor.execute(f"CREATE TABLE {player.split()[0].lower()} (gameNum int, points int, rebounds int, assists int, pr int, pa int, ra int, pra int)")

# ── Cloudflare-safe driver ──────────────────────────────────────────────────
driver = Driver(uc=True, headless=False)

try:
    driver.get('https://www.basketball-reference.com/players/')

    # uc_click is SeleniumBase's human-like click that bypasses bot checks
    playerLetter = driver.find_element(By.LINK_TEXT, list(player.split()[1])[0].upper())
    driver.uc_click(playerLetter)

    element = driver.find_element(By.LINK_TEXT, player)
    driver.uc_click(element)

    season = driver.find_element(By.LINK_TEXT, '2025-26')
    driver.uc_click(season)

    # Grab page source directly — no separate requests.get() needed
    page_source = driver.page_source
    current_url = driver.current_url

finally:
    driver.quit()  # Always close, even on error
# ───────────────────────────────────────────────────────────────────────────

infoParser = bs(page_source, 'html.parser')
tables = infoParser.find('table', {'class': 'stats_table sortable row_summable soc'})

for x in tables.find_all('tr'):
    holder = str(x.text).split(" ")
    if 'Rk' in holder or 'Inactive' in holder or "Dress" in holder or 'Not' in holder:
        continue
    else:
        if '(OT)' in holder:
            holder.remove('(OT)')
        if holder[2] == '':
            continue

    mycursor.execute(
        f'INSERT INTO {player.split()[0].lower()} (gameNum, points, rebounds, assists, pr, pa, ra, pra) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (
            float(holder[1]),
            float(holder[33]),
            float(holder[27]),
            float(holder[28]),
            float(holder[33]) + float(holder[27]),
            float(holder[33]) + float(holder[28]),
            float(holder[27]) + float(holder[28]),
            float(holder[33]) + float(holder[27]) + float(holder[28])
        )
    )
db.commit()

# ── Pull stats from DB ──────────────────────────────────────────────────────
for col, arr in [('points', playerPts), ('assists', playerAsts), ('rebounds', playerRebs),
                 ('pr', PR), ('pa', PA), ('ra', RA), ('pra', PRA)]:
    mycursor.execute(f'SELECT {col} FROM {player.split()[0].lower()}')
    arr.extend(i[0] for i in mycursor)

match stat:
    case "Points":    y = playerPts
    case "Rebounds":  y = playerRebs
    case "Assists":   y = playerAsts
    case "PR":        y = PR
    case "PA":        y = PA
    case "RA":        y = RA
    case "PRA":       y = PRA

mycursor.execute(f'SELECT gameNum FROM {player.split()[0].lower()}')
X.extend(i[0] for i in mycursor)

# ── ML model ───────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=13)
X_train = np.array(X_train).reshape(-1, 1)
X_test  = np.array(X_test).reshape(-1, 1)

lr = LinearRegression()
lr.fit(X_train, y_train)
y_predict = lr.predict(X_train)

X_train_flat = X_train.flatten()
plt.xlabel("Game Number")
plt.ylabel(f"{stat}")
plt.scatter(X_train_flat, y_train, label='Training Data', color='black')
plt.plot(X_train_flat, y_predict, color='b', label='Linear Relation')
plt.scatter(X_test, y_test, color='r', label='Testing Data')
plt.legend()
plt.show()

parlayNum = lr.predict([[X[-1] + 1]])
print(f"Model score: {lr.score(X_test.reshape(-1, 1), y_test):.3f}")

if parlayNum <= overUnder:
    print(f"My training data suggests you go UNDER on {overUnder} (predicted: {parlayNum[0]:.1f}).")
else:
    print(f"My training data suggests you go OVER on {overUnder} (predicted: {parlayNum[0]:.1f}).")