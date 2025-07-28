import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
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
    
    #2017 WAC URL is slightly different
    #https://en.wikipedia.org/wiki/2017_World_Championships_in_Athletics_%E2%80%93_Men%27s_decathlon
   
    headers = {"User-Agent": "Mozilla/5.0"}
    
    event_names = ["100 metres", "Long jump", "Shot put", "High jump", "400 metres",
        "110 hurdles", "Discus", "Pole vault", "Javelin", "1500 metres"]
    athletes_data = {}
    years = [2016,2017,2019,2020,2022,2023,2024]
    for year in years:
        print(year)
        if year == 2017:
            url = f"https://en.wikipedia.org/wiki/2017_World_Championships_in_Athletics_%E2%80%93_Men%27s_decathlon"
            competition = "World Athletics Championship"
        elif year in {2016,2020,2024}:
            url = f"https://en.wikipedia.org/wiki/Athletics_at_the_{year}_Summer_Olympics_%E2%80%93_Men%27s_decathlon"
            competition = "Olympics"
        else:
            url = f"https://en.wikipedia.org/wiki/{year}_World_Athletics_Championships_%E2%80%93_Men%27s_decathlon"
            competition = "World Athletics Championships"
        
        response = requests.get(url, headers = headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        athletes_data = Make_Competition_Data(event_names, soup, athletes_data, year, competition)

    df = pd.DataFrame.from_dict(athletes_data, orient='index')
    df = df.reset_index().rename(columns={'index': 'Name'})
    df = Add_Points(df)
    df.to_csv("dec_data.csv", mode='w', index=False)
    
def Make_Competition_Data(event_names, soup, athletes_data, year, competition):
    tables = soup.find_all("table", class_=lambda x: x and "wikitable sortable" in x)

    for num, table in enumerate(tables[:-1]):
        print(num)
        for row in table.tbody.find_all("tr"):
            results = row.find_all("td")
            if len(results) < 3:
                continue
            
            name = None
            for td in results:
                if td.get("align") == "left":
                    name = td.get_text(strip=True)
                    break
            if not name:
                raise ValueError("There is no name")
            
            #Adam's name has middle name in only 1 event (1500m 2016 Olympics)
            if name == "Adam Sebastian Helcelet":
                name = "Adam Helcelet"
        
            print(name)
            if num in {0, 4, 5, 9}:
                score = Scrape_Track(results)
            elif num in {3, 7}:
                score = Scrape_HighJump_Vault(results)
            else:
                score = Scrape_Field(results)
            name = f"{name} {year} {competition}"
            
            if name not in athletes_data:
                athletes_data[name] = {}
            athletes_data[name][event_names[num]] = score
    return athletes_data
    
def Scrape_Track(list):
    global previous
    
    score = None
    for i, cell in enumerate(list[:-2]):
        if cell.get("align") == "left" and list[i+1].get("align") == "left":
            score = list[i+2].get_text(strip=True)
            break
    
    if score in {"NM", "DQ", "DNF", "DNS", "DNS1"}:
        return None
        
    #Later technology has times as 3 decimal places for ties with [14.167]
    if "[" in score:
        score = re.match(r"^(\d+\.\d+)\[", score).group(1)
    
    #1500m
    if ":" in score:
        seconds = float(score[0])*60
        seconds = seconds + float(score[2:])
        previous = seconds
        #print (seconds)
        return seconds
    
    #check for ties
    if not score or "." not in score:
        score = previous
        print("___________________________________________________________")
    
    previous = float(score)
    return float(score)
    
def Scrape_Field(list):
    for cell in list:
        if cell.get_text(strip=True) in {"NM", "DQ", "DNF", "DNS", "DNS1"}:
            return 0
        if cell.find("b"):
            return float(cell.find("b").get_text(strip=True))
    raise ValueError("No rows found in the table!")
    
def Scrape_HighJump_Vault(list):
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

'''
 --- Functions to calculate total score ---
I couldve put it in the scraper and scraped the last table but the table excludes nonfinishers
'''
def Add_Points(df):
    points_all = []
    for index, athlete in df.iterrows():
        point = 0
        print(athlete.Name)
        for num in range(1,11):
            if pd.isna(athlete.iloc[num]) or athlete.iloc[num] == 0:
                pass
            elif num in {1,5,6,10}:
                point = point + Calculate_Track(num,athlete.iloc[num])
            else:
                point = point + Calculate_Field(num,athlete.iloc[num])
        points_all.append(point)
    df["Total Points"] = points_all
    return df
    
def Calculate_Track(num, event_score):
    print(num,event_score)
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
    print(num, event_score)
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

Scrape_Wikipedia()
#Clean_Data()
#Add_Points()
#Scrape_Wikipedia_2017()
    