# -*- coding: utf-8 -*-

"""
Created on Tue 2020/09/25
本程序用于新奥公司提供的车在数据终端的数据集的测试，理解数据结构，解析数据含义，转化为方便处理的格式
本程序使用百度地图，pyecharts包

@author: Zhwh-notbook
"""
import pandas as pd
import os
import platform

import requests
import datetime
import time
import math
import json

from pyecharts.charts import BMap as baidu_map
from pyecharts import options as opts
import webbrowser
import statsmodels.api as sm

import pretty_errors

pretty_errors.activate()

# --------------------------------定义全局变量 百度开发者key与数字签名 ------------------------

global KEY, EARTH_REDIUS
KEY = 'iHDcbVaHkRo6xz149QBiqlrn2FAbwX6b'
EARTH_REDIUS = 6378.137  # 地球半径
requests.DEFAULT_RETRIES = 5

# --------------------------------------------操作百度地图--------------------------


class BMap(object):
    """
    百度地图sdk，编写时间2020-11-13
    """

    def __init__(self, ak_key, output="json"):
        """
        初始化，需要密钥
        :param ak_key: 密钥
        :param output: 输出，json或xml；设置 JSON 返回结果数据将会以JSON结构构成；如果设置 XML 返回结果数据将以 XML 结构构成。
        """
        self.keys = ak_key
        self.output = output

    def get_data(self, url: str, params: dict):
        """
        获取基础数据
        :param url: 链接地址: Str类型
        :param params: 请求参数，Dict类型
        :return: 返回请求值
        """
        data = False
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                if self.output == 'JSON':
                    data = response.json()
                else:
                    data = response.text
        except requests.exceptions.ConnectionError:
            requests.status_codes = "Connection refused"

        # response = requests.get(url, params=params)
        return data

    def location_decode(self, location, poi_type=None, radius=500, extensions_road="false", callback=None):
        """
        地理位置转经纬度,官方文档参考：https://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding-abroad
        示例：http://api.map.baidu.com/reverse_geocoding/v3/?ak=您的ak&output=json&coordtype=wgs84ll&location=31.225696563611,121.49884033194
        """

        url = "http://api.map.baidu.com/reverse_geocoding/v3/?parameters"
        params = {
            'ak': self.keys,
            # 'ak': 'iHDcbVaHkRo6xz149QBiqlrn2FAbwX6b',
            'location': location,
            'poi_types': poi_type,
            'radius': radius,
            'extensions_road': extensions_road,
            'output': self.output,
            # 'output': "json",
            'callback': callback,
        }

        if location is None:
            print('location不能为空')

        data = self.get_data(url, params)
        return data


# ---------------------------------------操作GPS信息------------------------------
class Gps(object):
    """
    高德地图sdk，编写时间2020-08-20
    """

    def __init__(self, earth_radius):
        self.earth_radius = earth_radius

    def rad(self, d):
        return d * math.pi / 180.0

    def getDistance(self, lat1, lng1, lat2, lng2):
        radLat1 = self.rad(lat1)
        radLat2 = self.rad(lat2)
        a = self.rad(lat1) - self.rad(lat2)
        b = self.rad(lng1) - self.rad(lng2)
        s = 2 * math.asin(math.sqrt(
            math.pow(math.sin(a / 2), 2) + math.cos(radLat1) * math.cos(radLat2) * math.pow(math.sin(b / 2), 2)))
        s = s * self.earth_radius * 1000
        return s

    def haversine(self, lon1, lat1, lon2, lat2):  # 经度1，纬度1，经度2，纬度2 （十进制度数）
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # 将十进制度数转化为弧度
        lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

        # haversine公式
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return c * self.earth_radius * 1000


# ----------------------------- 读取新奥公司监控GPS数据文件 ------------------------------------

# 读取程序需要的数据源等配置信息
def get_config():
    operating_system = platform.system()
    scrip_dir = os.path.abspath('.')
    # scrip_dir = scrip_dir.replace('/data_import', '')

    # 读取位于当前目录下的配置文件
    if operating_system == 'Windows':
        file_name = os.path.join(scrip_dir, "config_windows.ini")
    elif operating_system == 'Linux':
        file_name = os.path.join(scrip_dir, "config_linux.ini")
    else:
        pass

    with open(file_name, "r", encoding="UTF-8") as config_file:
        text_lines = config_file.readlines()

        for line in text_lines:
            # 处理空行
            if not line.isspace():  # 判断是否是空行
                if not line.startswith("#"):  # 判断是否属是注释行
                    # 根据line字符串，提取信息
                    print(line)
                    if "DATA_PATH" in line:
                        data_path = line.replace('DATA_PATH=', '')
                        data_path = data_path.replace('\n', '')
                    if "MAP_SAVE_PATH" in line:
                        map_save_path = line.replace('MAP_SAVE_PATH=', '')
                        map_save_path = map_save_path.replace('\n', '')
                    if "DATA_SAVE_PATH" in line:
                        data_save_path = line.replace('DATA_SAVE_PATH=', '')
                        data_save_path = data_save_path.replace('\n', '')
                else:
                    pass
            else:
                pass
    config_file.close()
    return data_path, map_save_path, data_save_path


