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
    soup = BeautifulSoup(response.content, 'html.parser')
    details = soup.select_one('#mainContent > div.flowerWrapper > div > div > div > div.detailData.row.first.view__detail')
    
    # Initialize the details dictionary with empty values
    job_details = {
        'Ref Number': '',
        'Primary Location': '',
        'Country': '',
        'Job Type': '',
        'Work Style': ''
    }

    if details:
        field_sets = details.select('.fieldSet')
        for field_set in field_sets:
            label = field_set.select_one('.fieldSetLabel').text.strip()
            value = field_set.select_one('.fieldSetValue').text.strip()
            
            if 'Ref Number' in label:
                job_details['Ref Number'] = value
            elif 'Primary Location' in label:
                job_details['Primary Location'] = value
            elif 'Country' in label:
                job_details['Country'] = value
            elif 'Job Type' in label:
                job_details['Job Type'] = value
            elif 'Work Style' in label:
                job_details['Work Style'] = value
    
    return job_details

def scrape_jobs(main_url, existing_ids):
    jobs_data = []
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    next_url = main_url
    processed_jobs = 0

    while next_url:
        response = requests.get(next_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.select('#mainContent > ul > li.listSingleColumnItem')
        
        for job in job_listings:
            title_tag = job.find('h3', class_='listSingleColumnItemTitle')
            job_title = title_tag.text.strip()
            apply_link = title_tag.find('a')['href']
            job_id = apply_link.split('/')[-1]
            
            if job_id not in existing_ids:
                # Fetch additional job details from individual job page
                additional_details = fetch_job_details(apply_link)
                
                job_data = {
                    'Date Added': date_str,
                    'Time Added': time_str,
                    'ID': job_id,
                    'Ref Number': additional_details['Ref Number'],
                    'Category': '',
                    'Job Title': job_title,
                    'Primary Location': additional_details['Primary Location'],
                    'Country': additional_details['Country'],
                    'Job Type': additional_details['Job Type'],
                    'Workplace Type': additional_details['Work Style'],
                    'Commitment': '',
                    'Location': '',
                    'Apply Link': apply_link,
                    'Job Description': '',
                    'Salary': ''
                }
                jobs_data.append(job_data)
                processed_jobs += 1
                print(f"Processed new job: {processed_jobs} - {job_title}")

        # Find the 'Next' link, if it exists
        next_link = soup.select_one('a.paginationNextLink')
        next_url = next_link['href'] if next_link else None

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
url = 'https://jobs.telusinternational.com/en_US/careers/aicommunity'

# Load existing job IDs
existing_ids = load_existing_ids('telus.csv')

# Scrape the data
new_job_listings = scrape_jobs(url, existing_ids)

# File to save to
csv_file = 'telus.csv'

# Update the job listings CSV file
update_job_listings(csv_file, new_job_listings)

print("TELUS job listings have been updated with new entries.")
