# WebSiteLinkScanner
网站内链接扫描,只能简单的做一些网站内的链接搜集了  
可能不同的网站对headers中的Referer有不同的处理方法，比如百度Referer如果是www.baidu.com就不回应了，所以如果有这样的问题，可以去改改headers中的Referer  

## 选项说明  
<pre>-d  http://www.baidu.com  # 就是要扫描的域名  
-s                          # 有此选项可保存图片  
-t  3                       # 请求一个链接等待时间，单位是秒，默认为0，如设置3秒，等待时间为2~4秒之间的一个随机值  
-b                          # 有此选项，在扫描结束后发出警告声提示扫描结束，提示10声，在cmder下无效  
-l  500                     # 保存url最长长度，默认为600，超过600则不保存</pre>