# 获取指定文件夹内的文件夹名称以及文件列表
def get_data_file_list(DATA_PATH):
    operating_system = platform.system()

    # 判断试验数据目录中是否包含子文件夹，如果包含子文件夹，构建dir列表，保存dir信息
    if os.path.isdir(DATA_PATH):
        dir_list = []
        for (root, dirs, files) in os.walk(DATA_PATH):
            for sub_dir in dirs:
                dir_list.append(sub_dir)

        if len(dir_list) > 0:
            print('指定路径', DATA_PATH, '文件夹包含子文件夹，共', len(dir_list), '个子文件夹')
        else:
            print('指定路径', DATA_PATH, '文件夹不包含子文件夹')
            if operating_system == 'Windows':
                path_list = DATA_PATH.split('\\')  # 将地址以地址分隔符拆分
            elif operating_system == 'Linux':
                path_list = DATA_PATH.split('/')  # 将地址以地址分隔符拆分
            dir_list = [path_list[len(path_list) - 1]]

    else:
        print('指定路径', DATA_PATH, '是一个数据文件')
        if operating_system == 'Windows':
            path_list = DATA_PATH.split('\\')  # 将地址以地址分隔符拆分
        elif operating_system == 'Linux':
            path_list = DATA_PATH.split('/')  # 将地址以地址分隔符拆分
        dir_list = [path_list[len(path_list) - 1]]

    # 将数据文件夹内所有试验数据路径存入列表
    DATA_Format = [".xlsx", ".xls"]
    file_list = []
    for (root, dirs, files) in os.walk(DATA_PATH):
        for filename in files:
            # print(filename)
            if os.path.splitext(filename)[1] in DATA_Format:
                file_list.append(os.path.join(root, filename))
                print(os.path.join(root, filename))
    print('指定路径', DATA_PATH, '文件夹包括子文件夹，共包括', len(file_list), '个数据文件')

    # 将数据文件夹名字，与数据文件绝对路径对应，汇总为数据框
    colnames = ['dir', 'file_path']
    data_files = pd.DataFrame(columns=colnames)
    for i in file_list:
        for j in dir_list:
            # 如果文件路径中包含scenario名字，则加以区分
            if i.find(j) != -1:
                temp = pd.DataFrame([[j, i]], columns=colnames)
                data_files = pd.concat([data_files, temp], ignore_index=True, sort=False)

    # 增加数据文件夹名称的标签项
    data_files['file_name'] = 'INF'
    for i in range(len(data_files.index)):
        path_temp = data_files['file_path'].iloc[i]
        if operating_system == 'Windows':
            path = path_temp.split('\\')  # 将地址以地址分隔符拆分
        elif operating_system == 'Linux':
            path = path_temp.split('/')  # 将地址以地址分隔符拆分
        else:
            pass
        L = len(path)
        file_name = path[L - 1][:-5]
        data_files.loc[data_files.index[i], 'file_name'] = file_name

    return data_files


# 导入试验数据，标准化列名
def get_data(file_path):
    # 定义拉丁字符的变量名
    col_names = ['truck_license',
                 'long_GPS', 'lat_GPS',
                 'long_BaiDu', 'lat_BaiDu',
                 'speed', 'direction', 'time',
                 ]

    print('正在导入路径夹为', file_path, '的数据')

    #  导入试验数据
    temp_import = pd.read_excel(io=file_path,
                                sheet_name=0,
                                # header=None,
                                skiprows=0,  # 不导入第一行汉字数据
                                names=col_names,
                                # engine='openpyxl'
                                )

    return temp_import


