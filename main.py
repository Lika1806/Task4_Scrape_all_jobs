from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import pandas as pd


driver = webdriver.Chrome()
start_url = 'https://staff.am/en'
driver.get(start_url)
button = driver.find_element(By.XPATH, '//*[@id="w1"]/li[1]/a')
button.click()



def scrape_job_page(text):
    '''Returns the list with information about job, in this order: 
    [Employment term:
    Category:
    Job type:
    Number of Views:
    Required candidate level: 
    Salary:
    Professional skills:
    Soft skills:]
    '''
    final_list = []
    soup = BeautifulSoup(text)
    #getting general information
    gen_info = soup.find_all('div', class_='col-lg-6 job-info')
    for div in gen_info:
        p_s = div.find_all('p')
        for p in p_s:
            final_list.append(p.text.split(':')[1].strip())
    final_list = final_list[:-1]

    #getting post views
    view = soup.find('div', class_ = 'statistics')
    view = view.find('p').text
    view = view.split()[-2]
    print(view)
    final_list.append(view)
    
    #getting Required candidate level: and Salary 
    level_info = soup.find_all('h3')  
    level = None
    salary = None
    for i in level_info:
        if 'Required candidate level:' in i.text:
            level = i.text.split(':')[1].strip()
            if 'Not defined' in level:
                level = None
        elif 'Salary' in i.text:
            salary = i.text.split(':')[1].strip()
            salary = salary.replace('\t', ' ').replace('\n', ' ')
            salary = ' '.join(salary.split())
            
    final_list+=[level,salary]
    
    #getting information about skills
    skill_info = soup.find_all('div', class_ = 'soft-skills-list clearfix')
    skills = {'Professional skills': [], 'Soft skills':[]}
    for div in skill_info:
        title = div.find('h3').text.strip()
        p_s = div.find_all('p')
        skills[title] = [p.text.strip() for p in p_s]

    #updating final list
    final_list+=[skills['Professional skills'], skills['Soft skills']]
#    print(final_list)
    return final_list

def scrape_list_page(text):
    '''Returns a full list with information about job, in this order: 
    [Job title:
    Company name:
    Post date:
    Location:
    Employment term:
    Category:
    Job type:
    Number of Views:
    Required candidate level:
    Salary:
    Professional skills;
    Soft skills:]
    '''
    soup = BeautifulSoup(text, 'html')
    
    #finding all jobs
    the_list = soup.find_all('div', class_ = 'web_item_card hs_job_list_item')
    page_list = []
    
    for job in the_list:
        
        job_info = []
        info = job.find('div',class_ = 'job-inner job-item-title')

        #getting job name and company name
        info = info.find_all('p')
        job_name = info[0].text.strip()
        company_name = info[1].text.strip()
        
        #getting post date and location
        post_date = job.find('span', class_='formatted_date').text.strip()
        location = job.find('p', class_='job_location').text.strip()
        
        #adding all found information to the final list
        job_info = [job_name, company_name, post_date, location]

        #finding job's personal page url and getting data from that url
        job_url = job.find('a')['href']
        driver.get('https://staff.am'+ job_url)
        job_info.extend(scrape_job_page(driver.page_source))
        driver.back()
        
        page_list.append(job_info)
        
    return page_list

final_job_list = []
while True:
    try:
        new_list = scrape_list_page(driver.page_source)
        final_job_list+=new_list
        with open('final_gob_info.json', 'w') as file:
            json.dump(final_job_list, file)
        # Wait for the next button to be clickable
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'next'))
        )
        next_button.click()

        # Wait for 5 seconds after clicking the next button
        WebDriverWait(driver, 5).until(EC.staleness_of(next_button))
    except Exception as e:
        print(e)
        break


df = pd.DataFrame(final_job_list, columns = ['Job title',
                                             'Company name', 
                                             'Post date',
                                             'Location',
                                             'Employment term',
                                             'Category',
                                             'Job type',
                                             'Number of Views',
                                             'Required candidate level',
                                             'Salary',
                                             'Professional skills',
                                             'Soft skills'])
df = df[['Post date',
        'Number of Views',
        'Location',
        'Company name', 
        'Job title',
        'Category',
        'Job type',
        'Employment term',
        'Required candidate level',
        'Salary',
        'Professional skills',
        'Soft skills']]

df.to_csv('job_final_list.csv', index=False)