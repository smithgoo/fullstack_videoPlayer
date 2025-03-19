import requests
from bs4 import BeautifulSoup
import time
import random

# 模拟其他浏览器
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/13.0.3 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.64',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 10; Pixel 3 XL Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 OPR/75.0.3969.243',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
]

file_path = 'magnet_links.txt'
allBaseUrl = "https://www.dytt8.com"
newbaseurl = "https://www.dytt8.com/html/gndy/dyzz/list_23_2.html"

# 创建全局 session
session = requests.Session()

# 记录脚本开始时间
start_time = time.time()


# 通用请求函数，自动重试机制
def safe_request(url, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            headers = {'User-Agent': random.choice(user_agents)}
            response = session.get(url, headers=headers, timeout=timeout)
            response.encoding = 'gb2312'
            return response
        except requests.exceptions.RequestException as e:
            print(f"[错误] 第 {attempt + 1} 次请求 {url} 失败: {e}")
            time.sleep(random.uniform(3, 5))  # 出错等待几秒再试
    print(f"[失败] 多次重试后仍无法请求 {url}")
    return None


# 获取最大页数
def getMaxPage(newbaseurl):
    response = safe_request(newbaseurl)
    if not response:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    co_content8 = soup.find('div', class_='co_content8')
    pagination = co_content8.find('div', class_='x') if co_content8 else None
    if not pagination:
        print("未找到分页区块")
        return None

    a_tags = pagination.find_all('a')
    if not a_tags:
        print("未找到分页链接")
        return None

    last_page_url = a_tags[-1].get('href')
    if last_page_url:
        page_number = last_page_url.split('_')[-1].split('.')[0]
        print(f"[信息] 最大页数: {page_number}")
        return int(page_number)
    return None


# 循环请求每一页并提取信息
def getPageAndCycle():
    max_page = getMaxPage(newbaseurl)
    if not max_page:
        print("无法获取最大页数")
        return

    print(f"[信息] 开始爬取，最大页数: {max_page}")

    for page_num in range(1, max_page + 1):
        # 计算并打印脚本当前的运行时间
        elapsed_time = time.time() - start_time
        elapsed_minutes = elapsed_time // 60
        elapsed_seconds = elapsed_time % 60
        print(f"[信息] 当前运行时间: {int(elapsed_minutes)} 分 {int(elapsed_seconds)} 秒")

        print(f"[信息] 请求第 {page_num} 页...")
        page_url = f"{allBaseUrl}/html/gndy/dyzz/list_23_{page_num}.html"
        response = safe_request(page_url)
        if not response:
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        co_content8 = soup.find('div', class_='co_content8')
        if not co_content8:
            print("未找到 co_content8 区域")
            continue

        td_list = co_content8.find_all('td', height='26')
        for td in td_list:
            a_tag = td.find('a', class_='ulink')
            if a_tag:
                link = a_tag['href']
                title = a_tag.get_text(strip=True)
                print(f"标题: {title}")
                print(f"链接: {allBaseUrl + link}")
                getVideoInfo(allBaseUrl + link, title)
                time.sleep(random.uniform(1, 2))  # 短暂延迟

        time.sleep(random.uniform(10, 15))  # 每页延迟


# 获取电影详情并提取磁力链接
def getVideoInfo(url, title):
    response = safe_request(url)
    if not response:
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    co_content8 = soup.find('div', class_='co_content8')
    if not co_content8:
        print("未找到 co_content8 区域")
        return

    # 先读取已存在的链接，避免重复写入
    try:
        with open(file_path, 'r', encoding='utf-8') as f_exist:
            existing_links = set(line.split(' # ')[0] for line in f_exist if line.startswith('magnet:'))
    except FileNotFoundError:
        existing_links = set()

    # 用集合存储当前页面提取到的 magnet 链接，自动去重
    found_magnets = set()

    # 提取所有 <a> 标签（包括 target='_blank' 和 <p> 内的 <a>）
    all_a_tags = co_content8.find_all('a')

    for a in all_a_tags:
        href = a.get('href')
        if href and href.startswith('magnet:'):
            found_magnets.add(href)

    # 开始写入新增的 magnet 链接
    with open(file_path, 'a', encoding='utf-8') as f:
        for magnet_link in found_magnets:
            if magnet_link not in existing_links:
                f.write(f"{magnet_link} # {title}\n")
                print(f"[新增] 写入磁力链接: {magnet_link}")
            else:
                print(f"[跳过] 已存在磁力链接: {magnet_link}")


if __name__ == '__main__':
    getPageAndCycle()
    # getVideoInfo('https://www.dytt8.com/html/gndy/dyzz/20191101/59315.html','111')