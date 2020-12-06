# -*- coding: utf-8 -*-

"""
Created on Tue 2020/10/12
本程序用于新奥公司提供的数据集的测试
对路线进行不同风险不同颜色的绘制

@author: Zhwh-notbook
"""
import pandas as pd
import numpy as np
import os
import platform

import requests
import datetime
import random

import math
from sklearn.cluster import DBSCAN
from sklearn import metrics

from pyecharts.charts import BMap
from pyecharts import options as opts
from pyecharts.globals import GeoType
import webbrowser

import pretty_errors

pretty_errors.activate()

# --------------------------------定义全局变量 百度开发者key与数字签名 ------------------------

global KEY, EARTH_REDIUS
KEY = 'iHDcbVaHkRo6xz149QBiqlrn2FAbwX6b'
EARTH_REDIUS = 6378.137  # 地球半径
requests.DEFAULT_RETRIES = 5


# ---------------------------------------操作GPS信息-------------------------------------------
class Gps(object):

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


# ---------------------------------------------------------------------------------------------


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


# 调用百度地图绘制点图，不同类型风险行为采用颜色不同的标记
def plot_scatter_map(route_data, path):
    route_data = route_data[route_data['speed'] > 10.0]
    data = route_data[['lat_BaiDu', 'long_BaiDu', 'behavior', 'label']].copy()
    data.columns = ['lat', 'lon', 'behavior', 'label']

    # 地图中心
    map_center = [data['lon'].mean(), data['lat'].mean()]
    # 初始化百度地图
    bd_map = BMap(init_opts=opts.InitOpts(width="1920px", height="1080px"))
    bd_map.add_schema(baidu_ak=KEY,
                      center=map_center,
                      zoom=8,
                      is_roam=True,
                      map_style=None,
                      )

    color = ['red', 'green', 'blue', 'yellow', 'gold', 'cyan', 'magenta', 'purple']

    # 将数据分为异常路段和正常路段
    normal_route = data[data['label'] <= -0.0].copy()
    risk_route = data[data['label'] > 0.0].copy()

    # 绘制正常路段散点图，颜色为绿色
    normal_map_data = []
    # 利用BMap.add_coordinate 将坐标值赋值给一个地点名称，并增加近BMap对象地理信息中
    for i in range(len(normal_route)):
        name = 'low_risk' + str(i)
        longitude = normal_route['lon'].iloc[i]
        latitude = normal_route['lat'].iloc[i]

        bd_map.add_coordinate(name=name,
                              longitude=longitude,
                              latitude=latitude
                              )
        normal_map_data.append((name, -1))

    # 绘制高风险路段散点图，颜色为红色
    risk_map_data = []
    # 利用BMap.add_coordinate 将坐标值赋值给一个地点名称，并增加近BMap对象地理信息中
    for j in range(len(risk_route)):
        name = 'high_risk' + str(j)
        longitude = risk_route['lon'].iloc[j]
        latitude = risk_route['lat'].iloc[j]

        bd_map.add_coordinate(name=name,
                              longitude=longitude,
                              latitude=latitude
                              )
        risk_map_data.append((name, -1))

    # 将低风险轨迹散点标识在百度地图上
    bd_map = bd_map.add(
        series_name='低风险路段',
        type_="scatter",
        data_pair=normal_map_data,
        symbol_size=10,
        effect_opts=opts.EffectOpts(),
        label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color='green'),
    )

    # 将高风险轨迹散点标识在百度地图上
    bd_map = bd_map.add(
        series_name='高风险路段',
        type_="scatter",
        data_pair=risk_map_data,
        symbol_size=20,
        effect_opts=opts.EffectOpts(),
        label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color='red'),
    )

    # 将绘图结果输出至网页文件
    bd_map = bd_map.add_control_panel(maptype_control_opts=opts.BMapTypeControlOpts(position=1),
                                      )
    # 设置图例
    bd_map = bd_map.set_global_opts(legend_opts=opts.LegendOpts(is_show=True,
                                                                item_height=50,
                                                                ),
                                    title_opts=opts.TitleOpts(title="新奥危险货物运输高风险路段聚类分析图"),
                                    )
    # 将地图加载到网页
    bd_map = bd_map.render(path)

    # 用浏览器打开文件
    webbrowser.open(path)
    return bd_map


