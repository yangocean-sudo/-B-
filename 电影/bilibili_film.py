# -*- codeing = utf -8 -*-
# @Time : 2021/8/1 上午9:04
# @Author : Cui Yangyang
# @File : bilibili.py
# @Software: PyCharm
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import ssl
import re
import xlwt
from io import BytesIO
import gzip
import json
import time

# 使用ssl创建未验证的上下文，在url中传入上下文参数
context = ssl._create_unverified_context()

# 所有的需要爬取的内容，虽然后面用json data的时候有些并没有用到
findName = re.compile(r'<a class="media-title" (.+)>(.*?)</a>')
findType = re.compile(r'<a class="home-link" href="(.*?)"</a>')
findDetail = re.compile(r'<span class="absolute">"(.*?)"</span>')
findDownload = re.compile(r'<script>window.__INITIAL_STATE__={"(.*?)"</script>')
findDetailLink = re.compile(r'<a class="media-cover" href="(.*?)" target="_blank"><!-- --></a>')
findTag = re.compile(r'<span class="media-tag">(.*?)</span>')
findActor = re.compile(r'<span class="hide" style="opacity: 0;"><p>(.*?)</p></span>')


def wait(seconds):
    print('wait for ' + str(seconds) + ' seconds')
    time.sleep(seconds)


def getData():
    # 最大的list，将直接倒入Excel中
    big_data_list = []
    # for j in range(1, 192):
    for j in range(1, 20):
        # 动态地址
        url = 'https://api.bilibili.com/pgc/season/index/result?area=-1&style_id=-1&release_date=-1&season_status=-1' \
              '&order=2&st=2&sort=0&page='+str(j)+'&season_type=2&pagesize=20&type=1 '
        # url = 'https://api.bilibili.com/pgc/season/index/result?season_version=-1&spoken_language_type=-1&area=-1
        # &is_finish=-1&copyright=-1&season_status=-1&season_month=-1&year=-1&style_id=-1&order=2&st=1&sort=0&page
        # ='+str(j)+'&season_type=1&pagesize=20&type=1'
        html = askURL(url)
        # print(html.read().decode('utf-8'))
        jsonData = json.loads(html)
        # print(jsonData)
        data = jsonData['data']
        json_list = data['list']
        # for i in mediaInfo.keys():
        #     print(i)
        #     print(mediaInfo[i])
        for i in range(len(json_list)):
            # 这是单独一部影视资源的detail
            data = []
            # 标题
            title = json_list[i]['title']
            data.append(title)
            # 链接
            link = json_list[i]['link']
            data.append(link)
            # 影视资格（会员/独家/无）
            badge = json_list[i]['badge']
            data.append(badge)
            # 播放量
            order = json_list[i]['order']
            data.append(order)
            # 具体视频页链接
            link = json_list[i]['link']
            id = str(json_list[i]['media_id'])
            url = 'https://api.bilibili.com/pgc/review/user?media_id=' + id
            # 访问具体动态页面
            area_html = askURL(url)
            area_jsonData = json.loads(area_html)
            result = area_jsonData['result']
            media = result['media']
            # 国家与地区
            areas = media['areas']
            area_list = []
            for country in areas:
                area_list.append(country['name'])
            area_string = ""
            # 将列表中的国家转入字符串中，再将字符串添加到详细信息列表里
            for i in range(len(area_list)):
                if i == len(area_list)-1:
                    area_string = area_string + area_list[i]
                else:
                    area_string = area_string + area_list[i] + ","
            data.append(area_string)
            # 访问具体视频页链接需要解码
            html = askURLDecode(link)
            movieData = re.search(r"window\.__INITIAL_STATE__=(.*?);", html).group(1)
            # 当时遇到了一个问题，在简介中遇到'}'符号，导致程序不能正常运行，就用这个if条件句解决了
            if (movieData[len(movieData)-1] != "}"):
                movieData = re.search(r"window\.__INITIAL_STATE__=(.*?)};", html).group(1) + "}"
            movieData = json.loads(movieData)
            mediaInfo = movieData['mediaInfo']
            # 故事简介，去除转译符号和词语
            evaluate = str(mediaInfo['evaluate']).replace("\n", "")
            evaluate = evaluate.replace("\\u3000", "")
            evaluate = evaluate.replace("\r", "")
            data.append(evaluate)
            # 评分
            rating = mediaInfo['rating']
            score = rating['score']
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.find_all('div', class_="media-info clearfix report-wrap-module"):
                item = str(item)
                detail_link = re.findall(findDetailLink, item)[0]
                # 这个是视频播放页面
                detail_html = askURLDecode("https:" + str(detail_link))
                actor_movieData = re.search(r"window\.__INITIAL_STATE__=(.*?);", detail_html).group(1)
                # 找到演员，删除一些转译符号
                actor = re.findall(r'"actors":"(.*?)"', actor_movieData)[0]
                actor = actor.replace("\\u002F", "、")
                actor = actor.replace("\\n", "、")
                data.append(actor)
                # actor_movieData = json.loads(actor_movieData)
                # for i in actor_movieData.keys():
                #     print(i)
                #     pœrint(actor_movieData[i])
                # actor_media_info = movieData['mediaInfo']
                # for i in actor_media_info.keys():
                #     print(i)
                #     print(actor_media_info[i])
                # actors = actor_media_info['actors']
                # print(actors)
                soup = BeautifulSoup(detail_html, "html.parser")
                # 找出分类
                for detail in soup.find_all('div', class_="media-info-r"):
                    detail = str(detail)
                    tag = re.findall(findTag,detail)
            # 将分类从列表转为string
            tag_string = ""
            for k in range(len(tag)):
                if k == len(tag) - 1:
                    tag_string = tag_string + tag[k]
                else:
                    tag_string = tag_string + tag[k] + ","
            data.append(tag_string)
            data.append(score)
            # 是否可以下载
            if not mediaInfo['episodes']:
                section = mediaInfo['section'][0]
                episodes = section['episodes'][0]
                rights = episodes['rights']
                download = rights['allow_download']
                if download == 1:
                    data.append("可以下载")
                else:
                    data.append("不能下载")
                print(data, "\n")
                big_data_list.append(data)
            else:
                episodes = mediaInfo['episodes'][0]
                rights = episodes['rights']
                download = rights['allow_download']
                if download == 1:
                    data.append("可以下载")
                else:
                    data.append("不能下载")
                print(data,"\n")
                big_data_list.append(data)
        wait(30)

    return big_data_list


