import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import time
import random
import os
import re
import math

def Scrape_Wikipedia():
    #https://en.wikipedia.org/wiki/Athletics_at_the_2024_Summer_Olympics_%E2%80%93_Men%27s_decathlon
    #https://en.wikipedia.org/wiki/Athletics_at_the_2020_Summer_Olympics_%E2%80%93_Men%27s_decathlon
    #https://en.wikipedia.org/wiki/Athletics_at_the_2016_Summer_Olympics_%E2%80%93_Men%27s_decathlon
    
    #https://en.wikipedia.org/wiki/2023_World_Athletics_Championships_%E2%80%93_Men%27s_decathlon
    #https://en.wikipedia.org/wiki/2022_World_Athletics_Championships_%E2%80%93_Men%27s_decathlon
    #https://en.wikipedia.org/wiki/2019_World_Athletics_Championships_%E2%80%93_Men%27s_decathlon
    #https://en.wikipedia.org/wiki/2017_World_Championships_in_Athletics_%E2%80%93_Men%27s_decathlon
   
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    event_names = [
        "100 metres", "Long jump", "Shot put", "High jump", "400 metres",
        "110 hurdles", "Discus", "Pole vault", "Javelin", "1500 metres"
    ]
    athletes = {}
    years = [2016,2019,2020,2022,2023,2024]
    for year in years:
        print(year)
        if year in {2016,2020,2024}:
            url = f"https://en.wikipedia.org/wiki/Athletics_at_the_{year}_Summer_Olympics_%E2%80%93_Men%27s_decathlon"
            competition = "Olympics"
        else:
            url = f"https://en.wikipedia.org/wiki/{year}_World_Athletics_Championships_%E2%80%93_Men%27s_decathlon"
            competition = "World Athletics Championships"
        if year == 2017:
            url = "https://en.wikipedia.org/wiki/2017_World_Championships_in_Athletics_%E2%80%93_Men%27s_decathlon"
            competition = "World Athletics Championship"
        
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        tables = soup.find_all("table", class_=lambda x: x and "wikitable sortable" in x)
        
        for num, table in enumerate(tables[:-1]):
            print(num)
            for row in table.tbody.find_all("tr"):
                results = row.find_all("td")
                if len(results) < 3:
                    continue
                #check for ties
                
                name_cell = results[2]
                name = name_cell.get_text(strip=True)
                if " " not in name or "(" in name or name == "Czech Republic" or name == "United States":
                    name_cell = results[1]
                    name = name_cell.get_text(strip=True)
                print(name)
                if num in {0, 4, 5, 9}:
                    score = ScrapeTrack(results)
                elif num in {3, 7}:
                    score = ScrapeHighJumpVault(results)
                else:
                    score = ScrapeField(results)
                name = f"{name} {year} {competition}"
                if name not in athletes:
                    athletes[name] = {}
                athletes[name][event_names[num]] = score

    
    df = pd.DataFrame.from_dict(athletes, orient='index')
    df = df.reset_index().rename(columns={'index': 'Name'})
    header = not os.path.exists("dec_data.csv")
    df.to_csv("dec_data.csv", mode='a', header=header, index=False)

def Scrape_Wikipedia_2017():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    event_names = [
        "100 metres", "Long jump", "Shot put", "High jump", "400 metres",
        "110 hurdles", "Discus", "Pole vault", "Javelin", "1500 metres"
    ]
    athletes = {}
    year = 2017
    url = "https://en.wikipedia.org/wiki/2017_World_Championships_in_Athletics_%E2%80%93_Men%27s_decathlon"
    competition = "World Athletics Championship"
    
    response = requests.get(url, headers = headers)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", class_=lambda x: x and "wikitable sortable" in x)
    
    for num, table in enumerate(tables[:-1]):
        print(num)
        for row in table.tbody.find_all("tr"):
            results = row.find_all("td")
            if len(results) < 3:
                continue
            #check for ties
            
            '''
            if " " not in name or "(" in name or name == "Czech Republic" or name == "United States":
                name_cell = results[1]
                name = name_cell.get_text(strip=True)
            '''
            
            if num in {0, 4, 5, 9}:
                if num == 0:
                    name_cell = results[3]
                elif num == 4 or num == 5:
                    name_cell = results[2]
                elif num == 9:
                    name_cell = results[1]
                name = name_cell.get_text(strip=True)
                print(name)
                score = ScrapeTrack(results)
            elif num in {3, 7}:
                for i, tag in enumerate(results):
                    if tag.text.strip() in {"A", "B"}:
                        name_cell = results[i+1]
                name = name_cell.get_text(strip=True)
                print(name)
                score = ScrapeHighJumpVault(results)
            else:
                name_cell = results[2]
                name = name_cell.get_text(strip=True)
                print(name)
                score = ScrapeField(results)
            name = f"{name} {year} {competition}"
            if name not in athletes:
                athletes[name] = {}
            athletes[name][event_names[num]] = score

    df = pd.DataFrame.from_dict(athletes, orient='index')
    df = df.reset_index().rename(columns={'index': 'Name'})
    header = not os.path.exists("dec_data.csv")
    df.to_csv("dec_data2.csv", mode='a', header=header, index=False)


