#!/usr/bin/env python
# coding=utf-8
import urllib2
import cookielib
import StringIO
import gzip
import re
import sys
import getopt
import os
import fanhaodatabase as fhdb

def cprint(color,msg):
    if color == 'r':
        fore=31
    elif color=='g':
        fore=32
    elif color=='b':
        fore=36
    elif color=='y':
        fore=33
    else:
        fore=37
    c='\x1B[%d;%dm'%(1,fore)
    print '%s%s\x1B[0m'%(c,msg)

def ccontinueprint(color,msg):
    if color == 'r':
        fore=31
    elif color=='g':
        fore=32
    elif color=='b':
        fore=36
    elif color=='y':
        fore=33
    else:
        fore=37
    c='\x1B[%d;%dm'%(1,fore)
    print '%s%s\x1B[0m'%(c,msg),

def gethtml(url):
    cookie=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    urllib2.install_opener(opener)
    myheader={"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Encoding":"gzip, deflate","Accept-Language":"en-US,en;q=0.5","Connection":"keep-alive","User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:26.0) Gecko/20100101 Firefox/26.0"}
    request=urllib2.Request(url,headers=myheader)
    response=urllib2.urlopen(request)
    html_zip=response.read()
    stringdata=StringIO.StringIO(html_zip)
    gzipper=gzip.GzipFile(fileobj=stringdata)
    html=gzipper.read()
    return html

def getkeywordfromhtml(pattern,html):
    reg=re.compile(pattern)
    return reg.findall(html)

def getinfohash(html):
    resultinfohash=getkeywordfromhtml('/information/(?P<infohash>[A-Z0-9]{40})',html)
    resultname=getkeywordfromhtml('<tr><td class="name">(?P<name>.+)</td><td class="size">',html)
    return resultinfohash,resultname
    
def gettitle(html):
    title=getkeywordfromhtml('<title>(?P<title>.+)</title>',html)
    return title

def gettime(html):
    time=getkeywordfromhtml('<td class="header">发行日期:</td>\n\t<td class="text">(?P<time>.+)</td>',html)
    return time
    
def getactor(html):
    actor=getkeywordfromhtml('<a href="vl_star.php\?s=(?P<id>\w+)" rel="tag">(?P<actor>\S+)</a>',html)
    return actor


def geturltorrent(fanhao):
    return 'http://www.torrentkitty.com/search/'+fanhao+'/'

def geturljav(fanhao):
    return 'http://www.javlibrary.com/cn/vl_searchbyid.php?keyword='+fanhao

def printmulti(result):
    cprint('r','搜到了好几部')
    cprint('b','--------------------------')
    for urlid,url,title,fanhao in result:
        cprint('g',fanhao)
        cprint('g',title.decode('utf-8'))
        cprint('b','--------------------------')
def getmulti(html):
    return getkeywordfromhtml('v class="video" id="(\w+)"><a href="(\S+)" title="(.+)"><div class="id">(\S+)</div>',html)

def printtorrent(fanhao):
    html=gethtml(geturltorrent(fanhao))
    infohash,name=getinfohash(html)
    if len(infohash)!=len(name):
        print 'reg erro'
        sys.exit(0)
    print '-------------------'
    print '得到的种子信息是：'
    for i in range(len(infohash)):
        print infohash[i]+"   ",
        cprint('b',name[i].decode('utf-8'))
    return infohash

def printactor(result):
    if len(result)==0:
        return 0 
    ccontinueprint('y','演员：')
    for i in result:
        ccontinueprint('r',i[1].decode('utf-8'))
        print ';',
    print " "
    return len(result)
   

def usage():
    print '''-d fanhao download 
             -a fanhao add the fanhao into library
             -s fanhao skip the info and list the torrent info directly'''
    sys.exit(0)
    
def isfanhao(fanhao):
    reg=re.compile('([a-zA-Z].)([0-9]*)')
    if reg.sub('',fanhao)=='':
        return True
    return False

def getkeys(list):
    result=[]
    for i in list:
        result.append(i[0])
    return result

if __name__=='__main__':
    db=fhdb.database()
    if len(sys.argv)==1:
        usage()
    optionlist,args=getopt.getopt(sys.argv[1:],'dsl')
    options=getkeys(optionlist)
    if args==[] and '-l' in options:
        #显示未完成的列表
        cprint('r','如下影片未完成')
        for fanhao,infohash in db.queryuncomplete():
            ccontinueprint('r',fanhao)
            print "     ",
            ccontinueprint('r',infohash)
            print ""
        sys.exit(0)      
    if not isfanhao(args[0]):
        usage()
    print options,args
    if '-s' in options:
        infohashs=printtorrent(args[0])
    else:
        #打印演员以及影片的信息,还有种子的信息
        html1=gethtml(geturljav(args[0]))
        title=gettitle(html1)
        if title==[]:
            print 'no info'
            sys.exit(0)
        else:
            actor=getactor(html1)
            cprint('y',args[0]+'信息是：')
            if printactor(actor)==0:
                printmulti(getmulti)
                sys.exit(0)
            cprint('r',title[0])
            infohashs=printtorrent(args[0])
    if '-d' in options:
        #说明需要下载
        if db.isexist(fanhao=args[0]):
            print '已经下过该影片'
            if not db.iscomplete(fanhao=args[0]):
                print '但是该电影没有完成'
                commanddl='lx download %s --continue'%infohashs[0]
                os.system(commanddl)
            else:
                sys.exit(0)
        else:
            commanddl='lx download %s'%infohashs[0]
            db.add(args[0],infohashs[0],0)
            os.system(commanddl)

   
