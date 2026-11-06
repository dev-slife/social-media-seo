"""
Author: dev.slife
Date Created: 10/16/2026
Date Updated: 11/6/2026
Description:
    A python script used to help clean and restructure social media and web traffic datasets.
"""


# ------------------------ IMPORTS ------------------------ #

import os
import csv
import json
import pandas as pd



# ------------------------ CONSTANTS ------------------------ #

RAW_DIR = "raw_data"
CLEAN_DIR = "clean_data"
OUTPUT_DIR = "output_data"
STAT_TABLES = "stat_tables"



# ------------------------ FILE OPERATIONS ------------------------ #

def output(name: str, data: list):
    path = os.path.join(OUTPUT_DIR, name + ".json")
    if (not os.path.exists(OUTPUT_DIR)):
        print(f"Path does not exist, creating one: {OUTPUT_DIR}")
        os.mkdir(OUTPUT_DIR)
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, sort_keys=True)
    return json.dumps(data, indent=4, sort_keys=True)


def read_csv(filename: str, raw: bool = True):
    dir = RAW_DIR if raw else CLEAN_DIR
    path = os.path.join(dir, filename)
    data = []
    if (os.path.exists(path)):
        with open(path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for line in reader:
                if not ('#' in str(line)):
                    data.append(line)
    else:
        print(f"Path does not exist: {path}")
    return data


def write_csv(name: str, data: list | dict | pd.DataFrame, include_index: bool = False, stat_tables: bool = False):
    root = STAT_TABLES if (stat_tables) else CLEAN_DIR
    path = os.path.join(root, name + ".csv")
    if (not os.path.exists(root)):
        print(f"Path does not exist, creating one: {root}")
        os.mkdir(root)
    df = pd.DataFrame(data) if (isinstance(data, list) or isinstance(data, dict)) else data
    df.to_csv(path, index=include_index)



# ------------------------ DATA FILTERING ------------------------ #

def filterCountry(country: str, data: dict):
    filtered = {}
    for i in range(len(data["Country"])):
        if (data["Country"][i] == country):
            for key in data.keys():
                filtered.setdefault(key, []).append(data[key][i])
    return filtered


def filterColumn(names: tuple, data: dict, remove: bool = True):
    filtered = {}
    for key in data.keys():
        if ((key not in names and remove) or (key in names and not remove)):
            filtered[key] = data[key]
    return filtered



# ------------------------ DATA RESTRUCTURING ------------------------ #

def structData(data: dict, column: str):
    columns_to_remove = ("Bio Link Taps", "Followers", "Stories Created", "Posts Created")
    links = {
        "Male": ["Female"],
        "Female": ["Male"],
        "Age 25-34": ["Age 35-44", "Age 45-54"],
        "Age 35-44": ["Age 25-34", "Age 45-54"],
        "Age 45-54": ["Age 25-34", "Age 35-44"]
    }
    filtered = filterColumn(columns_to_remove, data)
    newData = {}
    found, valid = column in filtered.keys(), filtered[column][0][-1] == '%'
    if (found and valid):
        for key in filtered.keys():
            if ((key == column) or (key in links.get(column, []))): continue
            for i in range(len(filtered[key])):
                dec = (float(filtered[column][i][0:(len(filtered[column][i]) - 1)])) / 100
                perc = True if (isinstance(filtered[key][i], str) and filtered[key][i][-1] == '%') else False
                val = (filtered[key][i][0:(len(filtered[key][i]) - 1)]) if (perc) \
                    else filtered[key][i]
                try:
                    res = str(round(float(val) * dec, 2)) + '%' if (perc) \
                        else round(float(val) * dec)
                    newData.setdefault(key, []).append(res)
                except ValueError:
                    newData.setdefault(key, []).append(val)
        return newData
    elif not found:
        print(f"Column not found: {column}")
    else:
        print(f"Column does not use percentages.")



# ------------------------ DATA BUILDING ------------------------ #

def map_data(raw_data: list):
    data_map = {}
    keys = None
    for i in range(len(raw_data)):
        if (i == 0):
            keys = [raw_data[0][j] for j in range(len(raw_data[0]))]
        else:
            for j in range(len(raw_data[i])):
                data_map.setdefault(keys[j], []).append(soft_to_number(raw_data[i][j]))
    return data_map



# ------------------------ STAT CALCULATIONS ------------------------ #

def soft_to_number(string):
    try:
        return float(string)
    except (ValueError, TypeError):
        return string
    

def stat_summary(data: dict, columns: list, output_name: str = None):
    df = pd.DataFrame(data)
    summary = df[columns].describe()
    print(summary)
    if (output_name):
        write_csv(output_name, summary, include_index=True, stat_tables=True)
    return summary


def avg_group(data: dict, group: list, stat_col: str, output_name: str = None):
    df = pd.DataFrame(data)
    dfGroup = df.groupby(group)[stat_col].mean()
    print(dfGroup)
    if (output_name):
        write_csv(output_name, dfGroup, include_index=True, stat_tables=True)
    return dfGroup


def corr_test(data: dict, output_name: str = None):
    df = pd.DataFrame(data)
    dfCorr = df.corr(numeric_only=True)
    print(dfCorr)
    if (output_name):
        write_csv(output_name, dfCorr, include_index=True, stat_tables=True)
    return dfCorr



# ------------------------ MAIN ------------------------ #

def main():
    columns_to_remove = ("Event count", "Key events", "User key event rate", "Total revenue", "Country")
    data_structures = ("Male", "Female", "Live In Baltimore", "Age 25-34", "Age 35-44", "Age 45-54")
    socialData = {
        "INSTAGRAM_RAW": map_data(read_csv("Instagram Web Data - Sheet1.csv"))
    }
    webData = {
        "AGE_DATA": map_data(read_csv("Demographic_details_Age.csv")),
        "CITY_DATA": map_data(read_csv("Demographic_details_City.csv")),
        "GENDER_DATA": map_data(read_csv("Demographic_details_Gender.csv")),
        "PAGES_DATA": map_data(read_csv("Pages_and_screens_Country.csv")),
        "USER_COUNTRY_DATA": map_data(read_csv("User_acquisition_Country.csv")),
        "USER_SESSION_DATA": map_data(read_csv("User_acquisition_Session_Source.csv"))
    }
    
    for d in data_structures:
        socialData["INSTAGRAM_" + d.upper()] = structData(socialData["INSTAGRAM_RAW"], d)
    for name, data in socialData.items():
        output(name, data)
        write_csv(name, data)
    for name, data in webData.items():
        webData[name] = filterColumn(columns_to_remove, filterCountry("United States", data))
    for name, data in webData.items():
        output(name, data)
        write_csv(name, data)
        
    stat_summary(socialData["INSTAGRAM_RAW"], ["Total Views", "Profile Visits"], "INSTAGRAM_STAT_SUMMARY")
    avg_group(socialData["INSTAGRAM_RAW"], ["Followers", "Bio Link Taps"], "Total Views", "INSTAGRAM_AVG_GROUP")
    corr_test(socialData["INSTAGRAM_RAW"], "INSTAGRAM_CORRELATION_TABLE")


if __name__ == "__main__":
    main()