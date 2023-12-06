"""This is a scraping program to get search result data on each kw"""

import datetime
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import pyrebase


# file name & path
now = datetime.datetime.today()
today = now.strftime("%Y%m%d_%H%M_%a")
month = f"{now:%b}"

input_dir_path = 'input_dir'
output_dir_path = 'output_dir'
input_file = f'{input_dir_path}/amazon_kwlist.csv'
save_path = 'search_data'  # save path on firebase

filename_sb = f"{today}_SB.csv"
filename_sp = f"{today}_SP.csv"
filename_og = f"{today}_OG.csv"
filename = [filename_sb, filename_sp, filename_og]
adname = ['SB', 'SP', 'OG']

# Chromedriver settings
options = Options()
options.add_argument('--incognito')
options.add_argument('--headless')
options.add_argument('--lang=ja')

driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
URL = "https://www.amazon.co.jp/ref=gno_logo?language=ja_JP/"

# Define how many times scrape for each keyword
search_times = 1

# Columns of dataframe
columns = ["date", "keyword", "repeat", "type", "rank", "ASIN", "Name"]

# xpath for scraping
sp_xpath = "//*[@data-component-type='sp-sponsored-result']/descendant::h2"
sp_asin_xpath = "//*[@data-component-type='sp-sponsored-result']" \
                "/../../../../div"
sb_xpath = "//*[@class='a-truncate-full a-offscreen']/../span"
sb_asin_xpath = "//*[@class='a-truncate-full a-offscreen']" \
                "/../../../../../div"
organic_xpath = "//*[@class='sg-col-4-of-12 s-result-item s-asin " \
                "sg-col-4-of-16 sg-col sg-col-4-of-20']/descendant::h2"
organic_asin_xpath = "//*[@class='sg-col-4-of-12 s-result-item s-asin " \
                     "sg-col-4-of-16 sg-col sg-col-4-of-20']"

# firebase info
config = {
    "apiKey": "AIzaSyB1qsOk2ppgS8fkSop4pJMN5dUqOxmOwIg",
    "authDomain": "kwsearch-23d25.firebaseapp.com",
    "databaseURL": "https://kwsearch-23d25-default-rtdb.firebaseio.com",
    "storageBucket": "kwsearch-23d25.appspot.com"
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()


def search_kw(kwd, URL, search_repeat):
    """Use chrome driver for scraping"""

    # Connect to internet
    driver.get(URL)
    driver.implicitly_wait(10)
    driver.refresh()
    driver.implicitly_wait(10)
    driver.maximize_window()
    driver.implicitly_wait(10)

    # Change lang setting to jp
    lang_button = driver.find_element_by_xpath \
        ("//*[@class='nav-icon nav-arrow null']")
    driver.implicitly_wait(10)
    lang_button.click()

    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)
    lang_select = driver.find_element_by_xpath \
        ("//*[@class='a-icon a-icon-radio']")

    driver.implicitly_wait(10)
    lang_select.click()

    driver.implicitly_wait(10)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)
    back_to_hp = driver.find_element_by_xpath \
        ("//*[@id='icp-btn-save-announce']/../../span")

    driver.implicitly_wait(10)
    back_to_hp.click()

    # Search keyword
    driver.implicitly_wait(10)
    driver.refresh()
    driver.implicitly_wait(10)
    driver.maximize_window()
    driver.implicitly_wait(10)

    time.sleep(5)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)
    searchbox = WebDriverWait(driver, 200).until(EC.element_to_be_clickable
                                                 ((By.ID,
                                                   "twotabsearchtextbox")))
    searchbox.send_keys(kwd)
    driver.find_elements_by_class_name("nav-input")[1].click()
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)

    # Scraping data
    sb = driver.find_elements_by_xpath(sb_xpath)
    sb_asin = driver.find_elements_by_xpath(sb_asin_xpath)
    sp = driver.find_elements_by_xpath(sp_xpath)
    sp_asin = driver.find_elements_by_xpath(sp_asin_xpath)
    organic = driver.find_elements_by_xpath(organic_xpath)
    organic_asin = driver.find_elements_by_xpath(organic_asin_xpath)

    title = str(kwd).replace("'", "").replace("[", "").replace("]", "")
    sb_list = []
    sp_list = []
    og_list = []

    rank = 0
    for (name, asin) in zip(sb, sb_asin):
        temp_list = [today, title, f"try_{search_repeat}", "SBA", str(rank + 1)]
        sb_name_data = name.text.replace(",", "")
        sb_asin_data = asin.get_attribute("data-asin")
        temp_list.append(str(sb_asin_data))
        temp_list.append(sb_name_data)
        sb_list.append(temp_list)
        rank += 1

    rank = 0
    for (name, asin) in zip(sp, sp_asin):
        temp_list = [today, title, f"try_{search_repeat}", "SPA", str(rank + 1)]
        sp_name_data = name.text.replace(",", "")
        sp_asin_data = asin.get_attribute("data-asin")
        if sp_asin_data is None:
            sp_asin_data = ""
        else:
            pass

        temp_list.append(sp_asin_data)
        temp_list.append(sp_name_data)
        sp_list.append(temp_list)
        rank += 1

    rank = 0
    for (name, asin) in zip(organic, organic_asin):
        temp_list = [today, title, f"try_{search_repeat}", "Organic", str(rank +
                                                                          1)]
        organic_result = name.text.replace(",", "")
        organic_asin = asin.get_attribute("data-asin")
        temp_list.append(organic_asin)
        temp_list.append(organic_result)
        og_list.append(temp_list)
        rank += 1

    return sb_list, sp_list, og_list


