# 20241108 修正有多種來源副檔名的問題

import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse

# 設定基礎 URL 和查詢頁面 URL
# 國家教育研究院-全國中小學題庫網
BASE_URL = "https://exam.naer.edu.tw/"

# Step 1
# 複製查詢結果生成的網址 (以下範例為"新北市/國小/一年級"條件所生成的網址)
SEARCH_URL = "https://exam.naer.edu.tw/searchResult.php?page=1&orderBy=lastest&keyword=&selCountry=01&selCategory=41&selTech=0&chkClass%5B%5D=9&selYear=&selTerm=&selType=&selPublisher="

# 使用正則表達式替換 page 的數值為 page={}
SEARCH_URL_TEMPLATE = re.sub(r'page=\d+', 'page={}', SEARCH_URL)

# Step 2
# 設定存儲資料夾，如果不想分類就同一個名稱用到底也可以。
DOWNLOAD_FOLDER = "ExamPaper"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_file(pdf_url, file_name):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"已下載: {file_name}")
    else:
        print(f"無法下載: {file_name}")

# 20241108 修正網站來源檔案除了pdf以外還有其它格式的邏輯
def parse_filename(info, file_url, file_type):
    # 先從來源 URL 中取得副檔名
    file_extension = os.path.splitext(urlparse(file_url).path)[1]
    # 依據規則生成檔名，最後加上副檔名
    return f"{info['city']}_{info['school']}_{info['grade']}_{info['year']}_{info['subject']}_{info['type']}_{info['version']}_{file_type}{file_extension}"

def scrape_page(page_url):
    response = requests.get(page_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # 找到表格行
    rows = soup.find_all('tr')[1:]  # 跳過表頭

    for row in rows:
        cells = row.find_all('td')
        
        # 確認該行是否包含足夠的欄位
        if len(cells) < 11:
            continue  # 略過欄位數不足的行
        
        # 提取資訊
        info = {
            "city": cells[0].text.strip(),
            "school": cells[1].text.strip(),
            "grade": cells[2].text.strip(),
            "year": cells[3].text.strip(),
            "subject": cells[5].text.strip(),
            "type": cells[6].text.strip(),
            "version": cells[7].text.strip(),
            "id": cells[8].text.strip()
        }

        # 生成檔名 20241108 remove
        # pdf_name = parse_filename(info)   

        # 下載 PDF 檔案
        # 試卷 PDF
        exam_link = cells[9].find('a')
        if exam_link and not exam_link['href'].startswith("mailto:"):
            exam_file_url = urljoin(BASE_URL, exam_link['href'])
            exam_file_name = parse_filename(info, exam_file_url, "試卷")
            download_file(exam_file_url, exam_file_name)

        # 答案 PDF
        answer_link = cells[10].find('a')
        if answer_link and not answer_link['href'].startswith("mailto:"):
            answer_file_url = urljoin(BASE_URL, answer_link['href'])
            answer_file_name = parse_filename(info, answer_file_url, "答案")
            download_file(answer_file_url, answer_file_name)

def main():
    # 取得初始頁面，來獲取總頁數
    response = requests.get(SEARCH_URL_TEMPLATE.format(1))
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # 從頁面中提取總頁數
    total_pages = int(soup.find('span', id='total_p').get('data-val', '1'))
    print(f"總頁數: {total_pages}")

    # 依頁碼迴圈爬取每頁
    for page_num in range(1, total_pages + 1):
        page_url = SEARCH_URL_TEMPLATE.format(page_num)
        print(f"開始爬取第 {page_num} 頁: {page_url}")
        scrape_page(page_url)

if __name__ == "__main__":
    main()
