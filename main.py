import os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import time
from tqdm import tqdm

def parse_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
    
    profile_name = soup.select_one('._a70e').text.strip() if soup.select_one('._a70e') else 'Unknown'
    
    conversations = []
    for message in soup.select('.pam._3-95._2ph-._a6-g'):
        sender = message.select_one('._3-95._2pim._a6-h._a6-i').text.strip()
        content_div = message.select_one('._3-95._a6-p')
        
        content_parts = [div.text.strip() for div in content_div.find_all('div', recursive=False) if div.text.strip()]
        content = ' '.join(content_parts)
        
        sender = '1acre' if sender.lower().startswith('1acre') else sender
        
        if content:
            conversations.append(f"[{sender}]: {content}")
    
    conversation_text = '\n'.join(dict.fromkeys(conversations))
    
    first_timestamp = soup.select('._3-94._a6-o')[-1].text.strip()
    first_contact = datetime.strptime(first_timestamp, '%d %b %Y, %H:%M')
    
    return {
        'First Contact Date and Time': first_contact,
        'Conversation': conversation_text,
        'Name of the Profile': profile_name
    }

def process_folders(root_folder):
    data = []
    total_files = sum([len(files) for r, d, files in os.walk(root_folder) if any(f.endswith('.html') for f in files)])
    
    with tqdm(total=total_files, desc="Processing HTML files", unit="file") as pbar:
        for root, dirs, files in os.walk(root_folder):
            html_files = [f for f in files if f.endswith('.html')]
            if html_files:
                folder_pbar = tqdm(html_files, desc=f"Processing {os.path.basename(root)}", leave=False)
                for file in folder_pbar:
                    file_path = os.path.join(root, file)
                    try:
                        data.append(parse_html(file_path))
                    except Exception as e:
                        print(f"Error processing {file_path}: {str(e)}")
                    pbar.update(1)
                folder_pbar.close()
    return data

def process_files(root_folder, output_file):
    start_time = time.time()
    print(f"Starting to process files in {root_folder}")
    data = process_folders(root_folder)
    print("Creating DataFrame and saving to Excel...")
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Data extracted and saved to {output_file}")
    print(f"Total time elapsed: {elapsed_time:.2f} seconds")
    print(f"Total HTML files processed: {len(data)}")

if __name__ == "__main__":
    root_folder = "./inbox/"
    output_file = "./inbox/instagram_conversations.xlsx"
    process_files(root_folder, output_file)