#coding:utf-8
#作者：公众号【码点小干货】
import socket,requests,chardet,re,json,os
from threading import Thread

def is_port_open(ip, port,timeout=1):
    """
    检查指定的IP地址和端口是否开放。
    :param ip: 目标服务器的IP地址。
    :param port: 要检查的端口。
    :param timeout: 连接尝试的超时时间。
    :return: 如果端口开放，返回True；否则返回False。
    """
    try:
        sock = socket.create_connection((ip, port), timeout)
        sock.close()  # 如果连接成功，关闭连接并返回True
        result = is_http_port(ip, port,timeout=1)
        return result
    except socket.error:
        return False  # 如果连接失败，抛出异常并返回False

def is_http_port(ip, port,timeout=2):
    #判断是否为http端口
    try:
        rsp = requests.get(f'http://{ip}:{port}', headers=headers, timeout=timeout)
        if rsp.status_code == 200:
            # 状态码等于200则正常
            if 'ZHGXTV' in rsp.text.upper():
                print(f'http://{ip}:{port} 智慧光迅酒店管理系统，正常访问\n')
                if ('zhgx', f'{ip}:{port}') not in valid_data:
                    valid_data.append(('zhgx', f'{ip}:{port}'))
            elif '/iptv/live/zh_cn.js' in rsp.text.lower():
                print(f'http://{ip}:{port} 智能桌面管理系统，正常访问\n')
                if ('znzm', f'{ip}:{port}') not in valid_data:
                    valid_data.append(('znzm', f'{ip}:{port}'))
            else:
                print(f'http://{ip}:{port} 未知系统或者其他WEB？？？')
            return True
        else:
            return False
    except Exception as e:
        return False

def check_iplist(info):
    #多线程扫描端口是否能通
    ip,port = info.strip().split(':')
    is_http_port(ip,port)
    parts = ip.split('.')
    ipprefix = '.'.join(parts[:3])
    T_list = []
    print(f'扫描{ipprefix}网段 端口{port}')
    for i in range(2,254):
        checkip = f'{ipprefix}.{i}'
        task = Thread(target=is_port_open,args=(checkip,port))
        task.start()
        T_list.append(task)
    for t in T_list:
        t.join()

def read_checkip():
    #读取当前文件夹下的ip合集
    info = []
    with open('iplist.txt','r') as f:
        data = f.readlines()
        for i in data:
            if i != '\n' and ':' in i:
                info.append(i.strip())
    return info

def program_judgment(info):
    #节目判断信息过滤替换
    info = info.strip()
    if 'CCTV' in info.upper() or '中央' in info.upper() or 'CETV' in info.upper():
        if '5+' not in info.upper():
            try:
                name, url = info.split(',')
                name = re.findall('\w\w\w\w\d{1,2}|\w\w\w\w-\d{1,2}|\w\w\w\w-\w{1,4}|\w\w\w\w\w{1,8}|中央\d{1,2}', name)[0]
                name = name.replace('-', '').replace('高清', '').replace('HD', '').replace('-CM-IPTV', '').replace(
                    '-Tel', '').replace(' ', '').replace('标清', '').replace('中央', 'CCTV').replace('超清', '').replace(
                    '画中画', '').replace('单音轨', '')
                ys.append(f'{name},{url}')
                return True
            except:pass
        else:
            name, url = info.split(',')
            ys.append(f'CCTV5+,{url}')
    elif '卫视' in info.upper():
        line = info.upper().replace('高清', '').replace('HD', '').replace('-CM-IPTV', '').replace('-Tel', '').replace(' ',
                                                                                                            '').replace(
            '+', '').replace('标清', '').replace('-', '').replace('超清', '').replace('画中画', '').replace('单音轨', '')
        ws.append(line.lower())
    elif '<br>' not in info.upper() and '' != info.upper() and info[0] != ',' and info[0] != '1':
        line = info.upper().replace('高清', '').replace('HD', '').replace('-CM-IPTV', '').replace('-Tel', '').replace(' ',
                                                                                                            '').replace(
            '+', '').replace('标清', '').replace('YD', '').replace('-', '').replace('超清', '').replace('画中画', '').replace(
            '单音轨', '')
        df.append(line.lower())

def zhgx_analysis(info):
    #智慧光讯解析
    url = f'http://{info}/ZHGXTV/Public/json/live_interface.txt'
    try:
        rsp = requests.get(url,headers=headers,timeout=3)
        rsp = str(rsp.content.decode(chardet.detect(rsp.content)['encoding']))
        for line in rsp.split('\r\n'):
            if ',' in line:
                if 'hls' in line:
                    line = re.sub('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', info,line)
                elif 'udp' in line or 'rsp' in line or 'rtsp' in line:
                    if '@' not in line:
                        line = line.replace('://','/')
                    elif '@' in line:
                        line = line.replace('://@','/')
                    line = line.split(',')[0] + ',' + f"http://{info}/%s"%line.split(',')[1]
                program_judgment(line)
    except Exception as e:
        print(e)

def znzm_analysis(info):
    #智能桌面解析
    url = f'http://{info}/iptv/live/1000.json'
    try:
        rsp = requests.get(url,headers=headers,timeout=3)
        rsp = rsp.content.decode(chardet.detect(rsp.content)['encoding'])
        data = json.loads(rsp)
        if data['code'] == 0:
            for line in data['data']:
                line = '{},{}'.format(line['name'], 'http://{}{}'.format(info, line['url']))
                if ',' in line:
                    if 'hls' in line:
                        line = re.sub('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}',
                                      info, line)
                    elif 'udp' in line or 'rsp' in line or 'rtsp' in line:
                        if '@' not in line:
                            line = line.replace('://', '/')
                        elif '@' in line:
                            line = line.replace('://@', '/')
                        if 'http' not in line:
                            line = line.split(',')[0] + ',' + f"http://{info}/%s" % line.split(',')[1]
                        else:
                            line = line.split(',')[0] + ',' + f"%s/" % line.split(',')[1]
                    program_judgment(line)
        else:
            print('当前地址无效！')
    except:pass

def write_iptv(ys,ws,df):
    filename = 'live.txt'
    if os.path.isfile(filename):
        os.remove(filename)
    all = open('live.txt', 'a', encoding='utf-8')
    all.write("央视频道,#genre#\n")
    for i in set(ys):
        all.write(i+'\n')
    all.write("卫视频道,#genre#\n")
    for i in set(ws):
        all.write(i+'\n')
    all.write("地方频道,#genre#\n")
    for i in set(df):
        all.write(i+'\n')

def main():
    #主函数
    for line in read_checkip():
        check_iplist(line)
    for line in valid_data:
        if line != '':
            if line[0] == 'zhgx':
                zhgx_analysis(line[1].strip())
            elif line[0] == 'znzm':
                znzm_analysis(line[1].strip())
            else:
                print('不支持的解析')
    write_iptv(ys,ws,df)
    print('获取完成！输出到当前文件夹live.txt中')

if __name__ == '__main__':
    print('-' * 50)
    print('直接或间接使用本仓库或者软件内容的个人和组织，仅仅用作学习交流！\n应在24小时内完成学习和研究，并及时删除！！\n数据接口均来自于互联网，禁止商业行为，一切与商业有关违法行为与本人无关\n')
    print('作者：公众号【码点小干货】')
    print('-' * 50)
    ys = []
    ws = []
    df = []
    valid_data = []
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"}
    main()