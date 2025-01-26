import pandas as pd 
import random
import numpy as np
import requests
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
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

print("""
Welcome to Parlay Guesser for over or under. This is a basic machine learning model that helps users determine over
or under bets on certain stats. The data collected to make this possible was collected from NBA.com.
Make sure to enter the player's first name(SPELLING MATTERS) and their team(AGAIN 
SPELLING MATTERS), and the algorithm will do the rest to determine whether or not you should go over or under. 
""")

# initializing array data
playerPts, playerAsts, playerRebs = [], [], []

#getting user input
player = input("Enter the name of the player: ")
team = input("Enter the name of the team your player plays for: ")
stat = input("Which stat are you going to bet on: Points, Rebounds, or Assists: ")
overUnder = float(input("Enter the number to go over or under on: "))


# adds the chromedriver extension which has to be in the same location as the file using the object
service = Service(executable_path='chromedriver.exe')

# gets the driver object which allows you to surf the web
driver = webdriver.Chrome(service=service)

#gets navigation link
driver.get('https://www.nba.com/players')

# waits for the element to exist in the webpage before clicking on it
# WebDriverWait(driver, 5).until(
#     EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, player))
# )

# finds links from the text title
links = driver.find_elements(By.CLASS_NAME, 'DropDown_select__4pIg9')

# this is done to go through a scrollable part of the website
drop = Select(links[1])

# just to ensure no lag
time.sleep(3)

# picks your option from the scrollable portion
drop.select_by_visible_text(team)

# just to ensure no lag
time.sleep(3)

playerLinks = driver.find_elements(By.CLASS_NAME, 'RosterRow_playerFirstName__NYm50')
# just to ensure no lag
time.sleep(5)
'''
problem arises with the scrollview I need to fix later
'''
for i in range(len(playerLinks)):
    if playerLinks[i].text == player:
        playerLinks[i].click()
        break
    else:
        continue


# gets the current URL
htmlParser = requests.get(driver.current_url)

# closing the driver
driver.close()

# beautiful soup and requests web scraping
infoParser = bs(htmlParser.text, 'html.parser')
infoParser.find('table')

# algorithm for scraping the points
if stat == 'Points':
    for i in infoParser.find_all('tr'):
        pts = i.find_all('td')
        for t in range(len(pts)):
            if t == 4:
                playerPts.append(int(pts[t].text))
                break
            else:
                continue
    y = np.array(playerPts)

# algorithm for scraping assists
if stat == 'Assists':
    for i in infoParser.find_all('tr'):
        pts = i.find_all('td')
        for t in range(len(pts)):
            if t == 17:
                playerAsts.append(int(pts[t].text))
                break
            else:
                continue
    y = np.array(playerAsts)

# algorithm for scraping rebounds
if stat == 'Rebounds':
    for i in infoParser.find_all('tr'):
        pts = i.find_all('td')
        for t in range(len(pts)):
            if t == 16:
                playerRebs.append(int(pts[t].text))
                break
            else:
                continue
    y = np.array(playerRebs)


X = np.array([1, 2, 3, 4, 5])

# training and testing data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1, random_state=5)

# makes the array into 2D for the inputs because the inputs require to be 2D
# something is wrong with X_train as it loses a value for some reason
X_train = np.array(X_train).reshape(-1,1)

# X_test = np.array(X_test).reshape(-1,1)

# create linear regression object
lr = LinearRegression()


lr.fit(X_train, y_train)

# lr can start predicting output values given an input
y_predict = lr.predict(X_train)
X_train = X_train.flatten()
plt.xlabel("Game Number")
plt.ylabel(f"{stat}")
plt.scatter(X_train, y_train, color='black')
plt.plot(X_train, y_predict, color='b')
plt.show()
plt.close('Figure 1')

# getting a predicted estimate
parlayNum = lr.predict([[6]])
print(parlayNum)
if (parlayNum <= overUnder):
    print(f"My training data suggests that you go under on {overUnder}.")

else:
    print(f"My training data suggests you go over on {overUnder}.")