# 计算相邻数据之间的时间间隔
def driving_time(data):
    for i in range(len(data)):

        if i == 0:
            data['driving_time'].values[i] = 0.0
        else:
            time1 = data['time'].iloc[i - 1]
            time2 = data['time'].iloc[i]

            time1 = datetime.datetime.strptime(str(time1), "%Y-%m-%d %H:%M:%S")
            time2 = datetime.datetime.strptime(str(time2), "%Y-%m-%d %H:%M:%S")

            trip_time = (time2 - time1).seconds

            data['driving_time'].values[i] = trip_time
    return data


# 将一段轨迹数据转化为百度地图需要的格式
def route_to_baidu_line(data, color='green'):
    data = data[['lat_BaiDu', 'long_BaiDu']].copy()
    data.columns = ['lat', 'lon']
    # 字典中的coords字段，是有个【经度，纬度】的列表
    coords = []
    for i in range(len(data)):
        longitude = data['lon'].iloc[i]
        latitude = data['lat'].iloc[i]
        coords_point = [longitude, latitude]
        coords.append(coords_point)

    # 字典中的lineStyle字段，dict格式
    if color == 'red':
        lineStyle = {'normal': {'color': 'rgba(255,0,255,1)'}}
    else:
        lineStyle = {'normal': {'color': 'rgba(0,100,0,1)'}}

    baidu_line_data = {'coords': coords, 'lineStyle': lineStyle}

    return baidu_line_data


# 将轨迹数据转化为百度地图lines格式数据——使用时间作为切割依据
def route_data_cut(route_data, color='green'):
    route_data = route_data[route_data['speed'] > 0]
    # 将数据按驾驶人信息分隔，按时间序列排序

    # 剔除重复的数据文件路径
    truck_list = route_data.drop_duplicates(['truck_license'])['truck_license'].copy()
    # 将数据根据时间间隔大于10分钟的规则进行分割，保存进list

    # 将每一段行程数据保存进一个列表
    trip_list = []

    for truck in truck_list:
        truck_temp = route_data[route_data['truck_license'] == truck]

        # 将行程数据按照时间序列排序
        truck_temp = truck_temp.sort_values(by='time')

        # 重新计算提出零速度后的相邻数据行之间的时间间隔
        truck_temp = driving_time(truck_temp)

        # 获取行程间隔数据的索引列表
        time_cut_index = truck_temp[truck_temp['driving_time'] > 600].index
        index_bp = truck_temp.index[0]
        index_ep = truck_temp.index[len(truck_temp) - 1]

        for i in range(len(time_cut_index)):
            if i == 0:
                trip_temp_data = truck_temp.loc[index_bp: time_cut_index[i]]
                trip_temp_data = trip_temp_data.drop(index=[time_cut_index[i]])
            else:
                trip_temp_data = truck_temp.loc[time_cut_index[i - 1]: time_cut_index[i]]
                trip_temp_data = trip_temp_data.drop(index=[time_cut_index[i]])
            trip_list.append(trip_temp_data)

        trip_temp_data = truck_temp.loc[time_cut_index[i]: index_ep]
        trip_temp_data = trip_temp_data.drop(index=[index_ep])
        trip_list.append(trip_temp_data)

    #  遍历行程列表，生成百度地图支持的数据文件列表
    trip_baidu_list = []
    for trip in trip_list:
        # route_to_baidu_line(trip, color=color)
        trip_baidu_list.append(route_to_baidu_line(trip, color=color))

    return trip_baidu_list


