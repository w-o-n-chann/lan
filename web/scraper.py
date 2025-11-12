import requests
from bs4 import BeautifulSoup
import json
import time
import os

# --- CẤU HÌNH ---
BASE_URL = "https://emohbackup.moh.gov.vn/publish/home"
START_URL = f"{BASE_URL}/publish/home"
OUTPUT_FILE = 'van_ban_byt.json'

# CHÚ Ý: Đặt giới hạn an toàn để tránh gây quá tải cho máy chủ BYT. 
# Hiện tại tôi đặt giới hạn là 5 trang để demo.
# Nếu bạn muốn lấy hết (tổng 95 trang), hãy thay MAX_PAGES = 99
MAX_PAGES = 5 

# --- HÀM THU THẬP DỮ LIỆU ---

def get_data_from_page(url):
    """Lấy dữ liệu từ một trang cụ thể."""
    print(f"  -> Đang truy cập: {url}")
    data_page = []
    next_link = None
    
    try:
        # Tăng timeout cho các trường hợp kết nối chậm
        response = requests.get(url, timeout=20) 
        response.raise_for_status() # Kiểm tra lỗi HTTP (4xx hoặc 5xx)
    except requests.exceptions.RequestException as e:
        print(f"!!! Lỗi khi truy cập trang web {url}: {e}")
        return [], None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    table = soup.find('table', class_='table table-bordered table-striped')

    if table:
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]

        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 6: 
                ky_hieu = cols[1].text.strip()
                
                # Lấy link tải về file đính kèm
                file_link_tag = cols[5].find('a') 
                file_link_suffix = file_link_tag['href'] if file_link_tag and 'href' in file_link_tag.attrs else None

                # Tạo link tuyệt đối cho Frontend
                full_file_link = f"{BASE_URL}{file_link_suffix}" if file_link_suffix else ''

                data_page.append({
                    'Ký hiệu': ky_hieu,
                    'Ban hành': cols[2].text.strip(),
                    'Trích yếu': cols[3].text.strip(),
                    'Đơn vị ban hành': cols[4].text.strip(),
                    'Link file': full_file_link
                })

    # Tìm link đến trang tiếp theo (Pagination)
    pagination = soup.find('div', class_='dataTables_paginate')
    if pagination:
        # Tìm thẻ <a> có chữ "►"
        next_button = pagination.find('a', string='►')
        if next_button and 'href' in next_button.attrs:
            next_link = next_button['href']
            # Chuyển link tương đối thành link tuyệt đối
            if next_link and not next_link.startswith('http'):
                next_link = f"{BASE_URL}{next_link}"

    return data_page, next_link

def crawl_all_pages():
    """Thực hiện crawl qua tất cả các trang."""
    all_data = []
    current_url = START_URL
    page_count = 1
    
    while current_url and page_count <= MAX_PAGES:
        print(f"\n--- Đang thu thập Trang {page_count}/{MAX_PAGES} ---")
        data_page, next_url = get_data_from_page(current_url)
        all_data.extend(data_page)
        current_url = next_url
        page_count += 1
        
        # ĐỘ TRỄ: Giúp giảm tải cho máy chủ. Không nên bỏ qua bước này!
        if current_url:
            time.sleep(2) 

    print("\n>>> Hoàn thành thu thập dữ liệu.")
    print(f"Tổng số văn bản thu thập được: {len(all_data)}")

    # Lưu dữ liệu vào file JSON
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # Sử dụng ensure_ascii=False để giữ tiếng Việt và indent=4 để dễ đọc
            json.dump(all_data, f, ensure_ascii=False, indent=4)
            
        print(f"Đã lưu dữ liệu thành công vào file: {OUTPUT_FILE}")
    except Exception as e:
        print(f"!!! Lỗi khi lưu file JSON: {e}")

if __name__ == "__main__":
    crawl_all_pages()