# 访问并解码gzip压缩后的网址
def askURLDecode(url):
    # 模拟浏览器头部信息，向豆瓣服务器发送消息
    head = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    # 用户代理表示告诉豆瓣服务器我们是什么类型的浏览器，告诉浏览器我们可以接受什么水平的文件内容
    request = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request, context=context, timeout=5)
        html = response.read()
        # 发现是gzip压缩过的数据
        # 解码html
        buff = BytesIO(html)
        f = gzip.GzipFile(fileobj=buff)
        html = f.read().decode('utf-8')

    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)

    return html


# 访问正常网址
def askURL(url):
    # 模拟浏览器头部信息，向豆瓣服务器发送消息
    head = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    # 用户代理表示告诉豆瓣服务器我们是什么类型的浏览器，告诉浏览器我们可以接受什么水平的文件内容
    request = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request, context=context, timeout=5)
        html = response.read().decode("utf-8")

    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)

    return html


def saveData(data_list, save_path):
    # 创建workbook对象
    book = xlwt.Workbook(encoding="utf-8", style_compression=0)
    # 创建工作表
    sheet = book.add_sheet('哔哩哔哩电影', cell_overwrite_ok=True)
    col = ("电影名称", "电影链接", "资格", "播放数", "国家", "简介", "演员", "类型", "评分", "能否下载")
    for i in range(0, 10):
        # 列名
        sheet.write(0, i, col[i])
    for i in range(0, len(data_list)):
        print("第%d条" % (i+1))
        data = data_list[i]
        for j in range(0, 10):
            sheet.write(i+1, j, data[j])

    # 保存
    book.save(save_path)


if __name__ == '__main__':
    data_list = getData()
    save_path = "哔哩哔哩电影2.0.xls"
    saveData(data_list, save_path)
    print("爬取完毕")
