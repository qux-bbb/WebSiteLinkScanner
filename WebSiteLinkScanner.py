# coding:utf8

#网站静态页面扫描

import os # 用来创建文件夹
from optparse import OptionParser
import requests
import re
import time 
import random



# 加headers，绕过简单的反爬虫机制
headers = {
	"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
	"Referer": "http://www.google.com",
}


# 一些文件 如 图片，js，css文件，不用分析，直接跳过

ignore_tails = [".jpg", ".JPG", ".png", ".gif",".js", ".css", ".pdf", ".doc", ".xls",  ".ppt", "pptx", ".apk"]
def ignore_it(url):
	for tail in ignore_tails:
		if url.endswith(tail):
			return True
	return False

# 判断是否为图片
img_tails = [".jpg", ".png", ".gif", ".ico"]
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

def scan(domain):
	if domain[-1] == "/":  # 如果域名最后有 "/",就去掉
		domain = domain[0:-1]

	urls = [domain]
	base_url = re.findall(r"https?://(?:www\.)?(.*\..*?$)",domain)[0]  # 最基本的url，用来判断是否同网站
	for url in urls:
		print(url.decode("utf8"))  # 有的汉字直接输出乱码，所以decode一下  
		# 判断是否保存图片
		if is_img(url) and save_img_flag:
			save_img(url)

		if ignore_it(url):
			continue

		dir_url = url # 用来拼接不是http、https的链接
		if '/' in url[8:]:
			dir_url = re.findall(r'(https?://.*)/', url)[0]

		# 判断是否延时访问
		if wait_time != 0:
			real_wait_time = wait_time  - 1 +  random.random()*2  # 延时范围在wait_time前后1秒左右
			time.sleep(real_wait_time)

		res = ""
		try: # 有的时候会出现超时错误，包裹起来，有别的异常造成中断，所以捕获所有异常
			res = requests.get(url, headers = headers, timeout = 10)
		# except requests.exceptions.Timeout:
		except Exception as e:
			continue

		# 单引号是 有的重定向用的是单引号
		# \s? 是 有些 = 两边都有空格
		half_urls = re.findall(r"(?:href|src|action)\s?=\s?[\"\'](.*?)[\"\']", res.content) # 如果使用res.text,在保存时会出错
		for half_url in half_urls:

			if len(half_url) == 0: # 匹配为空的情况，需要跳过进行下一轮，比如 href="'+b+'"]
				continue

			if half_url.startswith("data:"): # 有的资源文件直接以 src形式写到html里，需要跳过
				continue
			if half_url.startswith("mailto:"): # 邮件链接，需要跳过
				continue			
			if half_url.startswith("javascript:"): # 有的js文件里包含 href="javascript:hello()"类似的形式，需要跳过
				continue

			if half_url[0:2] == "//": # 新的情况，还有这种形式的 //www.hello.com/sdf 做下预处理
				if "https" in domain:
					half_url = "https:" + half_url
				else:
					half_url = "http:" + half_url

			if "http" in half_url or "https" in half_url:
				if base_url in half_url: # 是本网站的url
					if half_url[-1] == '/':  # 有http://hello  http://hello/  其实是一种情况
						half_url = half_url[:-1]
					if half_url not in urls:
						urls.append(half_url)
			else: # 没有 http、https的url肯定是这个站的，只要根据情况区分就好了
				join_url = "" 
				if half_url[0] == '/':  # 这种情况直接从根目录算起
					join_url = domain + half_url
				elif half_url[0:2] == './':
					join_url = dir_url + half_url[1:]
				else:
					join_url = dir_url + "/" + half_url

				while "../" in join_url: # 这里需要把  hello/../  这样的形式去掉,直接用replace正则表达式失败了，不知道怎么回事
					if re.match(r"(/[a-zA-Z0-9\-_]+/\.\./)", join_url):
						join_url = re.sub(r'(/[a-zA-Z0-9\-_]+/\.\./)', "/", join_url)
					else:
						join_url = re.subn(r"\.\./","", join_url)[0] # 有的 ../写多了，如果上面没有匹配成功，就该把../全部删掉，跳出循环了
						break
				if join_url[-1] == '/':  # 有http://hello  http://hello/  其实是一种情况
					join_url = join_url[:-1]
				if join_url not in urls:
					urls.append(join_url)

	open("result.txt",'w').write("\n".join(urls))
	print("The result saved in result.txt")

	# 扫描完成响铃
	if finish_bell:
		for i in range(20):
			print("\a")


if __name__ == '__main__':

	parser = OptionParser(
        "Usage:    python WebSiteScanner.py [options]\nExample:  python WebSiteScanner.py -d http://hello.com")
	parser.add_option("-d", "--domain", dest="domain", help="a domain")
	parser.add_option("-s", "--save_image", action="store_true", dest="save_image", default=False, help="save images")
	parser.add_option("-t", "--wait_time", type="int", dest="wait_time", default=0, help="delay access time")
	parser.add_option("-b", "--bell_done", action="store_true", dest="finish_bell", default=False, help="after scan, give belling")
	(options, args) = parser.parse_args()

	domain = options.domain
	save_img_flag = options.save_image
	wait_time = options.wait_time
	finish_bell = options.finish_bell


	if domain == None:
		parser.print_help()
		exit(0)

	# 如果要保存图片，先创建一个文件夹
	if save_img_flag:
		if not os.path.exists("img"):
			os.mkdir("img")

	scan(domain)