# 将轨迹数据转化为百度地图lines格式数据——使用距离作为切割依据
def route_cut(data, color='green'):
    # 剔除重复的数据文件路径
    truck_list = data.drop_duplicates(['truck_license'])['truck_license'].to_list()
    # 将数据根据时间间隔大于10分钟的规则进行分割，保存进list

    # 将每一段行程数据保存进一个列表
    trip_list = []

    for truck in truck_list:
        print(truck)
        truck_temp = data[data['truck_license'] == truck].copy()

        # 剔除车辆静止时的数据
        truck_temp = truck_temp[truck_temp['distance'] > 0].copy()

        # 将行程数据按照时间序列排序
        truck_temp = truck_temp.sort_values(by='time')

        # 通过相邻GPS坐标计算的行程距离
        truck_temp = gps_distance(earth_r=EARTH_REDIUS,
                                  data=truck_temp)

        # 以间距大于100米采样
        # truck_temp = truck_temp[truck_temp['distance_gps'] > 100].copy()
        truck_temp = gps_distance(earth_r=EARTH_REDIUS,
                                  data=truck_temp)

        # 重新计算提出零速度后的相邻数据行之间的时间间隔
        truck_temp = driving_time(truck_temp)

        a = truck_temp.sort_values(by='distance_gps').copy()

        # 获取行程间隔数据的索引列表，初定为间距2km以上时认为是分隔的路线
        time_cut_index = truck_temp[truck_temp['distance_gps'] > 2000].index
        index_bp = truck_temp.index[0]
        index_ep = truck_temp.index[len(truck_temp) - 1]

        if len(time_cut_index) > 1:

            for i in range(len(time_cut_index)):
                if i == 0:
                    trip_temp_data = truck_temp.loc[index_bp: time_cut_index[i]]
                    trip_temp_data = trip_temp_data.drop(index=[time_cut_index[i]])
                else:
                    trip_temp_data = truck_temp.loc[time_cut_index[i - 1]: time_cut_index[i]]
                    trip_temp_data = trip_temp_data.drop(index=[time_cut_index[i]])

                # 只有具备一定长度的路线才被绘制，初定为至少包括5个轨迹坐标点
                if len(trip_temp_data) > 5:
                    trip_list.append(trip_temp_data)

            if index_ep > time_cut_index[i]:
                trip_temp_data = truck_temp.loc[time_cut_index[i]: index_ep]
                trip_temp_data = trip_temp_data.drop(index=[index_ep])
            if len(trip_temp_data) > 5:
                trip_list.append(trip_temp_data)

    #  遍历行程列表，生成百度地图支持的数据文件列表
    trip_baidu_list = []
    for trip in trip_list:
        route_to_baidu_line(trip, color=color)
        trip_baidu_list.append(route_to_baidu_line(trip, color=color))

    return trip_baidu_list


