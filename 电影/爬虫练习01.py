# -*- codeing = utf -8 -*-
# @Time : 2021/7/21 下午7:00
# @Author : Cui Yangyang
# @File : 爬虫练习01.py
# @Software: PyCharm

from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import ssl
import re
import xlwt

# 使用ssl创建未验证的上下文，在url中传入上下文参数
context = ssl._create_unverified_context()


def main():
    base_url = "https://movie.douban.com/top250?start="

    # 获取网页
    data_list = getData(base_url)

    # 保存数据
    save_path = "豆瓣电影Top250.xls"
    saveData(data_list, save_path)


# 创建正则表达式对象，表示字符串的模式,影片链接的规则
findLink = re.compile(r'<a href="(.*?)">')

# 影片图片的链接
# re.S让换行符包含在字符中
findImgSrc = re.compile(r'<img.*src="(.*?)"', re.S)

# 影片片名
findTitle = re.compile(r'<span class="title">(.*)</span>')

# 影片评分
findRating = re.compile(r'<span class="rating_num" property="v:average">(.*)</span>')

# 评价人数
findJudge = re.compile(r'<span>(\d*)人评价</span>')

# 找到概况
findInq = re.compile(r'<span class="inq">(.*)</span>')

# 找到影片相关内容
findBd = re.compile(r'<p class="">(.*?)</p>', re.S)


# 获取网页
def getData(base_url):
    data_list = []
    # 调用获取页面信息的函数10次
    for i in range(0, 10):
        url = base_url + str(i * 25)
        # 保存获取到的网页源码
        html = askURL(url)

        # 逐一进行解析
        soup = BeautifulSoup(html, "html.parser")
        # 查找符合要求的字符串，形成列表
        for item in soup.find_all('div', class_="item"):
            # for item in soup.find_all('span', class_="title"):
            # 保存一部电影的所有信息
            data = []
            item = str(item)

            # 通过正则表达式来查找指定的链接
            link = re.findall(findLink, item)[0]
            data.append(link)

            # 添加图片
            imgSrc = re.findall(findImgSrc, item)[0]
            data.append(imgSrc)

            # 片名可能只有一个中文名，也有可能都有
            titles = re.findall(findTitle, item)
            if len(titles) == 2:
                # 中文名
                ctitle = titles[0]
                data.append(ctitle)
                # 去掉无关的符号，添加外文名
                otitle = titles[1].replace("/", "")
                data.append(otitle)
            else:
                data.append(titles[0])
                # 外文名留空
                data.append(' ')

            # 评分
            rating = re.findall(findRating, item)[0]
            data.append(rating)

            # 评价人数
            judgeNum = re.findall(findJudge, item)[0]
            data.append(judgeNum)

            # 添加概述
            inq = re.findall(findInq, item)
            if len(inq) != 0:
                # 去掉句号
                inq = inq[0].replace(".", "")
                data.append(inq)
            else:
                # 留空
                data.append(" ")

            bd = re.findall(findBd, item)[0]
            # 去掉br和斜杠
            bd = re.sub(r'<br(\s+)?/>(\s+)?', " ", bd)
            bd = re.sub('/', ' ', bd)
            # 去掉前后空格
            data.append(bd.strip())

            # 把处理好的一部电影信息放入data_list
            data_list.append(data)

    return data_list


# 得到指定一个URL的网页内容
def askURL(url):
    # 模拟浏览器头部信息，向豆瓣服务器发送消息
    head = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    # 用户代理表示告诉豆瓣服务器我们是什么类型的浏览器，告诉浏览器我们可以接受什么水平的文件内容
    request = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request, context=context)
        html = response.read().decode("utf-8")

    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    
    return html


# 保存数据
def saveData(data_list, save_path):
    # 创建workbook对象
    book = xlwt.Workbook(encoding="utf-8", style_compression=0)
    # 创建工作表
    sheet = book.add_sheet('豆瓣电影top250', cell_overwrite_ok=True)
    col = ("电影详情链接", "图片链接", "影片中文名", "影片外国名", "评分", "评价数", "概况", "相关信息")
    for i in range(0, 8):
        # 列名
        sheet.write(0, i, col[i])
    for i in range(0, 250):
        print("第%d条" % (i+1))
        data = data_list[i]
        for j in range(0, 8):
            sheet.write(i+1, j, data[j])

    # 保存
    book.save(save_path)

# 当程序执行时
if __name__ == '__main__':
    main()
    print("爬取完毕")
