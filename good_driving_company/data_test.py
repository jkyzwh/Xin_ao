# -*- coding: utf-8 -*-

"""
Created on Tue 2020/09/25
本程序用于新奥公司提供的车在数据终端的数据集的测试，理解数据结构，解析数据含义，转化为方便处理的格式

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
# import json
# from urllib.parse import urlencode

import folium
import webbrowser
import statsmodels.api as sm

import pretty_errors
pretty_errors.activate()

# --------------------------------定义全局变量 高德开发者key与数字签名 ------------------------

global KEY, EARTH_REDIUS
KEY = '1d7a5c90ef3d9cd09995aec793404657'
EARTH_REDIUS = 6378.137  # 地球半径
# KEY = '771f529bb4d20b88fc847b8f1954b737'  # 吴楠提供的key
# SIG = 'b24f7386fd53fefd198f623dadb08598'
requests.DEFAULT_RETRIES = 5


# --------------------------------------------操作高德地图--------------------------


class AMap(object):
    """
    高德地图sdk，编写时间2020-08-20
    """

    def __init__(self, keys, sig=None, output="JSON"):
        """
        初始化，需要密钥
        :param keys: 密钥
        :param sig：数字签名,详见：https://lbs.amap.com/faq/quota-key/key/41169
        :param output: 输出，JSON or XML；设置 JSON 返回结果数据将会以JSON结构构成；如果设置 XML 返回结果数据将以 XML 结构构成。
        """
        self.keys = keys
        self.sig = sig
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

    def coordinate(self, locations: str):
        """
        key,请求服务权限标识,用户在高德地图官网申请Web服务API类型KEY
        locations, 坐标点,经度和纬度用","分割，经度在前，纬度在后，经纬度小数点后不得超过6位。多个坐标对之间用”|”进行分隔最多支持40对坐标。
        coordsys,原坐标系,可选值：gps mapbar baidu;
        output,返回数据格式类型,可选值：JSON,XML
        """

        data = False
        url = 'https://restapi.amap.com/v3/assistant/coordinate/convert?parameters'
        params = {
            'key': self.keys,
            'locations': locations,
            'coordsys': 'gps',
            'output': self.output,
        }

        # data = self.get_data(url, params)

        while data == False:  # 如果调用失败，返回False，则循环执行
            data = self.get_data(url, params)

        # url = url + urlencode(params)
        # data = requests.get(url).json()
        return data

    def location_encode(self, address, city=None, is_batch='false', callback=None):
        """
        地理位置转经纬度,官方文档参考：https://lbs.amap.com/api/webservice/guide/api/georegeo
        :param address: 国家、省份、城市、区县、城镇、乡村、街道、门牌号码、屋邨、大厦，如：北京市朝阳区阜通东大街6号。
                        如果需要解析多个地址的话，请用"|"进行间隔，并且将 batch 参数设置为 true，最多支持 10 个地址
                        进进行"|"分割形式的请求。
        :param city: 城市，Str类型，可以为中文也可以是拼音
        :param is_batch: 是否批量查询, Str类型，'true' or 'false'
        :param callback: 回调函数，值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效。
        :return status 返回结果状态值返回值为 0 或 1，0 表示请求失败；1 表示请求成功。
                count 返回结果数目
                info  返回状态说明，当 status 为 0 时，info 会返回具体错误原因，否则返回“OK”
                geocodes 地理编码信息列表，结果对象列表，包括下述字段：
                [
                    {
                        adcode：区域编码。例如：110101
                        building:建筑，Str类型，其为字典的Key，下面为其所对应的Value值
                        {
                            name: 建筑名称，List类型
                            type: 建筑类别，List类型
                         }
                        city：地址所在的城市名, Str类型。例如：北京市
                        citycode：城市编码，Str类型。例如:010
                        country: 国家，Str类型。国内地址默认返回中国
                        district：地址所在的区, Str类型。例如：朝阳区
                        formatted_address：结构化地址信息，Str类型。例如:省份＋城市＋区县＋城镇＋乡村＋街道＋门牌号码
                        level：匹配级别，Str类型
                        location：坐标点，Str类型。经度，纬度
                        neighborhood：社区信息，Dict类型
                        {
                            name: 社区名称，List类型。例如：['北京大学']
                            type：社区类型，List类型。例如：['科教文化服务','学校', '高等院校']
                        }
                        number：门牌，List类型。例如：例如：['6号']。
                        province：地址所在的省份名, Str类型。例如：'北京市'。此处需要注意的是，中国的四大直辖市也算作省级单位
                        street：街道，List类型。例如：['阜通东大街']
                        township：坐标点所在乡镇/街道（此街道为社区街道，不是道路信息），List类型。例如：['燕园街道']。
                    },
                    {...}
                ]
        """
        url = "https://restapi.amap.com/v3/geocode/geo?parameters"
        params = {
            'key': self.keys,
            'address': address,
            'city': city,
            'is_batch': is_batch,
            'output': self.output,
            'callback': callback
        }
        data = self.get_data(url, params)
        return data

    def location_decode(self, location, poi_type=None, radius=1000, extensions="base", is_batch='false', road_level=None
                        , callback=None, home_or_corp=0):
        """
        该方法用于经纬度坐标转地理位置，官方文档参考：https://lbs.amap.com/api/webservice/guide/api/georegeo
        :param location: 经纬度坐标, Str类型。
                        传入内容规则：经度在前，纬度在后，经纬度间以“,”分割，经纬度小数点后不要超过 6 位。
                        如果需要解析多个经纬度的话，请用"|"进行间隔，并且将 batch 参数设置为 true，最多支持传入 20 对坐标点。
                        每对点坐标之间用"|"分割。
        :param poi_type: 以下内容需要 extensions 参数为 all 时才生效。
                        逆地理编码在进行坐标解析之后不仅可以返回地址描述，
                        也可以返回经纬度附近符合限定要求的POI内容（在 extensions 字段值为 all 时才会返回POI内容）。
                        设置 POI 类型参数相当于为上述操作限定要求。参数仅支持传入POI TYPECODE，可以传入多个POI TYPECODE，
                        相互之间用“|”分隔。该参数在 batch 取值为 true 时不生效。获取 POI TYPECODE 可以参考POI分类码表
        :param radius: 搜索半径， Int类型。radius取值范围在0~3000，默认是1000。单位：米
        :param extensions: Str类型，参数默认取值是 base，也就是返回基本地址信息；参数取值为 all 时会返回基本地址信息、附近 POI 内容、道路信息
                            以及道路交叉口信息。
        :param is_batch: 是否批量查询, Str类型，'true' or 'false'
        :param road_level: 以下内容需要 extensions 参数为 all 时才生效。可选值：0，1。
                            当road_level=0时，显示所有道路
                            当road_level=1时，过滤非主干道路，仅输出主干道路数据
        :param callback: callback值是用户定义的函数名称，此参数只在 output 参数设置为 JSON 时有效
        :param home_or_corp: 是否优化POI返回顺序
                            以下内容需要 extensions 参数为 all 时才生效。
                            home_or_corp 参数的设置可以影响召回 POI 内容的排序策略，目前提供三个可选参数：
                            0：不对召回的排序策略进行干扰。
                            1：综合大数据分析将居家相关的 POI 内容优先返回，即优化返回结果中 pois 字段的poi顺序。
                            2：综合大数据分析将公司相关的 POI 内容优先返回，即优化返回结果中 pois 字段的poi顺序。
        :return: status 返回结果状态值，Str类型。返回值为 0 或 1，0 表示请求失败；1 表示请求成功。
                 info 返回状态说明，Str类型。当 status 为 0 时，info 会返回具体错误原因，否则返回“OK”。
                      详情可以参考info状态表https://lbs.amap.com/api/webservice/guide/tools/info
                 regeocodes 逆地理编码,数据类型Dict或者List。
                            is_batch 字段设置为'true'时为批量请求，此时 regeocodes 标签返回，标签下为 regeocode对象列表；
                            is_batch 为'false'时为单个请求，会返回 regeocode 对象字典；
                            regeocode 对象包含的数据如下：
                 [/{
                    addressComponent: 地址元素字典
                    {
                        adcode: 行政区编码, Str类型。例如：110108。
                        building：楼信息，Dict类型
                        {
                            name: 建筑名称，List类型。例如：例如：['万达广场']
                            type: 建筑类型，List类型。例如：['科教文化服务', '学校', '高等院校']
                        }
                        businessAreas: 经纬度所属商圈，List类型
                        [
                            {
                            id: 商圈所在区域的adcode, Str类型。 例如: '440106'
                            location: 商圈中心点经纬度，Str类型。例如: '113.333776,23.119825'
                            name: 商圈名称, Str类型。例如：'珠江新城'
                            }，
                            {
                            ...
                            }
                        ]
                        city: 坐标点所在城市名称, Str类型。
                              请注意：当城市是省直辖县时返回为空，以及城市为北京、上海、天津、重庆四个直辖市时，该字段返回为空；
                              省直辖县列表，https://lbs.amap.com/faq/webservice/webservice-api/geocoding/43267
                        citycode: 城市编码，Str类型。例如：'010'
                        country: 国家，Str类型。国内地址默认返回中国
                        district：坐标点所在区，Str类型。例如：'海淀区'
                        neighborhood：社区信息，Dict类型
                        {
                            name: 社区名称，List类型。例如：['北京大学']
                            type：社区类型，List类型。例如：['科教文化服务','学校', '高等院校']
                        }
                        province: 坐标点所在省名称, Str类型。例如：北京市
                        streetNumber: 门牌信息, Dict类型
                        {
                            street: 街道名称。例如：中关村北二条
                            number: 门牌号。例如：3号
                            location: 坐标点。经纬度坐标点：经度，纬度
                            direction: 方向。坐标点所处街道方位。
                            distance: 门牌地址到请求坐标的距离。单位：米
                        }
                        towncode：乡镇街道编码，Str类型。例如：110101001000。
                        township：坐标点所在乡镇/街道（此街道为社区街道，不是道路信息），Str类型。例如：燕园街道。
                        seaArea: 所属海域信息。例如：渤海
                    }
                    formatted_address：结构化地址信息，Str类型。
                                      结构化地址信息包括：省份＋城市＋区县＋城镇＋乡村＋街道＋门牌号码。
                                      如果坐标点处于海域范围内，则结构化地址信息为：省份＋城市＋区县＋海域信息
                    roads: 道路信息列表。请求参数 extensions 为 all 时返回如下内容
                    [
                        road: 道路信息
                        [
                            id: 道路id
                            name: 道路名称
                            distance: 道路到请求坐标的距离。单位：米
                            direction: 方位。输入点和此路的相对方位
                            location: 坐标点
                        ]
                    ]
                    roadinters: 道路交叉口列表。请求参数 extensions 为 all 时返回如下内容。
                    [
                        roadinter: 道路交叉口
                        [
                            distance: 交叉路口到请求坐标的距离。	单位：米
                            direction: 方位。输入点相对路口的方位。
                            location: 路口经纬度
                            first_id: 第一条道路id
                            first_name: 第一条道路名称
                            second_id: 第二条道路id
                            second_name：第二条道路名称
                        ]
                    ]
                    pois: poi信息列表。请求参数 extensions 为 all 时返回如下内容
                    [
                        poi: poi信息列表
                        [
                            id: poi的id
                            name: poi点名称
                            type：poi类型
                            tel: 电话
                            distance: 该POI的中心点到请求坐标的距离。单位：米
                            direction: 方向。为输入点相对建筑物的方位
                            address: poi地址信息
                            location: 坐标点
                            businessarea: poi所在商圈名称
                        ]
                    ]
                    aois: aoi信息列表。请求参数 extensions 为 all 时返回如下内容
                    [
                        aoi: aoi信息
                        [
                            id: 所属 aoi的id
                            name: 所属 aoi 名称
                            adcode: 所属 aoi 所在区域编码
                            location: 所属 aoi 中心点坐标
                            area: 所属aoi点面积。单位：平方米
                            distance: 输入经纬度是否在aoi面之中。 0，代表在aoi内。其余整数代表距离AOI的距离
                        ]
                    ]
                 }/]
        """
        url = "https://restapi.amap.com/v3/geocode/regeo?parameters"
        params = {
            'key': self.keys,
            'location': location,
            'poi_type'.replace('_', ''): poi_type,
            'radius': radius,
            'extensions': extensions,
            'batch': is_batch,
            'road_level'.replace('_', ''): road_level,
            'sig': self.sig,
            'output': self.output,
            'callback': callback,
            'home_or_corp'.replace('_', ''): home_or_corp
        }
        data = self.get_data(url, params)
        return data


# ---------------------------------------操作GPS信息------------------------------
class Gps(object):
    """
    高德地图sdk，编写时间2020-08-20
    """

    def __init__(self, earth_radius):
        """
        初始化，需要密钥
        :param keys: 密钥
        :param sig：数字签名,详见：https://lbs.amap.com/faq/quota-key/key/41169
        :param output: 输出，JSON or XML；设置 JSON 返回结果数据将会以JSON结构构成；如果设置 XML 返回结果数据将以 XML 结构构成。
        """
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


# 利用高德 web API 转换GPS坐标为高德坐标
def amap_coordinate(data):
    amap = AMap(keys=KEY, output="JSON")
    # 对每一行进行遍历，生成gps坐标字符串
    data['long_GaoDe'] = 0.
    data['lat_GaoDe'] = 0.

    for i in range(len(data)):

        lat = data['lat_GPS'].iloc[i]
        long = data['long_GPS'].iloc[i]
        lat = round(lat, 5)
        long = round(long, 5)
        location_GPS = str(long) + ',' + str(lat)
        print(location_GPS)

        loc_gaode = amap.coordinate(locations=location_GPS)
        print(loc_gaode)

        if loc_gaode == False:
            long_GaoDe = 'Amap访问问题'
            lat_Gaode = 'Amap访问问题'
        else:
            GaoDe = loc_gaode['locations']
            long_GaoDe = float(str.split(GaoDe, ',')[0])
            lat_Gaode = float(str.split(GaoDe, ',')[1])

        data['long_GaoDe'].values[i] = long_GaoDe
        data['lat_GaoDe'].values[i] = lat_Gaode

    return data


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


# 利用高德 web API 逆编码经纬度数据，提取道路名称信息以及修正位置GPS坐标
def amap_decode(data, radius):
    sample = data.copy()
    sample['address'] = ''
    sample['province'] = ''
    sample['city'] = ''
    sample['road_name'] = ''
    sample['amap_long'] = 0.
    sample['amap_lat'] = 0.

    # 利用高德 web API通过经纬度坐标 逆编码获取道路信息
    amap = AMap(keys=KEY, output="JSON")
    for i in range(len(sample)):

        lat = sample['lat_GaoDe'].iloc[i]
        long = sample['long_GaoDe'].iloc[i]
        lat = round(lat, 5)
        long = round(long, 5)

        location = str(long) + ',' + str(lat)
        decode = amap.location_decode(location=location,
                                      poi_type='路',
                                      radius=radius,
                                      extensions="all",
                                      road_level=0)

        if decode == False:
            address = 'Amap访问问题'
            province = 'Amap访问问题'
            city = 'Amap访问问题'
            road_name = 'Amap访问问题'
            amap_location = 'Amap访问问题'
            intersection = 'Amap访问问题'
            amap_long = long
            amap_lat = lat

        else:
            address = decode['regeocode']['formatted_address']
            city = decode['regeocode']['addressComponent']['city']
            province = decode['regeocode']['addressComponent']['province']

            # 判断是否是交叉口
            if len(decode['regeocode']['roads']) > 1:
                road_name = decode['regeocode']['roads'][0]['name']
                amap_location = decode['regeocode']['roads'][0]['location']
                amap_long = float(str.split(amap_location, ',')[0])
                amap_lat = float(str.split(amap_location, ',')[1])
                intersection = 'yes'
            elif len(decode['regeocode']['roads']) == 1:
                road_name = decode['regeocode']['roads'][0]['name']
                amap_location = decode['regeocode']['roads'][0]['location']
                amap_long = float(str.split(amap_location, ',')[0])
                amap_lat = float(str.split(amap_location, ',')[1])
                intersection = 'no'
            else:
                road_name = '没找到临近道路'
                intersection = 'no'
                amap_location = ''
                amap_long = 0
                amap_lat = 0

        sample['address'].values[i] = address
        sample['province'].values[i] = province
        sample['city'].values[i] = city
        sample['road_name'].values[i] = road_name
        sample['amap_long'].values[i] = amap_long
        sample['amap_lat'].values[i] = amap_lat

        print(i, address, province, city, road_name, amap_location, intersection)
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


# ---------------------- 主程序 ----------------------

# 读取配置文件，获得数据文件路径
DATA_PATH, MAP_SAVE_PATH, DATA_SAVE_PATH = get_config()

# 获得所有数据文件的路径列表
data_files = get_data_file_list(DATA_PATH)

# 读取数据文件，利用高德API补全信息
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

# 补全高德坐标
abnormal = amap_coordinate(abnormal)
abnormal = amap_decode(data=abnormal,
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
