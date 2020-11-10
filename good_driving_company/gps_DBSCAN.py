# -*- coding: utf-8 -*-

"""
Created on Tue 2020/10/12
本程序用于新奥公司提供的数据集的测试，对异常行为点的聚类，可视化展示

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

# ---------------------------------------------------------------------------------------


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


# 可视化html的中文转换
def parse_zhch(s):
    return str(str(s).encode('ascii', 'xmlcharrefreplace'))[2:-1]


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
        all_data = point_data[['lat_GaoDe', 'long_GaoDe', 'behavior']]
        all_data.columns = ['lat', 'lon', 'behavior']

        # 地图类型，高德街道图
        map_tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
        # 地图类型，高德卫星图
        # map_tiles = 'http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'

    # 地图中心
    map_center = [all_data['lat'].mean(), all_data['lon'].mean()]

    map_plot = folium.Map(location=map_center,
                          zoom_start=5,
                          tiles=map_tiles,
                          attr='default'
                          )

    color = ['red', 'blue', 'green', 'purple', 'orange', 'darkpurple', 'darkgreen',
             'cadetblue', 'white', 'beige', 'lightblue', 'gray', 'lightred',
             'lightgray', 'darkred', 'darkblue', 'lightgreen', 'black', 'pink', ]

    behavior_list = all_data.drop_duplicates(['behavior'])['behavior'].copy()  # 剔除重复的数据文件路径
    i = 0
    for behavior in behavior_list:
        behavior_data = all_data[all_data['behavior'] == behavior]
        behavior_color = color[i]
        i = i + 1

        for name, row in behavior_data.iterrows():
            # 定义图标
            icon_kw = dict(prefix='fa', color=behavior_color, icon_color='darkred', icon='cny')
            icon = folium.Icon(**icon_kw)

            # 悬浮弹出信息
            tooltip = parse_zhch(behavior)

            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=parse_zhch(behavior),
                icon=icon,
                tooltip=tooltip,
            ).add_to(map_plot)

    # 增加随着鼠标显示经纬度
    map_plot.add_child(folium.LatLngPopup())

    return map_plot


# -------------------------------------------------------------------------
def main():
    # 读取配置文件，获得数据文件路径
    DATA_PATH, MAP_SAVE_PATH, DATA_SAVE_PATH = get_config()
    all_data_path = os.path.join(DATA_SAVE_PATH, "all_data.csv")
    abnormal_data_path = os.path.join(DATA_SAVE_PATH, "abnormal_data.csv")

    # 读取数据
    all_data = pd.read_csv(all_data_path,
                           header=0,
                           index_col=False,
                           # names=col_names,
                           low_memory=False
                           )
    abnormal_data = pd.read_csv(abnormal_data_path,
                                header=0,
                                index_col=False,
                                # names=col_names,
                                low_memory=False
                                )

    # 异常行为点的可视化, 定义保存轨迹可视化html的文件名
    save_file_name = 'abnormal_all_test.html'
    if not os.path.exists(MAP_SAVE_PATH):
        os.mkdir(MAP_SAVE_PATH)
    file_dir = os.path.join(MAP_SAVE_PATH, save_file_name)

    map_type = 'Gaode'
    map_plot = plot_map(map_type=map_type,
                        point_data=abnormal_data)
    map_plot.save(file_dir)
    webbrowser.open(file_dir)


# -------------------------------------------------------------------------
if __name__ == "__main__":
    main()