# 调用Gps类，计算相邻GPS坐标之间的直线距离
def gps_distance(earth_r, data):
    gps = Gps(earth_radius=earth_r)
    data['distance_gps'] = 0.0
    for i in range(len(data)):
        if i == 0:
            data['distance'].values[i] = 0.0
        else:
            lat1 = data['lat_GPS'].iloc[i - 1]
            lng1 = data['long_GPS'].iloc[i - 1]
            lat2 = data['lat_GPS'].iloc[i]
            lng2 = data['long_GPS'].iloc[i]
            data['distance_gps'].values[i] = gps.getDistance(lat1=lat1,
                                                             lng1=lng1,
                                                             lat2=lat2,
                                                             lng2=lng2
                                                             )

    return data


# 计算相邻GPS坐标之间的加速度、行程时间、转角速度
def gps_dataAdd(data):
    data['acc'] = 0.0
    data['driving_time'] = 0.0
    data['turn_speed'] = 0.0
    data['distance'] = 0.0

    for i in range(len(data)):

        if i == 0:
            data['acc'].values[i] = 0.0
            data['driving_time'].values[i] = 0.0
            data['turn_speed'].values[i] = 0.0
            data['distance'].values[i] = 0.0
        else:
            speed1 = data['speed'].iloc[i - 1] / 3.6
            speed2 = data['speed'].iloc[i] / 3.6
            turn1 = data['direction'].iloc[i - 1]
            turn2 = data['direction'].iloc[i]
            time1 = data['time'].iloc[i - 1]
            time2 = data['time'].iloc[i]

            time1 = datetime.datetime.strptime(str(time1), "%Y-%m-%d %H:%M:%S")
            time2 = datetime.datetime.strptime(str(time2), "%Y-%m-%d %H:%M:%S")

            driving_time = (time2 - time1).seconds

            data['driving_time'].values[i] = driving_time
            # print(time1, time2, (time2 - time1).seconds)

            if driving_time == 0:
                data['acc'].values[i] = 0.0
                data['distance'].values[i] = 0.0
            else:
                data['acc'].values[i] = (speed2 - speed1) / driving_time
                data['distance'].values[i] = 0.5 * (speed2 + speed1) * driving_time

            t = abs(turn2 - turn1)
            if t > 180:
                t = 360 - 180

            if driving_time == 0.:
                data['turn_speed'].values[i] = 0.0
            else:
                data['turn_speed'].values[i] = t / driving_time

    return data


# 利用百度 web API 逆编码经纬度数据，提取道路名称信息以及修正位置GPS坐标
def Bd_map_decode(data):
    sample = data.copy()
    sample['address'] = ''
    sample['province'] = ''
    sample['city'] = ''
    sample['district'] = ''
    sample['road_name'] = ''
    sample['bmap_distance'] = ''
    sample['remarks'] = ''

    # 利用百度 web API通过经纬度坐标 逆编码获取道路信息
    bmap = BMap(ak_key=KEY, output="json")
    for i in range(len(sample)):

        lat = sample['lat_BaiDu'].iloc[i]
        long = sample['long_BaiDu'].iloc[i]
        lat = round(lat, 5)
        long = round(long, 5)

        location = str(lat) + ',' + str(long)
        decode = bmap.location_decode(location=location,
                                      poi_type='出入口',
                                      radius=None,
                                      extensions_road="true",
                                      callback=None,
                                      )
        if not decode:
            address = '百度地图访问出现问题'
            province = '百度地图访问出现问题'
            city = '百度地图访问出现问题'
            district = '百度地图访问出现问题'
            road_name = '百度地图访问出现问题'
            bmap_distance = '百度地图访问出现问题'
            remarks = '百度地图访问出现问题'
        else:
            decode_json = json.loads(decode)
            # print(decode_json['result']['roads'])
            address = decode_json['result']['formatted_address']
            city = decode_json['result']['addressComponent']['city']
            province = decode_json['result']['addressComponent']['province']
            district = decode_json['result']['addressComponent']['district']

            # 判断是否是交叉口
            if len(decode_json['result']['roads']) > 0:
                road_name = decode_json['result']['roads'][0]['name']
                bmap_distance = decode_json['result']['roads'][0]['distance']
                #  判断是否存在隧道、枢纽、服务区
                remarks = 'road'
                for j in range(len(decode_json['result']['roads'])):
                    r_name = decode_json['result']['roads'][j]['name']
                    if '服务区' in r_name:
                        remarks = 'service_area'
                    if '互通' in r_name:
                        remarks = 'interchange'
                    if '枢纽' in r_name:
                        remarks = 'transportation_hub'
                    if '隧道' in r_name:
                        remarks = 'tunnel'
                if len(decode_json['result']['roads']) > 1:
                    #  判断是否存在交叉口
                    road_if = True
                    for k in range(len(decode_json['result']['roads'])):
                        r_name = decode_json['result']['roads'][k]['name']
                        if '路' in r_name or '线' in r_name or '街' in r_name:
                            temp = True
                        else:
                            temp = False
                        road_if = road_if and temp

                    if road_if:
                        remarks = 'intersection'
            else:
                road_name = '没找到临近道路'
                remarks = 'no_result'
                bmap_distance = ''

        sample['address'].values[i] = address
        sample['province'].values[i] = province
        sample['city'].values[i] = city
        sample['road_name'].values[i] = road_name
        sample['district'].values[i] = district
        sample['bmap_distance'].values[i] = bmap_distance
        sample['remarks'].values[i] = remarks

        print(i, address, province, city, road_name, bmap_distance, remarks)
        time.sleep(1)  # 避免频繁访问网站造成错误，推迟执行时间

    return sample


