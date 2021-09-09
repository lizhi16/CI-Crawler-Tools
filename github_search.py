# This script used to get the list of github repo address
# which contains the DevOps platforms' config files
import requests
import time
import json
import sys
from bs4 import BeautifulSoup
from selenium import webdriver

# the keywords for searching
keyword = ".travis.yml"

# save path for the list 
path = "./repoList_travis_2021.txt"

address = "https://github.com/search?l=&p={}&q=filename%3A" +  keyword + "+path%3A%2F+size%3A{}..{}&ref=advsearch&s=indexed&type=Code"

#driver = webdriver.Firefox(executable_path = "/N/u/zli10/Carbonate/malicious_dockerfile/bin/geckodriver")
driver = webdriver.Firefox()
driver.maximize_window()
session = requests.session()
def login(account, password):
    global driver, session
    driver.get('https://github.com/login')
    time.sleep(2)
    driver.find_element_by_id('login_field').send_keys(account)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_xpath('//input[@class="btn btn-primary btn-block js-sign-in-button"]').click()

    # waiting for verification code
    #time.sleep(60)

    cookie = driver.get_cookies()
    driver.quit()

    ck = requests.cookies.RequestsCookieJar()
    #add cookie to CookieJar
    for i in cookie:
        ck.set(i["name"], i["value"])
    #update cookie in session
    session.cookies.update(ck)

# get the list of searching results
def resolve_github_list(startSize, endSize):
    # save the searching results
    projectList = open(path, "a+")

    page = 1
    totalPage = 100
    while page <= totalPage:
        url = address.format(str(page), startSize, endSize)
        print ("Index-", page, ": ", url)

        content = session.get(url)
        soup = BeautifulSoup(content.text,'html.parser')

        if page == 1:
            # Get correct total page numbers from reqeusts
            try:
                totalPage = int(soup.find('em', class_="current")['data-total-pages'])
                print ("[INFO] total pages: ", totalPage)
            except Exception as e:
                if int(endSize) - int(startSize) <= 1:
                    totalPage = 100
                else:
                    print ("Can't get the total pages!")
                    totalPage = 1
                #return None

        links = soup.find_all('div',class_="f4 text-normal")
        for link in links:
            project = link.find('a')

            projectConfig = str(project['title'].encode("utf-8"))
            # TODO: judge the title if it fits the keywords
            if keyword in projectConfig:
                link = "https://github.com" + str(project['href'])
                projectList.write(link + "\n")

        if content.status_code == 429:
            page = page - 1
            print ("[WARN] We get the 429, sleeping 60s")
            time.sleep(60)

        page = page + 1
        time.sleep(3)

    projectList.close()

def search_results_numbers(startSize, endSize):
    url = address.format("1", startSize, endSize)

    links = []
    flag = 5
    while len(links) == 0 and flag > 0:
        content = session.get(url)
        soup = BeautifulSoup(content.text,'html.parser')
        links = soup.find_all('h3')
        flag = flag - 1

    for link in links:
        # "Showing *** available code results" means useful info
        if "code results" in link.text:
            number = str(link.text).split()[0].strip().replace(" ", "")
            print ("number: ", number)
            # if results over 1000, it will show "1,000"
            if "," in number:
                print ("if: ", number)
                if int(endSize) - int(startSize) == 1:
                    return 1000
                return 0
            else:
                print ("else: ", number)
                return int(number)
        elif "We couldn't find any code matching" in link.text:
            return -1

    print("url is ", url, links)
    return -2

def determine_search_steps(startSize, endSize, stopFlag):
    # determine the number of results
    status = search_results_numbers(startSize, endSize)

    # couldn't find any code matching
    if status == -1 and startSize < stopFlag:
        print("[test] couldn't find any code matching")
        tmpSize = endSize
        result = -1
        while tmpSize <= stopFlag and result <= 0:
            tmpSize = int(tmpSize*2)
            result = search_results_numbers(startSize, tmpSize)

        if tmpSize > stopFlag:
            return 0, 0 

        return startSize, tmpSize

    # links is null
    if status == -2:
        print ("Search done.")
        return 0, 0

    # need to reduce the searching range
    if status == 0:
        print("[test] status == 0")
        tmpSize = endSize
        result = -1
        while tmpSize > (startSize + 1) and result <= 0:
            tmpSize = int(tmpSize/2)
            result = search_results_numbers(startSize, tmpSize)

        if tmpSize < startSize + 1:
            tmpSize = startSize + 1

        return startSize, tmpSize

    if status < 100 and status > 0:
        tmpSize = int(endSize*2)
        result = search_results_numbers(startSize, tmpSize)

        if result > 0:
            return startSize, tmpSize

        return startSize, endSize

    return startSize, endSize

def main():
    # login
    login("ccs2021001@protonmail.com", "Lizhi906096237")
    #login("ccs202003@protonmail.com", "Lizhiccs202003")

    startSize = 14
    step = 100
    stopFlag = 100000
    while startSize <= stopFlag:
        endSize = startSize + step
        start, end = determine_search_steps(startSize, endSize, stopFlag)
        if start == 0 and end == 0:
            print ("[INFO] Stopping crawler...")
            break
        
        print ("start in while", start, (end - start), end)

        if end <= start:
            print ("[ERR] ERR happend end < start: ", start, end)
            end = start + 1
        
        resolve_github_list(start, end)
        startSize = end + 1

if __name__ == '__main__':
    main()
    driver.quit()
