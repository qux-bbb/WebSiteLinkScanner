# coding:utf8

#网站静态页面扫描

import os
import random
import re
import time
from optparse import OptionParser

import requests

headers = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
	"Referer": "http://www.google.com",
}


# 一些文件 如 图片，css文件，不用分析，直接跳过
ignore_tails = [".jpg", ".JPG", ".png", ".gif", ".ico", ".css", ".pdf", ".doc", ".docx", ".xls", ".xlsx",  ".ppt", "pptx", ".apk", ".wav", ".WAV"]
def ignore_it(url):
	for tail in ignore_tails:
		if url.endswith(tail):
			return True
	return False

# 判断是否为图片
img_tails = [".jpg", ".JPG", ".png", ".gif", ".ico"]
def is_img(url):
	for tail in img_tails:
		if url.endswith(tail):
			return True
	return False

# 默认不保存图片
save_img_flag = False
# 保存图片 
def save_img(url):
	img_name = url.split("/")[-1]
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

# 最大url长度限制，默认为600，超过直接忽略
max_url_len = 600

# 默认不扫描子域名，如果扫描子域名，结果太多，而且实际上已经跨网站了
sub_domain = False

# 保存所有的url
urls = []

def scan(main_url):
	urls_file = open("result.txt",'w+')
	main_url = main_url.strip()
	if main_url.endswith("/"):  # 如果域名最后有 "/",就删除
		main_url = main_url[:-1]

	urls_file.write(main_url + "\n")
	urls.append(main_url)
	if sub_domain:
		base_url = re.findall(r"https?://(?:www\.)?(.*\..*?$)",main_url)[0]  # 最基本的url，用来判断是否同网站，包括子域名
	else:
		base_url = re.findall(r"(https?://(?:www\.)?.*\..*$)",main_url)[0]  # 最基本的url，用来判断是否同网站，不包括子域名
		
	for url in urls:
		print(url.decode("utf8"))  # 有的汉字直接输出乱码，所以decode一下  
		# 判断是否保存图片
		if is_img(url) and save_img_flag:
			save_img(url)

		if ignore_it(url):
			continue

		# 判断是否延时访问
		if wait_time != 0:
			real_wait_time = wait_time  - 1 +  random.random()*2  # 延时范围在wait_time前后1秒左右
			time.sleep(real_wait_time)

		res = ""
		try: # 有的时候会出现超时错误，包裹起来，有别的异常造成中断，所以捕获所有异常
			res = requests.get(url, headers = headers, timeout = 10)
		# except requests.exceptions.Timeout:
		except Exception as e:
			print '[!] ' + str(e.__class__)
			continue

		# 单引号是 有的重定向用的是单引号
		# \s? 是 有些 = 两边都有空格
		half_urls = re.findall(r"(?:href|src|action)\s?=\s?[\"\'](.*?)[\"\']", res.content) # 如果使用res.text,在保存时会出错
		for half_url in half_urls:

			half_url_len = len(half_url)
			if half_url_len == 0 or half_url_len > max_url_len: # 匹配为空的情况，需要跳过进行下一轮，比如 href="'+b+'"]; 太长也直接略过
				continue

			if half_url in ['#', '.']: # 指本网页，直接忽略
				continue
			if half_url.startswith("data:"): # 有的资源文件直接以 src形式写到html里，需要跳过
				continue
			if half_url.startswith("mailto:"): # 邮件链接，需要跳过
				continue			
			if half_url.startswith("javascript:"): # 有的js文件里包含 href="javascript:hello()"类似的形式，需要跳过
				continue

			if half_url.startswith("//"):  # 新的情况，还有这种形式的 //www.hello.com/sdf 做下预处理
				if "https" in main_url:
					half_url = "https:" + half_url
				else:
					half_url = "http:" + half_url

			if "http" in half_url or "https" in half_url:
				if base_url in half_url: # 是本网站的url
					if len(half_url) > max_url_len: # 长度超过指定长度即放弃
						continue
					if half_url not in urls:
						urls_file.write(half_url + "\n")
						urls.append(half_url)
			else: # 现在没有 http、https的url肯定是这个站的，只要根据情况区分就好了

				tmp_url = url  # 去除问号的影响，比如这样的：http://a.com/b?c=http://b.com/
				if '?' in url:
					tmp_url = url.split('?')[0]
				dir_url = tmp_url  # 用来拼接不是http、https的链接
				if '/' in tmp_url[8:]:
					dir_url = re.findall(r'(https?://.*)/', tmp_url)[0]

				join_url = "" # 合并之后的完整url
				if half_url.startswith('/'):  # 这种情况直接从根目录算起
					join_url = main_url + half_url
				elif half_url.startswith('./'):
					join_url = dir_url + half_url[1:]
				elif half_url == '..':  # 上级目录
					join_url = dir_url
				else:
					join_url = dir_url + "/" + half_url

				while "../" in join_url: # 这里需要把  hello/../  这样的形式去掉
					if re.match(r"(/[a-zA-Z0-9\-_]+/\.\./)", join_url):
						join_url = re.sub(r'(/[a-zA-Z0-9\-_]+/\.\./)', "/", join_url)
					else:
						join_url = re.subn(r"\.\./","", join_url)[0] # 有的 ../写多了，如果上面没有匹配成功，就该把../全部删掉，跳出循环了
						break

				if len(half_url) > max_url_len: # 长度超过指定长度即放弃
						continue
				if join_url not in urls:
					urls_file.write(join_url + "\n")
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
        "Usage:    python WebSiteScanner.py [options]\nExample:  python WebSiteScanner.py -m http://hello.com")
	parser.add_option("-m", "--main_url", dest="main_url", help="a main_url")
	parser.add_option("-s", "--save_image", action="store_true", dest="save_image", default=False, help="save images")
	parser.add_option("-t", "--wait_time", type="int", dest="wait_time", default=0, help="delay access time")
	parser.add_option("-b", "--bell_done", action="store_true", dest="finish_bell", default=False, help="after scan, give belling")
	parser.add_option("-l", "--len_url", type="int", dest="max_url_len", default=600, help="max len of url")
	parser.add_option("-z", "--sub_domain", action="store_true", dest="sub_domain", default=False, help="scan include other subdomain")
	
	(options, args) = parser.parse_args()

	main_url = options.main_url
	save_img_flag = options.save_image
	wait_time = options.wait_time
	finish_bell = options.finish_bell
	max_url_len = options.max_url_len
	sub_domain = options.sub_domain


	if main_url == None:
		parser.print_help()
		exit(0)

	# 如果要保存图片，先创建一个文件夹
	if save_img_flag:
		if not os.path.exists("img"):
			os.mkdir("img")
	
	try:
		scan(main_url)
	except KeyboardInterrupt:
		print("Interrupted by user")
		exit()