# 判断数据中时间数据的秒位是否一直为零，如果是，返回FALSE，不是返回TRUE
def time_check(data):
    time_list = data['time']
    second = []
    for time_point in time_list:
        time_point = datetime.datetime.strptime(str(time_point), "%Y-%m-%d %H:%M:%S")
        time_str_list = str(time_point).split(':')
        if time_str_list[2] == '00':
            second.append(time_str_list[2])

    if len(second) >= len(time_list) * 0.8:
        result = False
    else:
        result = True

    return result


# 筛选超速的行为，打超速标签
def over_speed_check(import_data, speed_limit=75.0):
    data = import_data.copy()
    # 定义行为字段
    data['behavior'] = 'normal'

    for i in range(len(data)):
        speed = data['speed'].iloc[i]
        # print(speed)
        if speed > speed_limit:
            data['behavior'].values[i] = 'over_speed'
            # print('over_speed')
    return data


# 筛选急加速行为，打急加速标签
'''
针对每一辆车，采用个性化的判断准则
函数需要指定置信区间
'''


def ove_acc_check(import_data, confidence=0.95):
    data = import_data.copy()
    result = pd.DataFrame()  # 初始化数据框

    # 获取车辆拍照列表：
    truck_list = data.drop_duplicates(['truck_license'])['truck_license'].to_list()

    for truck in truck_list:
        truck_data = data[data['truck_license'] == truck]
        acc = truck_data[truck_data['acc'] > 0.]['acc'].to_list()
        dac = truck_data[truck_data['acc'] < 0.]['acc'].to_list()
        dac = [abs(i) for i in dac]
        # 数据confidence对应的累计密度概率
        acc_ecdf = sm.distributions.ECDF(acc)
        acc_std = acc_ecdf(confidence)

        dac_ecdf = sm.distributions.ECDF(dac)
        dac_std = dac_ecdf(confidence)

        for i in range(len(truck_data)):
            if truck_data['acc'].iloc[i] >= acc_std:
                if truck_data['behavior'].values[i] == 'normal':
                    truck_data['behavior'].values[i] = 'over_acc'
                else:
                    truck_data['behavior'].values[i] = truck_data['behavior'].values[i] + '+over_acc'
                print('acc_std=', acc_std)
                print(truck_data['acc'].iloc[i])

            if truck_data['acc'].iloc[i] <= (0 - dac_std):
                if truck_data['behavior'].values[i] == 'normal':
                    truck_data['behavior'].values[i] = 'over_dac'
                else:
                    truck_data['behavior'].values[i] = truck_data['behavior'].values[i] + '+over_dac'
                print('dac_std=', dac_std)
                print(truck_data['acc'].iloc[i])

        result = pd.concat([result, truck_data], ignore_index=True, sort=False)

    return result