# -------------------------------------------------------------------------
if __name__ == "__main__":
    # 读取配置文件，获得数据文件路径
    DATA_PATH, MAP_SAVE_PATH, DATA_SAVE_PATH = get_config()

    data_path = os.path.join(DATA_SAVE_PATH, "data_dbscan_result.csv")

    all_data = pd.read_csv(data_path,
                           header=0,
                           index_col=False,
                           # names=col_names,
                           low_memory=False
                           )

    # 将nan数据替换为-1
    all_data.fillna(value=-1, inplace=True)

    # 绘制异常点和正常点位分布散点图
    scatter_file_name = 'route_map_scatter.html'
    lines_file_name = 'route_map_lines.html'
    if not os.path.exists(MAP_SAVE_PATH):
        os.mkdir(MAP_SAVE_PATH)
    scatter_file_dir = os.path.join(MAP_SAVE_PATH, scatter_file_name)
    lines_file_dir = os.path.join(MAP_SAVE_PATH, lines_file_name)

    # map_plot = plot_scatter_map(route_data=all_data,
    #                             path=scatter_file_dir)

    # 绘制异常点和正常点分布路线图，首先将数据分为异常路段和正常路段
    # normal_route = all_data[all_data['label'] <= -0.0].copy()
    # risk_route = all_data[all_data['label'] > 0.0].copy()

    # 将行驶轨迹数据转化为百度地图支持的lines数据
    all_map_data = route_data_cut(route_data=all_data,
                                  color='green',
                                  )
    # risk_map_data = route_data_cut(route_data=risk_route,
    #                                color='red',
    #                                )

    # 地图中心
    map_center = [all_data['long_BaiDu'].mean(), all_data['lat_GPS'].mean()]

    # 初始化百度地图
    bd_map = BMap(init_opts=opts.InitOpts(width="1920px", height="1080px"))
    bd_map.add_schema(baidu_ak=KEY,
                      center=map_center,
                      zoom=8,
                      is_roam=True,
                      map_style=None,
                      )

    color = ['red', 'green', 'blue', 'yellow', 'gold', 'cyan', 'magenta', 'purple']

    # 将数据分为异常路段和正常路段
    normal_route = all_data[all_data['label'] <= -0.0].copy()
    risk_route = all_data[all_data['label'] > 0.0].copy()

    # # 绘制正常路段散点图，颜色为绿色
    # normal_map_data = []
    # # 利用BMap.add_coordinate 将坐标值赋值给一个地点名称，并增加近BMap对象地理信息中
    # for i in range(len(normal_route)):
    #     name = 'low_risk' + str(i)
    #     longitude = normal_route['lon'].iloc[i]
    #     latitude = normal_route['lat'].iloc[i]
    #
    #     bd_map.add_coordinate(name=name,
    #                           longitude=longitude,
    #                           latitude=latitude
    #                           )
    #     normal_map_data.append((name, -1))

    # 绘制高风险路段散点图，颜色为红色
    risk_map_data = []
    # 利用BMap.add_coordinate 将坐标值赋值给一个地点名称，并增加近BMap对象地理信息中
    for j in range(len(risk_route)):
        name = 'high_risk' + str(j)
        longitude = risk_route['long_BaiDu'].iloc[j]
        latitude = risk_route['lat_GPS'].iloc[j]

        bd_map.add_coordinate(name=name,
                              longitude=longitude,
                              latitude=latitude
                              )
        risk_map_data.append((name, -1))

    # bd_map = bd_map.add(
    #     series_name='低风险路段',
    #     type_="scatter",
    #     data_pair=normal_map_data,
    #     symbol_size=10,
    #     effect_opts=opts.EffectOpts(),
    #     label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
    #     itemstyle_opts=opts.ItemStyleOpts(color='green'),
    # )

    # 将高风险轨迹散点标识在百度地图上
    bd_map = bd_map.add(
        series_name='高风险路段',
        type_="scatter",
        data_pair=risk_map_data,
        symbol_size=20,
        effect_opts=opts.EffectOpts(),
        label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color='red'),
    )

    # 将低风险路线标识在百度地图上
    bd_map = bd_map.add(
        series_name='低风险路段',
        type_="lines",
        is_polyline=True,
        data_pair=all_map_data,
        linestyle_opts=opts.LineStyleOpts(opacity=0.8, width=5),
        effect_opts=opts.EffectOpts(),
        label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color='green'),
        # 如果不是最新版本的话可以注释下面的参数（效果差距不大）
        progressive=200,
        progressive_threshold=500,
    )

    # 将绘图结果输出至网页文件
    bd_map = bd_map.add_control_panel(maptype_control_opts=opts.BMapTypeControlOpts(position=1),
                                      )
    # 设置图例
    bd_map = bd_map.set_global_opts(legend_opts=opts.LegendOpts(is_show=True,
                                                                item_height=50,
                                                                ),
                                    title_opts=opts.TitleOpts(title="新奥危险货物运输高风险路段聚类分析图"),
                                    )
    # 将地图加载到网页
    bd_map = bd_map.render(lines_file_dir)

    # 用浏览器打开文件
    webbrowser.open(lines_file_dir)

    # # 地图中心
    # map_center = [all_data['long_BaiDu'].mean(), all_data['lat_GPS'].mean()]
    #
    # c = (
    #     BMap(init_opts=opts.InitOpts(width="1920px", height="1080px"))
    #         .add_schema(
    #         baidu_ak=KEY,
    #         center=map_center,
    #         zoom=10,
    #         is_roam=True,
    #         map_style={
    #             "styleJson": [{
    #                 "featureType": "estatelabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#8d694eff"
    #                 }
    #             }, {
    #                 "featureType": "restaurantlabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "restaurantlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "lifeservicelabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "lifeservicelabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "transportationlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "transportationlabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "on"
    #                 }
    #             }, {
    #                 "featureType": "financelabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "financelabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "land",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "building",
    #                 "elementType": "geometry.topfill",
    #                 "stylers": {
    #                     "color": "#e7dfd6ff"
    #                 }
    #             }, {
    #                 "featureType": "building",
    #                 "elementType": "geometry.sidefill",
    #                 "stylers": {
    #                     "color": "#f4ebe2ff"
    #                 }
    #             }, {
    #                 "featureType": "building",
    #                 "elementType": "geometry.stroke",
    #                 "stylers": {
    #                     "color": "#b9a797ff"
    #                 }
    #             }, {
    #                 "featureType": "estatelabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ebe1d8ff"
    #                 }
    #             }, {
    #                 "featureType": "estatelabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "estatelabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "28"
    #                 }
    #             }, {
    #                 "featureType": "manmade",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff"
    #                 }
    #             }, {
    #                 "featureType": "manmade",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "manmade",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "36"
    #                 }
    #             }, {
    #                 "featureType": "manmade",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#b6997fff"
    #                 }
    #             }, {
    #                 "featureType": "green",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "education",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "medical",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "scenicspots",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "entertainment",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "estate",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "shopping",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "visibility": "on",
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "transportation",
    #                 "elementType": "geometry",
    #                 "stylers": {
    #                     "color": "#ecececff"
    #                 }
    #             }, {
    #                 "featureType": "transportation",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff"
    #                 }
    #             }, {
    #                 "featureType": "transportation",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#b6997fff"
    #                 }
    #             }, {
    #                 "featureType": "transportation",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "36"
    #                 }
    #             }, {
    #                 "featureType": "medical",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff"
    #                 }
    #             }, {
    #                 "featureType": "medical",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#b6997fff"
    #                 }
    #             }, {
    #                 "featureType": "medical",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "36"
    #                 }
    #             }, {
    #                 "featureType": "education",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff"
    #                 }
    #             }, {
    #                 "featureType": "education",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#b6997fff"
    #                 }
    #             }, {
    #                 "featureType": "education",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "36"
    #                 }
    #             }, {
    #                 "featureType": "carservicelabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "carservicelabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "shoppinglabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "hotellabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "governmentlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "companylabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "businesstowerlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "entertainmentlabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "entertainmentlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "medicallabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "educationlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "scenicspotslabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "airportlabel",
    #                 "elementType": "labels.icon",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "airportlabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "36"
    #                 }
    #             }, {
    #                 "featureType": "airportlabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff"
    #                 }
    #             }, {
    #                 "featureType": "airportlabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#b6997fff"
    #                 }
    #             }, {
    #                 "featureType": "scenicspotslabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "28"
    #                 }
    #             }, {
    #                 "featureType": "scenicspotslabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#4a4a4aff"
    #                 }
    #             }, {
    #                 "featureType": "scenicspotslabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "educationlabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#8d694eff"
    #                 }
    #             }, {
    #                 "featureType": "educationlabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ebe1d8ff"
    #                 }
    #             }, {
    #                 "featureType": "educationlabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "26"
    #                 }
    #             }, {
    #                 "featureType": "medicallabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#8d694eff"
    #                 }
    #             }, {
    #                 "featureType": "medicallabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ebe1d8ff"
    #                 }
    #             }, {
    #                 "featureType": "medicallabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "24"
    #                 }
    #             }, {
    #                 "featureType": "businesstowerlabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ebe1d8ff"
    #                 }
    #             }, {
    #                 "featureType": "businesstowerlabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#8d694eff"
    #                 }
    #             }, {
    #                 "featureType": "businesstowerlabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "24"
    #                 }
    #             }, {
    #                 "featureType": "companylabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "hotellabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#8d694eff"
    #                 }
    #             }, {
    #                 "featureType": "hotellabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ebe1d8ff"
    #                 }
    #             }, {
    #                 "featureType": "hotellabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "24"
    #                 }
    #             }, {
    #                 "featureType": "shoppinglabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#8d694eff"
    #                 }
    #             }, {
    #                 "featureType": "shoppinglabel",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ebe1d8ff"
    #                 }
    #             }, {
    #                 "featureType": "transportationlabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#4a4a4aff"
    #                 }
    #             }, {
    #                 "featureType": "transportationlabel",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "24"
    #                 }
    #             }, {
    #                 "featureType": "scenicspots",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff"
    #                 }
    #             }, {
    #                 "featureType": "scenicspots",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#b6997fff"
    #                 }
    #             }, {
    #                 "featureType": "scenicspots",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "36"
    #                 }
    #             }, {
    #                 "featureType": "governmentlabel",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#4a4a4aff"
    #                 }
    #             }, {
    #                 "featureType": "scenicspotslabel",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "off"
    #                 }
    #             }, {
    #                 "featureType": "district",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "district",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#72533aff",
    #                     "weight": "3.5"
    #                 }
    #             }, {
    #                 "featureType": "town",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#72533aff",
    #                     "weight": "3"
    #                 }
    #             }, {
    #                 "featureType": "town",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "village",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ffffffff",
    #                     "weight": "2.5"
    #                 }
    #             }, {
    #                 "featureType": "village",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#72533aff",
    #                     "weight": "40"
    #                 }
    #             }, {
    #                 "featureType": "village",
    #                 "elementType": "labels.text",
    #                 "stylers": {
    #                     "fontsize": "20"
    #                 }
    #             }, {
    #                 "featureType": "highway",
    #                 "elementType": "geometry.fill",
    #                 "stylers": {
    #                     "color": "#fdf0daff"
    #                 }
    #             }, {
    #                 "featureType": "highway",
    #                 "elementType": "geometry.stroke",
    #                 "stylers": {
    #                     "color": "#ffd993ff"
    #                 }
    #             }, {
    #                 "featureType": "highway",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#000000ff"
    #                 }
    #             }, {
    #                 "featureType": "highway",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "nationalway",
    #                 "elementType": "geometry.fill",
    #                 "stylers": {
    #                     "color": "#fdf0daff"
    #                 }
    #             }, {
    #                 "featureType": "nationalway",
    #                 "elementType": "geometry.stroke",
    #                 "stylers": {
    #                     "color": "#ffd993ff"
    #                 }
    #             }, {
    #                 "featureType": "nationalway",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#000000ff"
    #                 }
    #             }, {
    #                 "featureType": "nationalway",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "provincialway",
    #                 "elementType": "geometry.stroke",
    #                 "stylers": {
    #                     "color": "#ffd993ff"
    #                 }
    #             }, {
    #                 "featureType": "provincialway",
    #                 "elementType": "geometry.fill",
    #                 "stylers": {
    #                     "color": "#fdf0daff"
    #                 }
    #             }, {
    #                 "featureType": "provincialway",
    #                 "elementType": "labels.text.fill",
    #                 "stylers": {
    #                     "color": "#000000ff"
    #                 }
    #             }, {
    #                 "featureType": "provincialway",
    #                 "elementType": "labels.text.stroke",
    #                 "stylers": {
    #                     "color": "#ffffffff"
    #                 }
    #             }, {
    #                 "featureType": "subway",
    #                 "elementType": "geometry.fill",
    #                 "stylers": {
    #                     "color": "#f5a117ff"
    #                 }
    #             }, {
    #                 "featureType": "manmade",
    #                 "elementType": "labels",
    #                 "stylers": {
    #                     "visibility": "on"
    #                 }
    #             }]
    #         },
    #     )
    #         .add(
    #         "低风险路段",
    #         type_="lines",
    #         is_polyline=True,
    #         data_pair=all_map_data,
    #         linestyle_opts=opts.LineStyleOpts(opacity=0.8, width=5),
    #         effect_opts=opts.EffectOpts(),
    #         label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
    #         itemstyle_opts=opts.ItemStyleOpts(color='green'),
    #         # 如果不是最新版本的话可以注释下面的参数（效果差距不大）
    #         # progressive=200,
    #         # progressive_threshold=500,
    #     )
    #         .render(lines_file_dir)
    # )

    # 用浏览器打开文件
    # webbrowser.open(lines_file_dir)
