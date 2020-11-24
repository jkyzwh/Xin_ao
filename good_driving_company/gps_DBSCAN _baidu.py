# -*- coding: utf-8 -*-

"""
Created on Tue 2020/10/12
本程序用于新奥公司提供的数据集的测试，对异常行为点的聚类，可视化展示

@author: Zhwh-notbook
"""
import pandas as pd
import numpy as np
import os
import platform

import requests
import math

import scipy.spatial.distance
from sklearn.cluster import DBSCAN
from sklearn import metrics
import folium
import webbrowser

# import statsmodels.api as sm
# import xlrd

# import scipy.stats as stats
# import json
# from urllib.parse import urlencode
# import datetime
# import time

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


# 根据GPS坐标计算两点之间的地球距离
def haversine(lonlat1, lonlat2):
    lat1, lon1 = lonlat1
    lat2, lon2 = lonlat2
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6378.137  # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000


# 根据轮廓系数悬着最佳的聚类参数组合
def dbscan_silhouette(data):
    res = []
    # 迭代不同的eps值
    for eps in np.arange(100, 2000, 100):
        # 迭代不同的min_samples值
        for min_samples in range(2, 11):
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            # 模型拟合
            dbscan.fit(data)
            # 统计各参数组合下的聚类个数（-1表示不存在集中的异常行为）
            n_clusters = len([i for i in set(dbscan.labels_) if i != -1])
            # 离散随机行为的个数
            outliners = np.sum(np.where(dbscan.labels_ == -1, 1, 0))
            # 统计每个簇的样本个数
            # stats = pd.Series([i for i in dbscan.labels_ if i != -1]).value_counts()
            # 计算聚类得分
            try:
                score = metrics.silhouette_score(data, dbscan.labels_)
            except:
                score = -99
            res.append({'eps': eps, 'min_samples': min_samples, 'n_clusters': n_clusters, 'outliners': outliners,
                        'score': score})
    # 将迭代后的结果存储到数据框中
    result = pd.DataFrame(res)
    return result


# 中文转换
def parse_zhch(s):
    return str(str(s).encode('ascii', 'xmlcharrefreplace'))[2:-1]


# 调用folium包绘制点图，不同类型风险行为采用不同的标记
def plot_map(map_type, point_data):
    if map_type == 'GPS':
        all_data = point_data[['lat_GPS', 'long_GPS', 'behavior', 'label']]
        all_data.columns = ['lat', 'long', 'behavior', 'label']

        # 地图类型，google 卫星图
        map_tiles = 'https://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        # 地图类型，google 地图
        # map_tiles = 'https://mt.google.com/vt/lyrs=h&x={x}&y={y}&z={z}'

    if map_type == 'Gaode':
        all_data = point_data[['lat_GaoDe', 'long_GaoDe', 'behavior', 'label']]
        all_data.columns = ['lat', 'long', 'behavior', 'label']

        # 地图类型，高德街道图
        map_tiles = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}'
        # 地图类型，高德卫星图
        # map_tiles = 'http://webst02.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'

    # 地图中心
    map_center = [all_data['lat'].mean(), all_data['long'].mean()]
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

        if 'over_speed' in behavior:
            # 创建异常驾驶行为——超速行为的FeatureGroup
            temp_plot = folium.FeatureGroup(name='超速行为分布', control=True)
        if 'over_acc' in behavior:
            # 创建异常驾驶行为——急加速行为的FeatureGroup
            temp_plot = folium.FeatureGroup(name='急加速行为分布', control=True)
        if 'over_dac' in behavior:
            # 创建异常驾驶行为——急减速行为的FeatureGroup
            temp_plot = folium.FeatureGroup(name='急减速异常行为分布', control=True)
        for row in behavior_data.iterrows():
            icon_kw = dict(prefix='fa',
                           color=behavior_color,
                           icon_color='darkred',
                           icon='cny',
                           )
            icon = folium.Icon(**icon_kw)

            # 悬浮弹出信息
            tooltip = parse_zhch(behavior)

            folium.Marker(
                location=[row[1]['lat'], row[1]['long']],
                popup=parse_zhch(behavior),
                icon=icon,
                tooltip=tooltip,
            ).add_to(temp_plot)

            # 将异常行为group作为Map的child
            map_plot.add_child(temp_plot)

    # 显示聚类分析的结果
    label_list = all_data.drop_duplicates(['label'])['label'].copy()

    # 创建一个聚类结果的FeatureGroup
    label_group = folium.FeatureGroup(name='高风险路段聚类', control=True)

    for label in label_list:
        if label == -1:
            continue
        else:
            label_data = all_data[all_data['label'] == label]
            folium.Circle(location=[label_data['lat'].mean(),
                                    label_data['long'].mean()],
                          radius=500,
                          # popup='popup',
                          color='gray',
                          fill=True,
                          fill_color='gray',
                          ).add_to(label_group)

    # 增加随着鼠标显示经纬度
    map_plot.add_child(folium.LatLngPopup())

    # 将聚类结果group作为Map的child
    map_plot.add_child(label_group)

    # 打开map的LayerControl
    folium.LayerControl().add_to(map_plot)
    return map_plot


# -------------------------------------------------------------------------
def main():
    # 读取配置文件，获得数据文件路径
    DATA_PATH, MAP_SAVE_PATH, DATA_SAVE_PATH = get_config()

    all_data_path = os.path.join(DATA_SAVE_PATH, "all_data.csv")
    abnormal_data_path = os.path.join(DATA_SAVE_PATH, "abnormal_data.csv")

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

    # --------------利用DBSCAN算法对空间GPS坐标进行聚类--------------------------
    abnormal_gps = abnormal_data[['amap_lat', 'amap_long']]
    # 去除na值 
    # abnormal_gps = abnormal_data[['amap_lat', 'amap_long']].dropna(axis=0, how='all')
    # 建立GPS坐标间距离矩阵
    distance_matrix = scipy.spatial.distance.squareform(scipy.spatial.distance.pdist(abnormal_gps,
                                                                                     (lambda u, v: haversine(u, v))
                                                                                     )
                                                        )
    # 多种距离和聚类数量组合的结果
    # dbscan_summry = dbscan_silhouette(distance_matrix)

    # 每500米有5次异常行为集中出现
    labels = DBSCAN(eps=500,
                    min_samples=5,
                    metric='precomputed',
                    n_jobs=-1,
                    ).fit_predict(distance_matrix)
    '''
    db = DBSCAN(eps=0.038, min_samples=3).fit(data)
    '''

    raito = len(labels[labels[:] == -1]) / len(labels)  # 计算噪声点个数占总数的比例
    print('全部异常行为数据中随机事件占比为', raito)
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)  # 获取分簇的数目
    print('数据中发现的异常行为集中发生路段数量为', n_clusters_)
    # score = metrics.silhouette_score(distance_matrix, labels)
    abnormal_data['label'] = labels

    # 轨迹可视化, 定义保存轨迹可视化html的文件名
    save_file_name = 'abnormal_dbscan.html'
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