# 调用百度地图绘制点图，不同类型风险行为采用不同颜色的标记
def plot_Bd_map(point_data, path):
    point_data = point_data[point_data['remarks'] != 'no_result']
    data = point_data[['lat_BaiDu', 'long_BaiDu', 'behavior']].copy()
    data.columns = ['lat', 'lon', 'behavior']

    # 地图中心
    map_center = [data['lon'].mean(), data['lat'].mean()]
    # 初始化百度地图
    bd_map = baidu_map(init_opts=opts.InitOpts(width="1920px", height="1080px"))
    bd_map.add_schema(baidu_ak=KEY,
                      center=map_center,
                      zoom=8, is_roam=True,
                      map_style=None,
                      )
    bd_map.set_global_opts(title_opts=opts.TitleOpts(title="新奥危险货物运输高风险路段位置图"))

    # 增加异常行为地理可视化标点

    color = ['red', 'green', 'blue', 'yellow', '#35226A', '#2D1C58', '#241747', '#1B1135']

    behavior_list = data.drop_duplicates(['behavior'])['behavior'].copy()  # 剔除重复的数据文件路径
    i = 0
    for behavior in behavior_list:
        behavior_data = data[data['behavior'] == behavior]
        behavior_color = color[i]
        i = i + 1

        map_data = []

        # 利用BMap.add_coordinate 将坐标值赋值给一个地点名称，并增加近BMap对象地理信息中
        for j in range(len(behavior_data)):
            name = behavior + str(j)
            longitude = behavior_data['lon'].iloc[j]
            latitude = behavior_data['lat'].iloc[j]

            bd_map.add_coordinate(name=name,
                                  longitude=longitude,
                                  latitude=latitude
                                  )
            map_data.append((name, 1))

        # 将地点增加到百度地图
        bd_map = bd_map.add(
            series_name=behavior,
            type_="scatter",
            data_pair= map_data,
            symbol_size=20,
            effect_opts=opts.EffectOpts(),
            label_opts=opts.LabelOpts(formatter="{b}", position="right", is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color=behavior_color),
        )

    # 将绘图结果输出至网页文件
    bd_map = bd_map.render(path)

    return bd_map


# ---------------------- 主程序 ----------------------

# 读取配置文件，获得数据文件路径
DATA_PATH, MAP_SAVE_PATH, DATA_SAVE_PATH = get_config()

# 获得所有数据文件的路径列表
data_files = get_data_file_list(DATA_PATH)

# 读取数据文件，利用百度API补全信息
files_list = data_files.drop_duplicates(['file_path'])['file_path'].copy()  # 剔除重复的数据文件路径
data_import = pd.DataFrame()  # 初始化数据框
for file_path in files_list:
    print(file_path)
    temp_import = get_data(file_path)
    truck_license = temp_import['truck_license'].iloc[0]
    # 剔除原始数据中存在的时间戳一样的数据
    temp_import = temp_import.drop_duplicates(['time'])
    # 只处理时间数据项完整的数据，缺少精确秒的数据不予处理
    if time_check(temp_import):
        print('正在处理牌照为', truck_license, '的车辆的轨迹数据')

        # 加速度、行程时间、转角速度
        temp_import = gps_dataAdd(temp_import)
        # 通过相邻GPS坐标计算的行程距离
        temp_import = gps_distance(earth_r=EARTH_REDIUS,
                                   data=temp_import)
        data_import = pd.concat([data_import, temp_import], ignore_index=True, sort=False)  # 将所有数据合并
    else:
        print('牌照为', truck_license, '的车辆的轨迹数据缺少秒数据，不予处理')
# 筛选超速以及急加速和急减速数据
over_check = over_speed_check(import_data=data_import,
                              speed_limit=80.0)

over_check = ove_acc_check(import_data=over_check, confidence=0.95)
# 异常行为数据点筛选
abnormal = over_check[over_check['behavior'] != 'normal']

abnormal = abnormal[abnormal['speed'] > 10]

# 补全百度坐标
abnormal = Bd_map_decode(data=abnormal)

# 轨迹可视化, 定义保存轨迹可视化html的文件名
save_file_name = "bmap_high_riak_road_sections.html"
if not os.path.exists(MAP_SAVE_PATH):
    os.mkdir(MAP_SAVE_PATH)
file_dir = os.path.join(MAP_SAVE_PATH, save_file_name)

# 将异常行为发生位置，可视化在百度地图上
bd_map = plot_Bd_map(point_data=abnormal,
                     path=file_dir)

webbrowser.open(file_dir)

# 将融合了逐桩坐标的试验数据储存在硬盘上
if not os.path.exists(DATA_SAVE_PATH):
    os.mkdir(DATA_SAVE_PATH)
all_data_path = os.path.join(DATA_SAVE_PATH, "all_data.csv")
print("有效数据保存在临时文件内，临时文件的保存路径为：", all_data_path)
over_check.to_csv(all_data_path, index=False, sep=',', encoding='utf_8_sig')

abnormal_data_path = os.path.join(DATA_SAVE_PATH, "abnormal_data.csv")
print("有效数据保存在临时文件内，临时文件的保存路径为：", all_data_path)
abnormal.to_csv(abnormal_data_path, index=False, sep=',', encoding='utf_8_sig')

