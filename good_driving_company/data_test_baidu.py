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
import xlrd

import requests
import datetime
import time
import math
# import scipy.stats as stats
import json
# from urllib.parse import urlencode

import folium
from pyecharts.charts import BMap
from pyecharts import options as opts
import webbrowser
import statsmodels.api as sm

import pretty_errors

pretty_errors.activate()

# --------------------------------定义全局变量 高德开发者key与数字签名 ------------------------

global KEY, EARTH_REDIUS
KEY = 'iHDcbVaHkRo6xz149QBiqlrn2FAbwX6b'
EARTH_REDIUS = 6378.137  # 地球半径
# KEY = '771f529bb4d20b88fc847b8f1954b737'  # 吴楠提供的key
# SIG = 'b24f7386fd53fefd198f623dadb08598'
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


#  读取数据集中的xlsx文件

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
def Bd_map_decode(data, radius):
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


# 调用folium包绘制点图，不同类型风险行为采用不同的标记
def plot_map(map_type, point_data):
    if map_type == 'GPS':
        all_data = point_data[['lat_GPS', 'long_GPS', 'behavior']]
        all_data.columns = ['lat', 'lon', 'behavior']

        # 地图类型，google 卫星图
        map_tiles = 'https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        # 地图类型，google 地图
        # map_tiles = 'https://mt.google.com/vt/lyrs=h&x={x}&y={y}&z={z}'

    if map_type == 'Gaode':
        # all_data = point_data[['lat_GaoDe', 'long_GaoDe']]
        all_data = point_data[['lat_GaoDe', 'long_GaoDe', 'behavior']]
        all_data.columns = ['lat', 'lon', 'behavior']

        # 地图类型，高德街道图
        map_tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
        # 地图类型，高德卫星图
        # map_tiles = 'http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'

    # 地图中心
    map_center = [all_data['lat'].mean(), all_data['lon'].mean()]

    map_plot = folium.Map(location=map_center,
                          zoom_start=16,
                          tiles=map_tiles,
                          attr='default'
                          )

    color = ['red', 'green', 'blue', 'yellow',
             '#F0EDF9', '#E2DBF3', '#D3CAEE', '#B7A6E2', '#A895DD', '#9A83D7', '#8C71D1', '#7D60CC', '#6F4EC6',
             '#613DC1', '#5938B0', '#50329E', '#472D8D', '#3E277B', '#35226A', '#2D1C58', '#241747', '#1B1135',
             '#F0EDF9', '#E2DBF3', '#D3CAEE', '#C5B8E8', '#B7A6E2', '#A895DD', '#9A83D7', '#8C71D1', '#7D60CC',
             '#6F4EC6', '#613DC1', '#5938B0', '#50329E', '#472D8D', '#3E277B', '#35226A', '#2D1C58', '#241747',
             '#1B1135']  # 37种

    # for name, row in all_data.iterrows():
    #     if int(row['classlabel']) == -1:
    #         folium.Circle(radius=20, location=[row["lat"], row["lon"]], popup="离群--停车点:{0}".format(name),
    #                       color='black', fill=True, fill_color='black').add_to(map)
    #     else:
    #         i = int(row['classlabel'])
    #         folium.Circle(radius=20, location=[row["lat"], row["lon"]], popup="{0}类--停车点:{1}".format(i, name),
    #                       color=color[i], fill=True, fill_color=color[i]).add_to(map)

    behavior_list = all_data.drop_duplicates(['behavior'])['behavior'].copy()  # 剔除重复的数据文件路径
    i = 0
    for behavior in behavior_list:
        behavior_data = all_data[all_data['behavior'] == behavior]
        behavior_color = color[i]
        i = i + 1

        for name, row in behavior_data.iterrows():
            folium.CircleMarker(radius=20,
                                location=[row['lat'], row['lon']],
                                # popup="离群--停车点:{0}".format(name),
                                color=behavior_color,
                                fill=True,
                                fill_color=behavior_color
                                ).add_to(map_plot)
    # 增加随着鼠标显示经纬度
    map_plot.add_child(folium.LatLngPopup())

    return map_plot


