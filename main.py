import requests
from bs4 import BeautifulSoup
import datetime
from contest import Contest
import pandas as pd
import xlsxwriter
import warnings
warnings.filterwarnings("ignore")

def office_comp(usr_txt):
    u_items = usr_txt.splitlines()
    return '\n'.join(u_items)

requested_date=input('Введите дату по UTC в формате dd.mm.yyyy: \n')
contests_rows = list()
contests = list()
requested_contests=list()
URL = "https://codeforces.com/contests?locale=ru"
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
page_indexes = soup.find_all("span", class_="page-index")
last_page_index = int(page_indexes[len(page_indexes)-1].text)
current_table = soup.find("div", class_="datatable")
current_table_rows = current_table.find_all("tr")
for i in range(0, len(current_table_rows)):
    tds = current_table_rows[i].find_all("td")
    if(len(tds)>0):
        name = tds[0].text.replace("\n", "")
        date = datetime.datetime.strptime(tds[2].text.split('\n')[2], '%d.%m.%Y %H:%M').strftime('%d.%m.%Y')
        contest = Contest(name, date, None)
        contests.append(contest)
        if(contest.date==requested_date):
            requested_contests.append(contest)

for i in range(1, last_page_index+1):
    URL = "https://codeforces.com/contests/page/"+str(i)
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    tables = soup.find_all("div", class_="contests-table")
    contests_temp = tables[0].find_all("tr")
    for contest_rows_temp in contests_temp:
        contests_rows.append(contest_rows_temp.find_all("td"))
    print(str(i)+'/'+str(last_page_index))

for contest_row in contests_rows:
    if(len(contest_row)>0):
        ahref = 'https://codeforces.com'+contest_row[4].find("a")['href']
        name = contest_row[0].text.split('\n')[1]
        date = datetime.datetime.strptime(contest_row[2].text.split('\n')[1], '%b/%d/%Y %H:%M').strftime('%d.%m.%Y')
        contest = Contest(name, date, ahref)
        contests.append(contest)
        if(contest.date==requested_date):
            requested_contests.append(contest)

if(len(requested_contests)>0):
    writer = pd.ExcelWriter('./'+requested_date+'.xlsx', engine='xlsxwriter')
    contests_shits = {}
    for requested_contest in requested_contests:
        if(requested_contest.href):
            URL = requested_contest.href
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            table = soup.find("table", class_="standings")
            participants_rows = table.find_all("tr")
            participants_names = list()
            for i in range(1,6):
                participant_name=participants_rows[i].find("td", class_="contestant-cell").text.replace("\n", "")
                participants_names.append(participant_name)
            sheet_name = office_comp(requested_contest.name.split(' ')[0].replace("\n", ""))
        else:
            participants_names = list()
            participants_names.append('Нет данных')
            sheet_name = office_comp(requested_contest.name.split(' ')[0].replace("\n", ""))
        top5 = pd.DataFrame({'Top 5 in '+requested_contest.name.replace("\n", " ").replace("x000D_", ""): participants_names})
        if(sheet_name in contests_shits):
            num=1
            while(sheet_name+str(num) in contests_shits):
                num+=1
            sheet_name=sheet_name+'_'+str(num)
        contests_shits[sheet_name] = top5
        contests_shits[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
        print(requested_contest.name)
    writer.save()
else:
    print('Ничего не найдено. Возможно, вы ввели время не по UTC или турнир ещё не начался')