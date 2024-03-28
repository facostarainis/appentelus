import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

# Define the columns order globally
columns_order = [
    'Date Added', 'Time Added', 'ID', 'Ref Number', 'Category', 'Job Title',
    'Workplace Type', 'Commitment', 'Location', 'Primary Location',
    'Apply Link', 'Job Description', 'Additional Job Description', 'Salary'
]

def load_existing_ids(csv_file):
    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file, dtype=str)  # Ensure IDs are read as strings
        return set(existing_data['ID'].astype(str))  # Convert IDs to strings if not already
    return set()

def fetch_job_details(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    details = soup.select_one('#mainContent > div.flowerWrapper > div > div > div > div.detailData.row.first.view__detail')
    description_section = soup.select_one('#mainContent > div.flowerWrapper > div > div > div > div.detailDescription.row')
    
    job_details = {
        'Ref Number': '',
        'Primary Location': '',
        'Location': '',  # Use this instead of Country
        'Job Type': '',
        'Work Style': '',
        'Job Description': '',
        'Additional Job Description': ''
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
            elif 'Country' in label:  # This data will now go into 'Location'
                job_details['Location'] = value
            elif 'Job Type' in label:
                job_details['Job Type'] = value
            elif 'Work Style' in label:
                job_details['Work Style'] = value

    if description_section:
        # Job Description
        description_texts = description_section.select('h3.icon, .crmDescription')
        job_description_text = '\n\n'.join([desc.get_text(separator='\n', strip=True) for desc in description_texts])
        job_details['Job Description'] = job_description_text.strip()

        # Additional Job Description
        additional_description = description_section.select_one('.view__detail-bottom')
        if additional_description:
            additional_job_description_text = additional_description.get_text(separator='\n', strip=True)
            job_details['Additional Job Description'] = additional_job_description_text.strip()

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
            job_id = str(apply_link.split('/')[-1])
            
            if job_id not in existing_ids:
                additional_details = fetch_job_details(apply_link)
                
                job_data = {column: '' for column in columns_order}  # Initialize all columns with empty string
                job_data.update({
                    'Date Added': date_str,
                    'Time Added': time_str,
                    'ID': job_id,
                    'Ref Number': additional_details.get('Ref Number', ''),
                    'Category': '',  # Update this if you have category data
                    'Job Title': job_title,
                    'Workplace Type': additional_details.get('Work Style', ''),
                    'Commitment': '',  # Update this if you have commitment data
                    'Location': additional_details.get('Location', ''),
                    'Primary Location': additional_details.get('Primary Location', ''),
                    'Apply Link': apply_link,
                    'Job Description': additional_details.get('Job Description', ''),
                    'Additional Job Description': additional_details.get('Additional Job Description', ''),
                    'Salary': ''  # Update this if you have salary data
                })
                jobs_data.append(job_data)
                processed_jobs += 1
                print(f"Processed job: {job_title} with ID: {job_id} [{processed_jobs}/{len(job_listings)}]")
            else:
                print(f"Skipping duplicate job: {job_title} with ID: {job_id}")

        next_link = soup.select_one('a.paginationNextLink')
        next_url = next_link['href'] if next_link else None

    return pd.DataFrame(jobs_data, columns=columns_order)


def update_job_listings(csv_file, new_data):
    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file)
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        combined_data.drop_duplicates(subset=['ID'], keep='first', inplace=True)
    else:
        combined_data = new_data

    combined_data.to_csv(csv_file, index=False, columns=columns_order)

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

