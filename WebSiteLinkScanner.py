# coding:utf8

#网站静态页面扫描


from optparse import OptionParser
import requests
import re

Referer = "http://www.google.com"
# 加headers，绕过简单的反爬虫机制
headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
"Referer": Referer,
}

# 一些文件 如 图片，js，css文件，不用分析，直接跳过

ignore_tails = [".jpg", ".png", ".gif",".js", ".css", "pdf"]
def ignore_it(url):
	for tail in ignore_tails:
		if url.endswith(tail):
			return True
	return False



def scan(domain):
	if domain[-1] == "/":  # 如果域名最后有 "/",就去掉
		domain = domain[0:-1]
	Referer = domain
	urls = [domain]
	base_url = re.findall(r"https?://(?:www\.)?(.*\..*?$)",domain)[0]  # 最基本的url，用来判断是否同网站
	for url in urls:
		print(url)
		if ignore_it(url):
			continue

		dir_url = url # 用来拼接不是http、https的链接
		if '/' in url[8:]:
			dir_url = re.findall(r'(https?://.*)/', url)[0]

		try: # 有的时候会出现超时错误，包裹起来
			res = requests.get(url, headers = headers, timeout = 10)
		except requests.exceptions.Timeout:
			continue

		# 单引号是有的重定向用的是单引号
		# \s? 是有些 = 两边都有空格
		half_urls = re.findall(r"(?:href|src)\s?=\s?[\"\']([a-zA-Z0-9:_\-\.\/]+)[\"\']", res.content)
		for half_url in half_urls:
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
					join_url = re.sub(r'(/[a-zA-Z0-9\-_]+/\.\./)', "/", join_url)

				if join_url[-1] == '/':  # 有http://hello  http://hello/  其实是一种情况
					join_url = join_url[:-1]
				if join_url not in urls:
					urls.append(join_url)

	open("result.txt",'w').write("\n".join(urls))
	print("The result saved in result.txt")


if __name__ == '__main__':

	parser = OptionParser(
        "Usage:    python WebSiteScanner.py [options]\nExample:  python WebSiteScanner.py -d http://hello.com")
	parser.add_option(
        "-d", "--domain", dest="domain", help="a domain")
	(options, args) = parser.parse_args()

	domain = options.domain

	if domain == None:
		parser.print_help()
		exit(0)

	scan(domain)
