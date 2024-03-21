import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

def load_existing_ids(csv_file):
    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file)
        return set(existing_data['ID'])
    return set()

def fetch_job_details(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    job_description_selector = 'div.content-wrapper.posting-page > div > div:nth-child(2) > div:nth-child(1)'
    salary_selector = 'div.content-wrapper.posting-page > div > div:nth-child(2) > div:nth-child(2)'
    
    job_description = soup.select_one(job_description_selector).get_text(separator="\n", strip=True)
    salary_info = soup.select_one(salary_selector).get_text(strip=True) if soup.select_one(salary_selector) else 'Not Provided'
    
    return job_description, salary_info

def scrape_jobs(url, existing_ids):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs_data = []
    postings_groups = soup.select('div.postings-group')
    total_jobs = sum(len(group.select('div.posting')) for group in postings_groups)
    fetched_jobs = 0
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    for group in postings_groups:
        category = group.find('div', class_='posting-category-title').text.strip()
        
        postings = group.select('div.posting')
        for posting in postings:
            job_id = posting['data-qa-posting-id']
            
            # Skip fetching details if the job ID exists
            if job_id in existing_ids:
                continue
            
            job_title = posting.find('h5').text.strip()
            workplace_type = posting.select_one('.workplaceTypes').text.strip()
            commitment = posting.select_one('.commitment').text.strip()
            location = posting.select_one('.location').text.strip()
            apply_link = posting.find('a', class_='posting-btn-submit')['href']
            
            job_description, salary_info = fetch_job_details(apply_link)
            
            job_data = {
                'Date Added': date_str,
                'Time Added': time_str,
                'ID': job_id,
                'Category': category,
                'Job Title': job_title,
                'Workplace Type': workplace_type,
                'Commitment': commitment,
                'Location': location,
                'Apply Link': apply_link,
                'Job Description': job_description,
                'Salary': salary_info
            }
            jobs_data.append(job_data)
            fetched_jobs += 1
            print(f"Fetching new jobs: {fetched_jobs}/{total_jobs} ({(fetched_jobs/total_jobs)*100:.2f}%)")
    
    return pd.DataFrame(jobs_data)

def update_job_listings(csv_file, new_data):
    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file)
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        combined_data.drop_duplicates(subset=['ID'], keep='first', inplace=True)
    else:
        combined_data = new_data
        
    combined_data.to_csv(csv_file, index=False)

# URL to scrape
url = 'https://jobs.lever.co/appen'

# Load existing job IDs
existing_ids = load_existing_ids('appen.csv')

# Scrape the data
new_job_listings = scrape_jobs(url, existing_ids)

# File to save to
csv_file = 'appen.csv'

# Update the job listings CSV file
update_job_listings(csv_file, new_job_listings)

print("Job listings have been updated with descriptions, salary information, and the date and time added.")
