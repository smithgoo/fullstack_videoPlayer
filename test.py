import requests
from bs4 import BeautifulSoup
import mysql.connector
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

base_url = 'https://shandianzy.com'
page_limit = 1000  # 可根据需求修改页数

# 数据库配置
db_config = {
    'user': 'root',
    'password': 'Jbnb123456',
    'host': 'localhost',
    'database': 'DBInfo'
}


# ========== 爬取逻辑 ==========

# 设置Session并配置重试
def create_session():
    session = requests.Session()

    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    return session


session = create_session()


def getCurrentPageUrlArr(page):
    tmp_url = f'{base_url}/index.php/index/index/page/{page}.html'
    response = session.get(tmp_url)

    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        result = []

        spans = soup.find_all('span', class_='xing_vb4')
        for span in spans:
            a_tag = span.find('a')
            if a_tag and a_tag.get('href'):
                result.append({
                    'title': a_tag.text.strip(),
                    'url': base_url + a_tag.get('href')
                })

        infos = []
        for res in result:
            info = urlCommonResultFilter(res)
            address = info.get('address', '')
            info['address'] = address.split('#') if address else []
            infos.append(info)

        return {
            'total_pages': getVideosTotalPage(soup),
            'current_page': page,
            'data': infos,
        }
    else:
        print(f"Failed to fetch page {page}. Status Code: {response.status_code}")
        return None


def urlCommonResultFilter(res):
    url = res['url']
    response = session.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        result = {
            'title': getMainTitle(soup),
            'cover': getCover(soup),
            'content': getContentInfoDetail(soup),
            'address': getPlayAddress(soup),
        }
        sub_info = getSubTitle(soup)
        if sub_info:
            result.update(sub_info)
        return result
    else:
        print(f"Failed to fetch URL: {url}. Status Code: {response.status_code}")
        return {}


# ========== 数据提取 ==========

def getMainTitle(soup):
    div_tag = soup.find('div', class_='vodh')
    return div_tag.text.strip() if div_tag else ""


def getCover(soup):
    div_tag = soup.find('div', class_='vodImg')
    img_tag = div_tag.find('img') if div_tag else None
    return img_tag['src'].strip() if img_tag else ""


def getContentInfoDetail(soup):
    div_tag = soup.find('div', class_='vodplayinfo')
    return div_tag.text.strip() if div_tag else ""


def getPlayAddress(soup):
    div_tag = soup.find('div', style="padding-left:10px;word-break: break-all; word-wrap:break-word;")
    if not div_tag:
        return ""
    ul_tag = div_tag.find('ul')
    if not ul_tag:
        return ""
    m3u8_list = []
    for li_tag in ul_tag.find_all('li')[:45]:  # 最多取45个地址
        parts = li_tag.get_text().split('$')
        if len(parts) == 2:
            m3u8_list.append(parts[1].strip())
    return '#'.join(m3u8_list)


def getSubTitle(soup):
    div_tag_l = soup.find('div', class_='vodinfobox')
    info_dict = {}
    if div_tag_l:
        for li_tag in div_tag_l.find_all('li'):
            key = li_tag.contents[0].strip(':').strip()
            span = li_tag.find('span')
            value = span.get_text().strip() if span else ""
            if key.startswith("别名"):
                info_dict['otherName'] = value[:99]
            elif key.startswith("导演"):
                info_dict['videoDirector'] = value
            elif key.startswith("主演"):
                info_dict['videoMaincharacter'] = value
            elif key.startswith("类型"):
                info_dict['videoType'] = value
            elif key.startswith("地区"):
                info_dict['videoArea'] = value
            elif key.startswith("语言"):
                info_dict['videoLanguage'] = value
            elif key.startswith("上映"):
                info_dict['videoReleasetime'] = value
            elif key.startswith("更新"):
                info_dict['videoUpdate'] = value
    return info_dict


def getVideosTotalPage(soup):
    div_tag = soup.find('div', class_='mac_pages')
    if div_tag:
        page_tag = div_tag.find('div', class_='page_tip')
        if page_tag:
            pagstr = page_tag.text.split("/")
            if len(pagstr) >= 2:
                return int(''.join(filter(str.isdigit, pagstr[1])))
    return 1


# ========== 数据库操作 ==========

def create_database_and_table():
    connection = mysql.connector.connect(user=db_config['user'], password=db_config['password'], host=db_config['host'])
    cursor = connection.cursor()

    # 创建数据库（如果不存在）
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")

    # 选择数据库
    cursor.execute(f"USE {db_config['database']}")

    # 创建表（如果不存在）
    create_table_query = """
    CREATE TABLE IF NOT EXISTS videos_videoinfo (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        cover VARCHAR(255),
        content TEXT,
        address TEXT,
        other_name VARCHAR(255),
        video_director VARCHAR(255),
        video_maincharacter VARCHAR(255),
        video_type VARCHAR(255),
        video_area VARCHAR(255),
        video_language VARCHAR(255),
        video_release_time VARCHAR(255),
        video_update VARCHAR(255)
    )
    """
    cursor.execute(create_table_query)

    cursor.close()
    connection.close()


def insert_or_update_data(data):
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    cursor.execute("SELECT title FROM videos_videoinfo")
    existing_titles = {record[0].split('\n')[0] for record in cursor.fetchall()}

    for d in data:
        title = d.get('title', '').split('\n')[0]  # 去掉换行，取主标题
        address = '#'.join(d.get('address', []))

        if title in existing_titles:
            # 更新数据
            update_query = """
                UPDATE videos_videoinfo
                SET cover=%s, content=%s, address=%s, other_name=%s, video_director=%s, video_maincharacter=%s,
                    video_type=%s, video_area=%s, video_language=%s, video_release_time=%s, video_update=%s
                WHERE title=%s
            """
            cursor.execute(update_query, (
                d.get('cover', ''), d.get('content', ''), address, d.get('otherName', ''),
                d.get('videoDirector', ''), d.get('videoMaincharacter', ''), d.get('videoType', ''),
                d.get('videoArea', ''), d.get('videoLanguage', ''), d.get('videoReleasetime', ''),
                d.get('videoUpdate', ''), title
            ))
        else:
            # 插入数据
            insert_query = """
                INSERT INTO videos_videoinfo
                (title, cover, content, address, other_name, video_director, video_maincharacter, video_type,
                 video_area, video_language, video_release_time, video_update)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                title, d.get('cover', ''), d.get('content', ''), address, d.get('otherName', ''),
                d.get('videoDirector', ''), d.get('videoMaincharacter', ''), d.get('videoType', ''),
                d.get('videoArea', ''), d.get('videoLanguage', ''), d.get('videoReleasetime', ''),
                d.get('videoUpdate', '')
            ))

    connection.commit()
    cursor.close()
    connection.close()


# ========== 主执行流程 ==========

def run_scraper():
    create_database_and_table()  # 创建数据库和表
    for page in range(1, page_limit + 1):
        print(f"正在爬取第 {page} 页...")
        response = getCurrentPageUrlArr(page)
        if response and response['data']:
            insert_or_update_data(response['data'])
            print(f"第 {page} 页 插入成功...")
        else:
            print(f"第 {page} 页无数据或请求失败")
        time.sleep(3)  # 避免请求过快被封IP


# ========== 启动 ==========

if __name__ == "__main__":
    run_scraper()
