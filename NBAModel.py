import numpy as np
import mysql.connector
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

print("""
Parlay Guesser for over or under on NBA players. This is a basic machine learning model that helps determine over
or under bets on certain stats.  
""")
load_dotenv()
passwordEnv = os.getenv("PASSWORD")
databaseEnv = os.getenv("DATABASE")
# initializing array data for machine learning model
playerPts, playerAsts, playerRebs, gameNum, X = [], [], [], [], []
try:
    db = mysql.connector.connect(host='localhost', user='root', password=passwordEnv, database=databaseEnv)
    mycursor = db.cursor()
    # getting user input
    player = input("Enter the name of the player: ")
    stat = input("Which stat are you going to bet on: Points, Rebounds, or Assists: ").strip()
    overUnder = float(input("Enter the number to go over or under on: "))
    # dynamically resets all the data in the table 
    mycursor.execute(f'DROP TABLE IF EXISTS {player.split()[0].lower()}')
    # creates the player's data table
    mycursor.execute(f"CREATE TABLE {player.split()[0].lower()} (gameNum int, points int, rebounds int, assists int)")
    # adds the chromedriver extension which has to be in the same location as the file using the object
    service = Service(executable_path='/Users/johnydabbous/Desktop/Predictive-Betting-Model-for-NBA-Player-Statistics/chromedriver')
    # gets the driver object which allows you to surf the web
    driver = webdriver.Chrome()
    # gets navigation link
    driver.get('https://www.basketball-reference.com/players/')
    # paste here
    playerLetter = driver.find_element(By.LINK_TEXT, list(player.split()[1])[0])
    playerLetter.click()
    element = driver.find_element(By.LINK_TEXT, player)
    driver.execute_script("arguments[0].click();", element)
    season = driver.find_element(By.LINK_TEXT, '2024-25')
    driver.execute_script("arguments[0].click();", season)

    # gets the current URL
    htmlParser = requests.get(driver.current_url)

    # closing the driver
    driver.close()
    # beautiful soup and requests web scraping
    infoParser = bs(htmlParser.text, 'html.parser')
    tables = infoParser.find('table', {'class': 'stats_table sortable row_summable soc'})
    for x in tables.find_all('tr'):
        holder2 = x.text
        holder = str(x.text).split(" ")
        if 'Rk' in holder or 'Inactive' in holder or "Dress" in holder or 'Not' in holder:
            continue
        else:
            if '(OT)' in holder:
                holder.remove('(OT)')
            # done to get rid of the redundant last row
            if holder[2] == '':
                continue
        
        mycursor.execute(f'INSERT INTO {player.split()[0].lower()} (gameNum, points, rebounds, assists) VALUES (%s, %s, %s, %s)', (float(holder[1]), float(holder[33]), float(holder[27]), float(holder[28])))
    db.commit()

    # getting the point data from the player
    mycursor.execute(f'SELECT points FROM {player.split()[0].lower()}')
    for i in mycursor:
        playerPts.append(i[0])

    # getting the assist data from the player
    mycursor.execute(f'SELECT assists FROM {player.split()[0].lower()}')
    for i in mycursor:
        playerAsts.append(i[0])

    # getting the assist data from the player
    mycursor.execute(f'SELECT rebounds FROM {player.split()[0].lower()}')
    for i in mycursor:
        playerRebs.append(i[0])

    # assigning y to some array data 
    match stat:
        case "Points":
            y = playerPts
        case "Rebounds":
            y = playerRebs
        case "Assists":
            y = playerAsts
    # getting gameNum data from database
    mycursor.execute(f'SELECT gameNum FROM {player.split()[0].lower()}')
    for i in mycursor:
        X.append(i[0])

    # training and testing data
    # Assigns X_train to 80% of randomly selected points of data
    # Assigns X_test to the remaining 20% of the data points
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=13)

    # makes the array into 2D for the inputs because the inputs require to be 2D
    # something is wrong with X_train as it loses a value for some reason
    X_train = np.array(X_train).reshape(-1, 1)
    X_test = np.array(X_test).reshape(-1, 1)
    # create linear regression object
    lr = LinearRegression()
    lr.fit(X_train, y_train)

    # lr can start predicting output values given an input
    y_predict = lr.predict(X_train)
    X_train = X_train.flatten()
    plt.xlabel("Game Number")
    plt.ylabel(f"{stat}")
    plt.scatter(X_train, y_train, label='Training Data', color='black')
    plt.plot(X_train, y_predict, color='b', label='Linear Relation')
    plt.scatter(X_test, y_test, color='r', label='Testing Data')
    plt.legend()
    plt.show()
    # getting a predicted estimate
    parlayNum = lr.predict([[X[-1] + 1]])
    print(lr.score(X_test.reshape(-1,1), y_test))
    if (parlayNum <= overUnder):
        print(f"My training data suggests that you go under on {overUnder} given your over/under of {parlayNum}.")

    else:
        print(f"My training data suggests you go over on {overUnder} given your over/under of {parlayNum}.")
except:
    print("The stat line could not be predicted. Check your inputs.")

# currently trying to implement a decision trees regression model
# 3/6/25