#most of the conditionals are unneccsary and could have
#been formatted much cleaner
def ScrapeTrack(list):
    global previous
    try:
        score = list[5].get_text(strip=True)
    #if exact tie
    except:
        return previous
    
    if len(list[3].get_text(strip=True)) == 7:
        score = list[3].get_text(strip=True)
        seconds = float(score[0])*60
        seconds = seconds + float(score[2:])
        previous = seconds
        #print (seconds)
        return seconds
    
    if "[" in score:
        # Extract the main score (before the bracket)
        main_score = re.match(r"^(\d+\.\d+)\[", score).group(1)
        return float(main_score)
    if score in {"NM", "DQ", "DNF", "DNS", "DNS1"}:
        return None
    if not score:
        return None
    if "." not in score:
        score = list[4].get_text(strip=True)
    if score in {"NM", "DQ", "DNF", "DNS", "DNS1"}:
        return None
    if "." not in score:
        score = list[3].get_text(strip=True)
    #if minutes
    if ":" in score:
        seconds = float(score[0])*60
        seconds = seconds + float(score[2:])
        previous = seconds
        #print (seconds)
        return seconds
    previous = float(score)
    return float(score)
    
def ScrapeField(list):
    #iterates through td
    for cell in list:
        if cell.get_text(strip=True) in {"NM", "DQ", "DNF", "DNS"}:
            return 0
        if cell.find("b"):
            return float(cell.find("b").get_text(strip=True))
    raise ValueError("No rows found in the table!")
    
def ScrapeHighJumpVault(list):
    global previousHJV
    try:
        for cell in list:
            if cell.get_text(strip=True) == "0" or "." in cell.get_text(strip=True) and len(cell.get_text(strip=True)) == 4:
                score = float(cell.get_text(strip=True))
                previousHJV = score
                return score
            if cell.get_text(strip=True) in {"NM", "DQ", "DNF", "DNS"}:
                previousHJV = 0.0
                return 0.0
        raise ValueError("No rows found in the table!")
    except:
        return previousHJV

def Clean_Data():
    df = pd.read_csv("dec_data2.csv")
    df = df.replace(0.0, np.nan)
    df_clean = df.dropna(how="any")
    df_clean.to_csv("dec_data2_clean.csv")

'''
 --- Functions to calculate total score ---
I couldve put it in the scraper and scraped the last table but I didnt wanna
'''
def Add_Points():
    df = pd.read_csv("dec_data2_clean.csv", index_col='Name')
    points_all = []
    for index, athlete in df.iterrows():
        point = 0
        for num in range(1,11):
            if num in {1,5,6,10}:
                point = point + Calculate_Track(num,athlete.iloc[num])
            else:
                #print(athlete.name,num,athlete.iloc[num])
                point = point + Calculate_Field(num,athlete.iloc[num])
        points_all.append(point)
    df["Total Points"] = points_all
    df.to_csv("dec_final_data2.csv")
    
def Calculate_Track(num, event_score):
    if num == 1:
        A = 25.4347
        B=18
        C=1.81
    if num == 5:
        A=1.53775
        B=82
        C=1.81
    if num == 6:
        A=5.74352
        B=28.5
        C=1.92
    if num == 10:
        A=0.03768
        B=480
        C=1.85
    points = math.floor(A * (B - event_score) ** C)
    return points
      
def Calculate_Field(num, event_score):
    #cm
    if num == 2:
        event_score = event_score * 100
        A=0.14354
        B=220
        C=1.4
    #m
    if num == 3:
        A=51.39
        B=1.5
        C=1.05
    #cm
    if num == 4:
        event_score = event_score * 100
        A=0.8465
        B=75
        C=1.42
    if num == 7:
        A=12.91
        B=4
        C=1.1
    #cm
    if num == 8:
        event_score = event_score * 100
        A=0.2797
        B=100
        C=1.35
    if num == 9:
        A=10.14
        B=7
        C=1.08
    points = math.floor(A * (event_score-B) ** C)
    return points

#Scrape_Wikipedia()
#Clean_Data()
Add_Points()
#Scrape_Wikipedia_2017()
    