# 调用百度地图绘制点图，不同类型风险行为采用不同的标记
def plot_Bd_map(point_data):
    data = point_data[['lat_BaiDu', 'long_BaiDu', 'behavior']].copy()
    data.columns = ['lat', 'lon', 'behavior']

    # 地图中心
    map_center = [data['lon'].mean(), data['lat'].mean()]
    # 初始化百度地图
    bd_map = BMap(init_opts=opts.InitOpts(width="2000px", height="1400px"))\
        .add_schema(
        baidu_ak=KEY,
        center=map_center,
        zoom=8,
        is_roam=True,
        map_style=None)\
        .set_global_opts(title_opts=opts.TitleOpts(title="新奥危险货物运输高风险路段位置图"))
    # 增加异常行为地理可视化标点

    color = ['red', 'green', 'blue', 'yellow', '#35226A', '#2D1C58', '#241747', '#1B1135']

    behavior_list = data.drop_duplicates(['behavior'])['behavior'].copy()  # 剔除重复的数据文件路径
    i = 0
    for behavior in behavior_list:
        behavior_data = data[data['behavior'] == behavior]
        behavior_color = color[i]
        i = i + 1

        map_data = []
        for j in range(len(behavior_data)):
            geo_coord = [behavior_data['lon'].iloc[j], behavior_data['lat'].iloc[j]]
            coord = [geo_coord, 1]
            # geo_coord.append(coord)
            # map_data.append(geo_coord)
            map_data.append(coord)

        bd_map = bd_map.add(
            series_name=behavior,
            type_="scatter",
            data_pair=map_data,
            symbol_size=12,
            # effect_opts=opts.EffectOpts(),
            # label_opts=opts.LabelOpts(formatter="{b}", position="right", is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color="purple"),
        )


        for name, row in behavior_data.iterrows():
            bd_map = bd_map.add(
                type_="effectScatter",
                series_name=behavior,
                data_pair=[behavior, row['lon'], row['lat']],
                symbol_size=12,
                effect_opts=opts.EffectOpts(),
                label_opts=opts.LabelOpts(formatter="{b}", position="right", is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(color=behavior_color),
            )

    bd_map = bd_map.render("bmap_high_riak_road_sections.html")
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
abnormal = Bd_map_decode(data=abnormal,
                         radius=300)  # 以GPS坐标周围300米为检索范围

# 轨迹可视化, 定义保存轨迹可视化html的文件名
save_file_name = 'abnormal_all.html'
if not os.path.exists(MAP_SAVE_PATH):
    os.mkdir(MAP_SAVE_PATH)
file_dir = os.path.join(MAP_SAVE_PATH, save_file_name)

map_type = 'Gaode'
map_plot = plot_map(map_type=map_type,
                    point_data=abnormal)
map_plot.save(file_dir)
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

# --------------------- 测试代码 ---------------------
# sample = data_import[data_import['speed'] > 10]
# sample = sample.iloc[10000: 12000]
# data = amap_coordinate(sample)
# data = amap_decode(data=sample,
#                    radius=300)  # 以GPS坐标周围300米为检索范围
#
# map_type = 'Gaode'
# point_data = data.copy()
#
# map_plot = plot_map(map_type, point_data)
#
# map_plot.save("map_plot.html")
# webbrowser.open("map_plot.html")

# 利用 folium 进行地图可视化
# del data_import
# 纬度 29.999376666666667 ；经度 121.6603   121.6603,29.999376666666667
# 逆地理编码web API
# https://restapi.amap.com/v3/geocode/regeo?key=1d7a5c90ef3d9cd09995aec793404657&location=121.6603,29.999376666666667&poitype=道路&radius=100&extensions=all&batch=false&roadlevel=0
# a = 'https://restapi.amap.com/v3/assistant/coordinate/convert?locations=122.2887,30.09745&coordsys=gps&output=json&key=1d7a5c90ef3d9cd09995aec793404657'
#
# b = requests.get(a).json()
# m = folium.Map(
#     location=[38.96, 117.78],
#     zoom_start=12,
#     # tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}', # 高德街道图
#     tiles='http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}',  # 高德卫星图
#     # tiles='https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', # google 卫星图
#     # tiles='https://mt.google.com/vt/lyrs=h&x={x}&y={y}&z={z}', # google 地图
#     attr='default'
# )
# m.save("1.html")
# webbrowser.open("1.html")

# ----------------------------------------------
data = [
    ["海门", 9],
    ["鄂尔多斯", 12],
    ["招远", 12],
    ["舟山", 12],
    ["齐齐哈尔", 14],
    ["盐城", 15],
    ["赤峰", 16],
    ["青岛", 18],
    ["乳山", 18],
    ["金昌", 19],
    ["泉州", 21],
    ["莱西", 21],
    ["日照", 21],
    ["胶南", 22],
    ["南通", 23],
    ["拉萨", 24],
    ["云浮", 24],
    ["梅州", 25],
    ["文登", 25],
    ["上海", 25],
    ["攀枝花", 25],
    ["威海", 25],
    ["承德", 25],
    ["厦门", 26],
    ["汕尾", 26],
    ["潮州", 26],
    ["丹东", 27],
    ["太仓", 27],
    ["曲靖", 27],
    ["烟台", 28],
    ["福州", 29],
    ["瓦房店", 30],
    ["即墨", 30],
    ["抚顺", 31],
    ["玉溪", 31],
    ["张家口", 31],
    ["阳泉", 31],
    ["莱州", 32],
    ["湖州", 32],
    ["汕头", 32],
    ["昆山", 33],
    ["宁波", 33],
    ["湛江", 33],
    ["揭阳", 34],
    ["荣成", 34],
    ["连云港", 35],
    ["葫芦岛", 35],
    ["常熟", 36],
    ["东莞", 36],
    ["河源", 36],
    ["淮安", 36],
    ["泰州", 36],
    ["南宁", 37],
    ["营口", 37],
    ["惠州", 37],
    ["江阴", 37],
    ["蓬莱", 37],
    ["韶关", 38],
    ["嘉峪关", 38],
    ["广州", 38],
    ["延安", 38],
    ["太原", 39],
    ["清远", 39],
    ["中山", 39],
    ["昆明", 39],
    ["寿光", 40],
    ["盘锦", 40],
    ["长治", 41],
    ["深圳", 41],
    ["珠海", 42],
    ["宿迁", 43],
    ["咸阳", 43],
    ["铜川", 44],
    ["平度", 44],
    ["佛山", 44],
    ["海口", 44],
    ["江门", 45],
    ["章丘", 45],
    ["肇庆", 46],
    ["大连", 47],
    ["临汾", 47],
    ["吴江", 47],
    ["石嘴山", 49],
    ["沈阳", 50],
    ["苏州", 50],
    ["茂名", 50],
    ["嘉兴", 51],
    ["长春", 51],
    ["胶州", 52],
    ["银川", 52],
    ["张家港", 52],
    ["三门峡", 53],
    ["锦州", 54],
    ["南昌", 54],
    ["柳州", 54],
    ["三亚", 54],
    ["自贡", 56],
    ["吉林", 56],
    ["阳江", 57],
    ["泸州", 57],
    ["西宁", 57],
    ["宜宾", 58],
    ["呼和浩特", 58],
    ["成都", 58],
    ["大同", 58],
    ["镇江", 59],
    ["桂林", 59],
    ["张家界", 59],
    ["宜兴", 59],
    ["北海", 60],
    ["西安", 61],
    ["金坛", 62],
    ["东营", 62],
    ["牡丹江", 63],
    ["遵义", 63],
    ["绍兴", 63],
    ["扬州", 64],
    ["常州", 64],
    ["潍坊", 65],
    ["重庆", 66],
    ["台州", 67],
    ["南京", 67],
    ["滨州", 70],
    ["贵阳", 71],
    ["无锡", 71],
    ["本溪", 71],
    ["克拉玛依", 72],
    ["渭南", 72],
    ["马鞍山", 72],
    ["宝鸡", 72],
    ["焦作", 75],
    ["句容", 75],
    ["北京", 79],
    ["徐州", 79],
    ["衡水", 80],
    ["包头", 80],
    ["绵阳", 80],
    ["乌鲁木齐", 84],
    ["枣庄", 84],
    ["杭州", 84],
    ["淄博", 85],
    ["鞍山", 86],
    ["溧阳", 86],
    ["库尔勒", 86],
    ["安阳", 90],
    ["开封", 90],
    ["济南", 92],
    ["德阳", 93],
    ["温州", 95],
    ["九江", 96],
    ["邯郸", 98],
    ["临安", 99],
    ["兰州", 99],
    ["沧州", 100],
    ["临沂", 103],
    ["南充", 104],
    ["天津", 105],
    ["富阳", 106],
    ["泰安", 112],
    ["诸暨", 112],
    ["郑州", 113],
    ["哈尔滨", 114],
    ["聊城", 116],
    ["芜湖", 117],
    ["唐山", 119],
    ["平顶山", 119],
    ["邢台", 119],
    ["德州", 120],
    ["济宁", 120],
    ["荆州", 127],
    ["宜昌", 130],
    ["义乌", 132],
    ["丽水", 133],
    ["洛阳", 134],
    ["秦皇岛", 136],
    ["株洲", 143],
    ["石家庄", 147],
    ["莱芜", 148],
    ["常德", 152],
    ["保定", 153],
    ["湘潭", 154],
    ["金华", 157],
    ["岳阳", 169],
    ["长沙", 175],
    ["衢州", 177],
    ["廊坊", 193],
    ["菏泽", 194],
    ["合肥", 229],
    ["武汉", 273],
    ["大庆", 279],
]

geoCoordMap = {
    "海门": [121.15, 31.89],
    "鄂尔多斯": [109.781327, 39.608266],
    "招远": [120.38, 37.35],
    "舟山": [122.207216, 29.985295],
    "齐齐哈尔": [123.97, 47.33],
    "盐城": [120.13, 33.38],
    "赤峰": [118.87, 42.28],
    "青岛": [120.33, 36.07],
    "乳山": [121.52, 36.89],
    "金昌": [102.188043, 38.520089],
    "泉州": [118.58, 24.93],
    "莱西": [120.53, 36.86],
    "日照": [119.46, 35.42],
    "胶南": [119.97, 35.88],
    "南通": [121.05, 32.08],
    "拉萨": [91.11, 29.97],
    "云浮": [112.02, 22.93],
    "梅州": [116.1, 24.55],
    "文登": [122.05, 37.2],
    "上海": [121.48, 31.22],
    "攀枝花": [101.718637, 26.582347],
    "威海": [122.1, 37.5],
    "承德": [117.93, 40.97],
    "厦门": [118.1, 24.46],
    "汕尾": [115.375279, 22.786211],
    "潮州": [116.63, 23.68],
    "丹东": [124.37, 40.13],
    "太仓": [121.1, 31.45],
    "曲靖": [103.79, 25.51],
    "烟台": [121.39, 37.52],
    "福州": [119.3, 26.08],
    "瓦房店": [121.979603, 39.627114],
    "即墨": [120.45, 36.38],
    "抚顺": [123.97, 41.97],
    "玉溪": [102.52, 24.35],
    "张家口": [114.87, 40.82],
    "阳泉": [113.57, 37.85],
    "莱州": [119.942327, 37.177017],
    "湖州": [120.1, 30.86],
    "汕头": [116.69, 23.39],
    "昆山": [120.95, 31.39],
    "宁波": [121.56, 29.86],
    "湛江": [110.359377, 21.270708],
    "揭阳": [116.35, 23.55],
    "荣成": [122.41, 37.16],
    "连云港": [119.16, 34.59],
    "葫芦岛": [120.836932, 40.711052],
    "常熟": [120.74, 31.64],
    "东莞": [113.75, 23.04],
    "河源": [114.68, 23.73],
    "淮安": [119.15, 33.5],
    "泰州": [119.9, 32.49],
    "南宁": [108.33, 22.84],
    "营口": [122.18, 40.65],
    "惠州": [114.4, 23.09],
    "江阴": [120.26, 31.91],
    "蓬莱": [120.75, 37.8],
    "韶关": [113.62, 24.84],
    "嘉峪关": [98.289152, 39.77313],
    "广州": [113.23, 23.16],
    "延安": [109.47, 36.6],
    "太原": [112.53, 37.87],
    "清远": [113.01, 23.7],
    "中山": [113.38, 22.52],
    "昆明": [102.73, 25.04],
    "寿光": [118.73, 36.86],
    "盘锦": [122.070714, 41.119997],
    "长治": [113.08, 36.18],
    "深圳": [114.07, 22.62],
    "珠海": [113.52, 22.3],
    "宿迁": [118.3, 33.96],
    "咸阳": [108.72, 34.36],
    "铜川": [109.11, 35.09],
    "平度": [119.97, 36.77],
    "佛山": [113.11, 23.05],
    "海口": [110.35, 20.02],
    "江门": [113.06, 22.61],
    "章丘": [117.53, 36.72],
    "肇庆": [112.44, 23.05],
    "大连": [121.62, 38.92],
    "临汾": [111.5, 36.08],
    "吴江": [120.63, 31.16],
    "石嘴山": [106.39, 39.04],
    "沈阳": [123.38, 41.8],
    "苏州": [120.62, 31.32],
    "茂名": [110.88, 21.68],
    "嘉兴": [120.76, 30.77],
    "长春": [125.35, 43.88],
    "胶州": [120.03336, 36.264622],
    "银川": [106.27, 38.47],
    "张家港": [120.555821, 31.875428],
    "三门峡": [111.19, 34.76],
    "锦州": [121.15, 41.13],
    "南昌": [115.89, 28.68],
    "柳州": [109.4, 24.33],
    "三亚": [109.511909, 18.252847],
    "自贡": [104.778442, 29.33903],
    "吉林": [126.57, 43.87],
    "阳江": [111.95, 21.85],
    "泸州": [105.39, 28.91],
    "西宁": [101.74, 36.56],
    "宜宾": [104.56, 29.77],
    "呼和浩特": [111.65, 40.82],
    "成都": [104.06, 30.67],
    "大同": [113.3, 40.12],
    "镇江": [119.44, 32.2],
    "桂林": [110.28, 25.29],
    "张家界": [110.479191, 29.117096],
    "宜兴": [119.82, 31.36],
    "北海": [109.12, 21.49],
    "西安": [108.95, 34.27],
    "金坛": [119.56, 31.74],
    "东营": [118.49, 37.46],
    "牡丹江": [129.58, 44.6],
    "遵义": [106.9, 27.7],
    "绍兴": [120.58, 30.01],
    "扬州": [119.42, 32.39],
    "常州": [119.95, 31.79],
    "潍坊": [119.1, 36.62],
    "重庆": [106.54, 29.59],
    "台州": [121.420757, 28.656386],
    "南京": [118.78, 32.04],
    "滨州": [118.03, 37.36],
    "贵阳": [106.71, 26.57],
    "无锡": [120.29, 31.59],
    "本溪": [123.73, 41.3],
    "克拉玛依": [84.77, 45.59],
    "渭南": [109.5, 34.52],
    "马鞍山": [118.48, 31.56],
    "宝鸡": [107.15, 34.38],
    "焦作": [113.21, 35.24],
    "句容": [119.16, 31.95],
    "北京": [116.46, 39.92],
    "徐州": [117.2, 34.26],
    "衡水": [115.72, 37.72],
    "包头": [110, 40.58],
    "绵阳": [104.73, 31.48],
    "乌鲁木齐": [87.68, 43.77],
    "枣庄": [117.57, 34.86],
    "杭州": [120.19, 30.26],
    "淄博": [118.05, 36.78],
    "鞍山": [122.85, 41.12],
    "溧阳": [119.48, 31.43],
    "库尔勒": [86.06, 41.68],
    "安阳": [114.35, 36.1],
    "开封": [114.35, 34.79],
    "济南": [117, 36.65],
    "德阳": [104.37, 31.13],
    "温州": [120.65, 28.01],
    "九江": [115.97, 29.71],
    "邯郸": [114.47, 36.6],
    "临安": [119.72, 30.23],
    "兰州": [103.73, 36.03],
    "沧州": [116.83, 38.33],
    "临沂": [118.35, 35.05],
    "南充": [106.110698, 30.837793],
    "天津": [117.2, 39.13],
    "富阳": [119.95, 30.07],
    "泰安": [117.13, 36.18],
    "诸暨": [120.23, 29.71],
    "郑州": [113.65, 34.76],
    "哈尔滨": [126.63, 45.75],
    "聊城": [115.97, 36.45],
    "芜湖": [118.38, 31.33],
    "唐山": [118.02, 39.63],
    "平顶山": [113.29, 33.75],
    "邢台": [114.48, 37.05],
    "德州": [116.29, 37.45],
    "济宁": [116.59, 35.38],
    "荆州": [112.239741, 30.335165],
    "宜昌": [111.3, 30.7],
    "义乌": [120.06, 29.32],
    "丽水": [119.92, 28.45],
    "洛阳": [112.44, 34.7],
    "秦皇岛": [119.57, 39.95],
    "株洲": [113.16, 27.83],
    "石家庄": [114.48, 38.03],
    "莱芜": [117.67, 36.19],
    "常德": [111.69, 29.05],
    "保定": [115.48, 38.85],
    "湘潭": [112.91, 27.87],
    "金华": [119.64, 29.12],
    "岳阳": [113.09, 29.37],
    "长沙": [113, 28.21],
    "衢州": [118.88, 28.97],
    "廊坊": [116.7, 39.53],
    "菏泽": [115.480656, 35.23375],
    "合肥": [117.27, 31.86],
    "武汉": [114.31, 30.52],
    "大庆": [125.03, 46.58],
}



res = []
for i in range(len(data)):
    geo_coord = geoCoordMap[data[i][0]]
    geo_coord.append(data[i][1])
    res.append([data[i][0], geo_coord])
