import json
import time
import os
from playwright.sync_api import sync_playwright # <<< SỬ DỤNG PLAYWRIGHT
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
BASE_URL = "https://emohbackup.moh.gov.vn"
START_URL = f"{BASE_URL}/publish/home"
OUTPUT_FILE = 'van_ban_byt.json'

# Giới hạn an toàn (10 trang). Bạn có thể thay MAX_PAGES = 99 để lấy hết
MAX_PAGES = 10 

# --- HÀM THU THẬP DỮ LIỆU ---

def get_data_from_page(page):
    """Lấy dữ liệu từ trang hiện tại."""
    data_page = []
    
    # Đợi cho bảng dữ liệu (table-bordered) xuất hiện
    try:
        page.wait_for_selector('table.table-bordered', timeout=10000)
    except Exception as e:
        print(f"!!! Lỗi: Không tìm thấy bảng dữ liệu trên trang. {e}")
        return []

    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='table table-bordered table-striped')

    if table:
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]

        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) >= 6: 
                ky_hieu = cols[1].text.strip()
                
                file_link_tag = cols[5].find('a') 
                file_link_suffix = file_link_tag['href'] if file_link_tag and 'href' in file_link_tag.attrs else None

                full_file_link = f"{BASE_URL}{file_link_suffix}" if file_link_suffix else ''

                data_page.append({
                    'Ký hiệu': ky_hieu,
                    'Ban hành': cols[2].text.strip(),
                    'Trích yếu': cols[3].text.strip(),
                    'Đơn vị ban hành': cols[4].text.strip(),
                    'Link file': full_file_link
                })
    
    return data_page

def crawl_all_pages():
    """Thực hiện crawl qua tất cả các trang bằng Playwright."""
    all_data = []
    page_count = 1
    
    print(">>> Bắt đầu khởi động trình duyệt Playwright...")
    with sync_playwright() as p:
        # Sử dụng Chromium và bỏ qua các lỗi chứng chỉ SSL (ignore_https_errors=True)
        browser = p.chromium.launch(headless=True, ignore_https_errors=True)
        page = browser.new_page()
        page.goto(START_URL)

        while page_count <= MAX_PAGES:
            print(f"\n--- Đang thu thập Trang {page_count}/{MAX_PAGES} ---")
            
            data_page = get_data_from_page(page)
            all_data.extend(data_page)
            
            # Kiểm tra và click nút trang tiếp theo (►)
            next_button_selector = 'div.dataTables_paginate a:text("►")'
            
            try:
                # Đợi cho nút bấm trang kế tiếp có sẵn
                next_button = page.wait_for_selector(next_button_selector, timeout=5000)
                
                # Nếu đây là trang cuối cùng
                if 'disabled' in next_button.get_attribute('class', default='') or page_count == MAX_PAGES:
                     print("Đã đạt đến trang cuối cùng hoặc giới hạn MAX_PAGES.")
                     break
                
                # Thực hiện click và đợi trang mới tải xong
                next_button.click()
                page.wait_for_load_state("networkidle") 
                
                page_count += 1
                time.sleep(1) # Độ trễ an toàn
                
            except Exception:
                # Không tìm thấy nút trang tiếp theo, kết thúc quá trình
                print("Không tìm thấy nút chuyển trang. Kết thúc quá trình.")
                break

        browser.close()

    print("\n>>> Hoàn thành thu thập dữ liệu.")
    print(f"Tổng số văn bản thu thập được: {len(all_data)}")

    # Lưu dữ liệu vào file JSON
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
            
        print(f"Đã lưu dữ liệu thành công vào file: {OUTPUT_FILE}")
    except Exception as e:
        print(f"!!! Lỗi khi lưu file JSON: {e}")

if __name__ == "__main__":
    crawl_all_pages()