def get_data(csv):
    """Get search keyword data from CSV file"""

    items = []
    for l in open(csv):
        items.append(l)

    num_items = len(items)

    for i, line in enumerate(open(csv)):
        progress = int(i / num_items * 100)
        print(f'Getting results...: {progress}%', end='\r')
        yield line.strip().split(",")
    print()


def flatten_2d(data):
    """Flatten 3d list to 2d"""

    for block in data:
        for elem in block:
            yield elem


def make_list(l):
    """Convert raw scraping list to CSV optimized format"""

    flatten_list = list(flatten_2d(l))
    final_list = "\n".join(",".join(i) for i in flatten_list)
    return final_list


def write_csv(writing_list, filename):
    """Write CSV in output directory (in firebase as well)"""

    for num, (contents, name) in enumerate(zip(writing_list, filename)):
        with open(f'{output_dir_path}/{name}', "w") as f:
            f.write(contents)
            firebase_path = storage.child(f'{save_path}/{name}')
            firebase_path.put(f'{output_dir_path}/{name}')
            combine_data(adname[num], f'{output_dir_path}/{name}')


def combine_data(ad, scraped_file):
    """After checking if summary file is available, combine scraped data"""

    summed_file = f'Amazon_search_{ad}_{month}.csv'

    try:
        storage.child(summed_file).download(f'{output_dir_path}/{summed_file}')
        df = pd.read_csv(f'{output_dir_path}/{summed_file}',
                         encoding="utf_8",
                         header=None, names=columns, skiprows=1)
    except:
        df = pd.DataFrame(columns=columns)

    finally:
        adding_csv = pd.read_csv(scraped_file, encoding="utf_8", names=columns,
                                 header=None)
        combined_csv = df.append(adding_csv, ignore_index=True).dropna(
            how='all')
        combined_csv.to_csv(f'{output_dir_path}/{summed_file}')
        storage.child(f'{summed_file}').put \
            (f'{output_dir_path}/{summed_file}')


SB_list = []
SP_list = []
OG_list = []

current_repeat = 1
for kwd in get_data(input_file):
    while current_repeat < search_times + 1:
        sb_list, sp_list, og_list = search_kw(kwd, URL, current_repeat)
        SB_list.append(sb_list)
        SP_list.append(sp_list)
        OG_list.append(og_list)
        current_repeat += 1
    current_repeat = 1
driver.close()

writing_list = \
    [make_list(SB_list), make_list(SP_list), make_list(OG_list)]

write_csv(writing_list, filename)
print('Done Scraping')
