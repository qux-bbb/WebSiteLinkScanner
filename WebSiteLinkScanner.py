# coding:utf8

#网站静态页面扫描

import os
import random
import re
import time
from optparse import OptionParser
import urlparse
import requests

import sys
reload(sys)
sys.setdefaultencoding('utf8')

headers = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
	"Referer": "http://www.google.com",
}


# 一些文件 如 图片，js文件，css文件，不分析，直接跳过
ignore_tails = [".jpg", ".JPG", ".png", ".gif", ".ico", ".css", ".js", ".pdf", ".doc", ".docx", ".xls", ".xlsx",  ".ppt", "pptx", ".apk", ".wav", ".WAV", ".zip", ".rar", ".7z"]
def ignore_it(url):
	url_path = urlparse.urlparse(url).path
	for tail in ignore_tails:
		if url_path.endswith(tail):
			return True
	return False

# 判断是否为图片
img_tails = [".jpg", ".JPG", ".png", ".gif", ".ico"]
def is_img(url):
	url_path = urlparse.urlparse(url).path
	for tail in img_tails:
		if url_path.endswith(tail):
			return True
	return False

# 默认不保存图片
save_img_flag = False
# 保存图片 
def save_img(url):
	url_path = urlparse.urlparse(url).path
	img_name = url_path.split("/")[-1]
	res = ""

	try: # 有的时候会出现超时错误，包裹起来，有别的异常造成中断，所以捕获所有异常
		res = requests.get(url, headers = headers, timeout = 10)
	# except requests.exceptions.Timeout:
	except Exception as e:
		return
	open("img/" + img_name, "wb").write(res.content)
	return

# 访问延时，默认不延时
wait_time = 0

# 扫描完成响铃，默认不响铃
finish_bell = False

# 只扫描main_url所在目录
only_main_dir = False

# 保存所有的url
urls = []


def scan(main_url, urls_file):
	main_url = main_url.strip()
	# 种子url的添加
	res = ""
	try:
		res = requests.get(main_url, headers=headers, timeout=10)
	except Exception as e:
		print '[!] ' + str(e.__class__) + main_url
		return
	urls.append(res.url)

	urlparse_main_url = urlparse.urlparse(res.url)
	domain_url = urlparse_main_url.scheme + '://' + urlparse_main_url.netloc

	if only_main_dir:
		if urlparse_main_url.path:
			main_url_dir = domain_url + re.findall(r"(.*/)", urlparse_main_url.path)[0]
		else:
			main_url_dir = domain_url + '/'
	else:
		if domain_url != main_url and domain_url+'/' != main_url:
			urls.append(domain_url)

	for url in urls:
		if len(url) == 0: # href=''
			continue

		# 判断是否保存图片
		if save_img_flag and is_img(url):
			save_img(url)

		if ignore_it(url):
			print url.decode("utf8")
			urls_file.write(url + "\n")
			continue

		# 判断是否延时访问
		if wait_time != 0:
			real_wait_time = wait_time  - 1 +  random.random()*2  # 延时范围在wait_time前后1秒左右
			time.sleep(real_wait_time)

		res = ""
		try:
			res = requests.get(url, headers=headers, timeout=10)
		except Exception as e:
			print '[!] ' + str(e.__class__) + url
			continue
		code_str = str(res.status_code)
		if code_str.startswith('2') or code_str.startswith('3'):
			print res.url.decode("utf8")
			urls_file.write(res.url + "\n")

		# ignore没有忽略掉，但是不需要分析的类型  只分析页面
		if 'text/html' not in res.headers['Content-Type']:
			continue


		half_urls = re.findall(r"(?:href|src|action)\s?=\s?\"(.*?)\"", res.content)
		half_urls.extend(re.findall(r"(?:href|src|action)\s?=\s?\'(.*?)\'", res.content))
		
		for half_url in half_urls:
			join_url = urlparse.urljoin(res.url, half_url)

			if domain_url in join_url: # 在本域名下
				if join_url not in [res.url, half_url] and join_url not in urls: # urls里还没有
					if only_main_dir:
						if main_url_dir in join_url:
							urls.append(join_url)
					else:
						urls.append(join_url)

	urls_file.close()	
	print("The result saved in result.txt")

	# 扫描完成响铃，只在cmd和终端下有效，cmder下无效
	if finish_bell:
		for i in range(10):
			time.sleep(1)
			print("\a")


if __name__ == '__main__':

	parser = OptionParser(
        "Usage:    python WebSiteScanner.py [options]\n"
		"Example:  python WebSiteScanner.py -m http://hello.com/")
	parser.add_option("-m", "--main_url", dest="main_url", help="a main_url")
	parser.add_option("-s", "--save_image", action="store_true", dest="save_image", default=False, help="save images")
	parser.add_option("-t", "--wait_time", type="int", dest="wait_time", default=0, help="delay access time")
	parser.add_option("-b", "--bell_done", action="store_true", dest="finish_bell", default=False, help="after scan, give belling")
	parser.add_option("-o", "--only_main_dir", action="store_true", dest="only_main_dir", default=False, help="only scan main url dir")
	
	(options, args) = parser.parse_args()

	main_url = options.main_url
	save_img_flag = options.save_image
	wait_time = options.wait_time
	finish_bell = options.finish_bell
	only_main_dir = options.only_main_dir

	if main_url == None:
		parser.print_help()
		exit(0)

	# 如果要保存图片，先创建一个文件夹
	if save_img_flag:
		if not os.path.exists("img"):
			os.mkdir("img")
	
	urls_file = open("result.txt", 'w+')
	try:
		scan(main_url, urls_file)
	except KeyboardInterrupt:
		urls_file.close()
		print("Interrupted by user")
		exit()
