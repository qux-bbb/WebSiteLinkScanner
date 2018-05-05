# WebSiteLinkScanner
网站内链接扫描,简单的做一些网站内的链接搜集,也可以保存图片   

## 选项说明  
<pre>
-m  https://www.baidu.com/  # 就是要扫描的网站  
-s                          # 有此选项可保存图片  
-t  3                       # 请求一个链接等待时间，单位是秒，默认为0，如设置3秒，等待时间为2~4秒之间的一个随机值  
-b                          # 有此选项，在扫描结束后发出警告声提示扫描结束，提示10声，在cmder下无效  
-o                          # 有此选项则只扫描所给url所在目录下的url  
</pre>

## 运行环境
python2.7，模块除了requests之外，别的都是python自带的  
举个运行例子：  
```bash
python WebSiteLinkScanner.py -m http://www.baidu.com/ -s -t 2 -b -o
```