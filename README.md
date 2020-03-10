# autoGetEpisodes
自动跟踪并下载美剧资源，支持邮件通知  

## 2020.3.11  v1.1 增加下载完成通知功能
## 2020.3.7   v1.0 稳定版发布

##
基于Python3编写，从https://txmeiju.com 搜索关键词 ，筛选出剧集的magnet链接，调用aria2下载资源  
代码比较简单，根据配置文件生成剧集的缓存文件，然后根据缓存文件来下载剧集

** 建议跑在NAS的Ubuntu Docker里 ,添加cron任务定时执行 **  
docker设置的建议:  
映射一个nas共享目录给docker，用来存放下载的剧集  
安装好aria2，这里略过  
建议安装一个aria2前端方便查看任务，推荐AriaNG  https://github.com/mayswind/AriaNg  
然后以Daemon形式运行aria2
把docker的  
22端口 (ssh)
80端口（查看前端页面）、  
6800端口（aria2 rpc）  
6901端口（BT监听端口，在aria2配置文件里修改）  
6902端口(DHT监听端口，在aria2配置文件里修改)  
这些端口映射出来，保证你的电脑能访问到  
6901、6902要映射到公网，且内外端口要一致，否则aria2没有下载速度
另外自己要有公网IP，到路由器上看你的公网IP和www.ip138.com 上看到的是不是一致，如果不一致的话就请打电话给你的运营商，否则下载还是会没速度  
~~”您好，我家宽带没有公网IP，但我需要远程查看家里的视频监控设备，请帮我分配一个“~~

## INSTALL
    # wget https://github.com/hyperlau/autoGetEpisodes/raw/master/release/autoGetEpisodes_v1.0.zip  

下载失败就git clone吧。。   
    # git clone https://github.com/hyperlau/autoGetEpisodes.git

## HOW TO USE

首先编辑脚本修改配置文件路径  
    self.configFile=os.path.abspath('/usr/local/autoGetEpisodes/config.cfg')  
    
需要下载的剧集信息要写进配置文件里

    [global]
    #DO NOT CHANGE baseUrl and searchUrl
    baseUrl=https://txmeiju.com
    searchUrl=%(baseUrl)s/tv/search?s=
    # aria2
    aria2Url=http://localhost:6800/rpc
    aria2Token=0sdafujlk23nfdsau90coi2jl3knm823oihjfsdnf
    # download dir
    downloadDir=/autoGetEpisodes
    # cache
    cacheDir=/usr/local/autoGetEpisodes/cache
    # 抓取页面timeout
    requestTimeout=10
    # 抓取sleep时长 防止被封禁IP
    requestSleep=1

    # 日志
    logFile=/usr/local/autoGetEpisodes/log.txt
    logLevel=DEBUG

    [国土安全]
    # 用于搜索关键词
    keyWord_0=Homeland.S08
    # 用于筛选搜索结果的关键词
    keyWord_1=

    [实习医生格蕾]
    keyWord_0=Greys.Anatomy.S16
    keyWord_1=720P


首先自己要在网站上手动测试好要下载的剧集关键字（搜索框里输入的关键字）（配置文件里的keyword_0）  
例如：国土安全  
因为txmeiju的搜索仅支持连续字符的搜索，所以脚本支持二次筛选搜索结果  (配置文件里的keyword_1)  
例如: 1080P  
然后就可以生成缓存文件了  
    # python3 autoGetEpisodes.py -g  
    
缓存文件默认在cache目录下
因为搜索出的剧集列表可能有我们不想下载的，例如这一季我看到了第10集，那可以编辑缓存文件把不需要下载的剧集的skip改成yes  
这样就不会被添加到aria2里  
再运行：
    # python3 autoGetEpisodes.py -c  

就会开始下载  
以后每次运行-c参数就可以了  
添加到aria2的文件的skip标志会自动置为yes
当有新的剧集的时候就会只添加新的剧集到aria2里

# 下载完成后通知
如需要启用此功能，请去掉aria2配置文件如下选项的注释符号（#）：  
    on-download-complete=/usr/local/autoGetEpisodes/completeNotify.py

# 关于cron定时执行
    22 * * * * export LANG='C.UTF-8'; /usr/local/autoGetEpisodes/autoGetEpisodes.py -c  
因为脚本里有中文，配置文件里也有中文，脚本在终端下执行没问题，但到了crontab里就会报错，所以要加export LANG='C.UTF-8';

回头补一个ubuntu docker配置的小文档，里面会有中文相关配置，供大家参考

简单吧？


# 注意事项：  
1 如果生成缓存后修改了配置文件里已经存在的剧集配置的keyword，需要删除对应的缓存文件重新生成  
2 配置文件里的路径要用绝对路径  
3 邮件通知建议用qq邮箱，不用改代码，如果是普通SMTP服务器的话代码要小改一下
