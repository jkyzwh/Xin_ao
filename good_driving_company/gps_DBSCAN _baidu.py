# -*- coding: utf-8 -*-

"""
Created on Tue 2020/10/12
本程序用于新奥公司提供的数据集的测试，对异常行为点的聚类，可视化展示
利用百度地图进行聚类结果的可视化

@author: Zhwh-notbook
"""
import pandas as pd
import numpy as np
import os
import platform

import requests
import math
import random

import scipy.spatial.distance
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


# 根据轮廓系数选择最佳的聚类参数组合
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


# 随机确定颜色
def color_choice():
    color = ['snow', 'ghost white', 'white smoke', 'gainsboro', 'floral white', 'old lace',
             'linen', 'antique white', 'papaya whip', 'blanched almond', 'bisque', 'peach puff',
             'navajo white', 'lemon chiffon', 'mint cream', 'azure', 'alice blue', 'lavender',
             'lavender blush', 'misty rose', 'dark slate gray', 'dim gray', 'slate gray',
             'light slate gray', 'gray', 'light grey', 'midnight blue', 'navy', 'cornflower blue', 'dark slate blue',
             'slate blue', 'medium slate blue', 'light slate blue', 'medium blue', 'royal blue', 'blue',
             'dodger blue', 'deep sky blue', 'sky blue', 'light sky blue', 'steel blue', 'light steel blue',
             'light blue', 'powder blue', 'pale turquoise', 'dark turquoise', 'medium turquoise', 'turquoise',
             'cyan', 'light cyan', 'cadet blue', 'medium aquamarine', 'aquamarine', 'dark green', 'dark olive green',
             'dark sea green', 'sea green', 'medium sea green', 'light sea green', 'pale green', 'spring green',
             'lawn green', 'medium spring green', 'green yellow', 'lime green', 'yellow green',
             'forest green', 'olive drab', 'dark khaki', 'khaki', 'pale goldenrod', 'light goldenrod yellow',
             'light yellow', 'yellow', 'gold', 'light goldenrod', 'goldenrod', 'dark goldenrod', 'rosy brown',
             'indian red', 'saddle brown', 'sandy brown',
             'dark salmon', 'salmon', 'light salmon', 'orange', 'dark orange',
             'coral', 'light coral', 'tomato', 'orange red', 'red', 'hot pink', 'deep pink', 'pink', 'light pink',
             'pale violet red', 'maroon', 'medium violet red', 'violet red',
             'medium orchid', 'dark orchid', 'dark violet', 'blue violet', 'purple', 'medium purple',
             'thistle', 'snow2', 'snow3',
             'snow4', 'seashell2', 'seashell3', 'seashell4', 'AntiqueWhite1', 'AntiqueWhite2',
             'AntiqueWhite3', 'AntiqueWhite4', 'bisque2', 'bisque3', 'bisque4', 'PeachPuff2',
             'PeachPuff3', 'PeachPuff4', 'NavajoWhite2', 'NavajoWhite3', 'NavajoWhite4',
             'LemonChiffon2', 'LemonChiffon3', 'LemonChiffon4', 'cornsilk2', 'cornsilk3',
             'cornsilk4', 'ivory2', 'ivory3', 'ivory4', 'honeydew2', 'honeydew3', 'honeydew4',
             'LavenderBlush2', 'LavenderBlush3', 'LavenderBlush4', 'MistyRose2', 'MistyRose3',
             'MistyRose4', 'azure2', 'azure3', 'azure4', 'SlateBlue1', 'SlateBlue2', 'SlateBlue3',
             'SlateBlue4', 'RoyalBlue1', 'RoyalBlue2', 'RoyalBlue3', 'RoyalBlue4', 'blue2', 'blue4',
             'DodgerBlue2', 'DodgerBlue3', 'DodgerBlue4', 'SteelBlue1', 'SteelBlue2',
             'SteelBlue3', 'SteelBlue4', 'DeepSkyBlue2', 'DeepSkyBlue3', 'DeepSkyBlue4',
             'SkyBlue1', 'SkyBlue2', 'SkyBlue3', 'SkyBlue4', 'LightSkyBlue1', 'LightSkyBlue2',
             'LightSkyBlue3', 'LightSkyBlue4', 'SlateGray1', 'SlateGray2', 'SlateGray3',
             'SlateGray4', 'LightSteelBlue1', 'LightSteelBlue2', 'LightSteelBlue3',
             'LightSteelBlue4', 'LightBlue1', 'LightBlue2', 'LightBlue3', 'LightBlue4',
             'LightCyan2', 'LightCyan3', 'LightCyan4', 'PaleTurquoise1', 'PaleTurquoise2',
             'PaleTurquoise3', 'PaleTurquoise4', 'CadetBlue1', 'CadetBlue2', 'CadetBlue3',
             'CadetBlue4', 'turquoise1', 'turquoise2', 'turquoise3', 'turquoise4', 'cyan2', 'cyan3',
             'cyan4', 'DarkSlateGray1', 'DarkSlateGray2', 'DarkSlateGray3', 'DarkSlateGray4',
             'aquamarine2', 'aquamarine4', 'DarkSeaGreen1', 'DarkSeaGreen2', 'DarkSeaGreen3',
             'DarkSeaGreen4', 'SeaGreen1', 'SeaGreen2', 'SeaGreen3', 'PaleGreen1', 'PaleGreen2',
             'PaleGreen3', 'PaleGreen4', 'SpringGreen2', 'SpringGreen3', 'SpringGreen4',
             'green2', 'green3', 'green4', 'chartreuse2', 'chartreuse3', 'chartreuse4',
             'OliveDrab1', 'OliveDrab2', 'OliveDrab4', 'DarkOliveGreen1', 'DarkOliveGreen2',
             'DarkOliveGreen3', 'DarkOliveGreen4', 'khaki1', 'khaki2', 'khaki3', 'khaki4',
             'LightGoldenrod1', 'LightGoldenrod2', 'LightGoldenrod3', 'LightGoldenrod4',
             'LightYellow2', 'LightYellow3', 'LightYellow4', 'yellow2', 'yellow3', 'yellow4',
             'gold2', 'gold3', 'gold4', 'goldenrod1', 'goldenrod2', 'goldenrod3', 'goldenrod4',
             'DarkGoldenrod1', 'DarkGoldenrod2', 'DarkGoldenrod3', 'DarkGoldenrod4',
             'RosyBrown1', 'RosyBrown2', 'RosyBrown3', 'RosyBrown4', 'IndianRed1', 'IndianRed2',
             'IndianRed3', 'IndianRed4', 'sienna1', 'sienna2', 'sienna3', 'sienna4', 'burlywood1',
             'burlywood2', 'burlywood3', 'burlywood4', 'wheat1', 'wheat2', 'wheat3', 'wheat4', 'tan1',
             'tan2', 'tan4', 'chocolate1', 'chocolate2', 'chocolate3', 'firebrick1', 'firebrick2',
             'firebrick3', 'firebrick4', 'brown1', 'brown2', 'brown3', 'brown4', 'salmon1', 'salmon2',
             'salmon3', 'salmon4', 'LightSalmon2', 'LightSalmon3', 'LightSalmon4', 'orange2',
             'orange3', 'orange4', 'DarkOrange1', 'DarkOrange2', 'DarkOrange3', 'DarkOrange4',
             'coral1', 'coral2', 'coral3', 'coral4', 'tomato2', 'tomato3', 'tomato4', 'OrangeRed2',
             'OrangeRed3', 'OrangeRed4', 'red2', 'red3', 'red4', 'DeepPink2', 'DeepPink3', 'DeepPink4',
             'HotPink1', 'HotPink2', 'HotPink3', 'HotPink4', 'pink1', 'pink2', 'pink3', 'pink4',
             'LightPink1', 'LightPink2', 'LightPink3', 'LightPink4', 'PaleVioletRed1',
             'PaleVioletRed2', 'PaleVioletRed3', 'PaleVioletRed4', 'maroon1', 'maroon2',
             'maroon3', 'maroon4', 'VioletRed1', 'VioletRed2', 'VioletRed3', 'VioletRed4',
             'magenta2', 'magenta3', 'magenta4', 'orchid1', 'orchid2', 'orchid3', 'orchid4', 'plum1',
             'plum2', 'plum3', 'plum4', 'MediumOrchid1', 'MediumOrchid2', 'MediumOrchid3',
             'MediumOrchid4', 'DarkOrchid1', 'DarkOrchid2', 'DarkOrchid3', 'DarkOrchid4',
             'purple1', 'purple2', 'purple3', 'purple4', 'MediumPurple1', 'MediumPurple2',
             'MediumPurple3', 'MediumPurple4', 'thistle1', 'thistle2', 'thistle3', 'thistle4',
             'gray1', 'gray2', 'gray3', 'gray4', 'gray5', 'gray6', 'gray7', 'gray8', 'gray9', 'gray10',
             'gray11', 'gray12', 'gray13', 'gray14', 'gray15', 'gray16', 'gray17', 'gray18', 'gray19',
             'gray20', 'gray21', 'gray22', 'gray23', 'gray24', 'gray25', 'gray26', 'gray27', 'gray28',
             'gray29', 'gray30', 'gray31', 'gray32', 'gray33', 'gray34', 'gray35', 'gray36', 'gray37',
             'gray38', 'gray39', 'gray40', 'gray42', 'gray43', 'gray44', 'gray45', 'gray46', 'gray47',
             'gray48', 'gray49', 'gray50', 'gray51', 'gray52', 'gray53', 'gray54', 'gray55', 'gray56',
             'gray57', 'gray58', 'gray59', 'gray60', 'gray61', 'gray62', 'gray63', 'gray64', 'gray65',
             'gray66', 'gray67', 'gray68', 'gray69', 'gray70', 'gray71', 'gray72', 'gray73', 'gray74',
             'gray75', 'gray76', 'gray77', 'gray78', 'gray79', 'gray80', 'gray81', 'gray82', 'gray83',
             'gray84', 'gray85', 'gray86', 'gray87', 'gray88', 'gray89', 'gray90', 'gray91', 'gray92',
             'gray93', 'gray94', 'gray95', 'gray97', 'gray98', 'gray99']

    return random.choice(color)


# 调用百度地图绘制点图，不同类型风险行为采用颜色不同的标记
def plot_map(point_data, path):
    point_data = point_data[point_data['remarks'] != 'no_result']
    data = point_data[['lat_BaiDu', 'long_BaiDu', 'behavior', 'label']].copy()
    data.columns = ['lat', 'lon', 'behavior', 'label']

    # 地图中心
    map_center = [data['lon'].mean(), data['lat'].mean()]
    # 初始化百度地图
    bd_map = BMap(init_opts=opts.InitOpts(width="1920px", height="1080px"))
    bd_map.add_schema(baidu_ak=KEY,
                      center=map_center,
                      zoom=8, is_roam=True,
                      map_style=None,
                      )

    color = ['red', 'green', 'blue', 'yellow', 'gold', 'cyan', 'magenta', 'purple']

    behavior_list = data.drop_duplicates(['behavior'])['behavior'].copy()  # 剔除重复的数据文件路径
    i = 0
    for behavior in behavior_list:
        behavior_data = data[data['behavior'] == behavior]
        # behavior_color = color_choice()  # 从color列表中随机抽取一个颜色
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
            data_pair=map_data,
            symbol_size=20,
            effect_opts=opts.EffectOpts(),
            label_opts=opts.LabelOpts(formatter="{b}", position="left", is_show=False),
            itemstyle_opts=opts.ItemStyleOpts(color=behavior_color),
        )

    # 显示聚类分析的结果
    label_list = data.drop_duplicates(['label'])['label'].copy()

    map_data = []

    for label in label_list:
        if label == -1:
            continue
        else:
            label_data = data[data['label'] == label]

            # 将聚类点命名增加至地图地名空间

            name = '高风险路段_' + str(label)

            bd_map.add_coordinate(name=name,
                                  longitude=label_data['lon'].mean(),
                                  latitude=label_data['lat'].mean()
                                  )
            map_data.append((name, len(label_data)))

    # 将地点增加到百度地图
    bd_map = bd_map.add(
        series_name='高风险行为频发路段',
        type_="scatter",
        data_pair=map_data,
        symbol_size=50,
        # blur_size=500,
        is_selected=True,  # 是否选中图例
        effect_opts=opts.EffectOpts(),
        label_opts=opts.LabelOpts(formatter="{b}", position="right", is_show=False),
        itemstyle_opts=opts.ItemStyleOpts(color='rgba(138,43,226, 0.8)'),
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

    bd_map = bd_map.render(path)

    # 用浏览器打开文件
    webbrowser.open(path)
    return bd_map


# -------------------------------------------------------------------------
if __name__ == "__main__":
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
    abnormal_gps = abnormal_data[['lat_BaiDu', 'long_BaiDu']]

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

    n_raito = len(labels[labels[:] == -1]) / len(labels)  # 计算噪声点个数占总数的比例
    print('全部异常行为数据中随机事件占比为', n_raito)
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)  # 获取分簇的数目
    print('数据中发现的异常行为集中发生路段数量为', n_clusters_)
    # score = metrics.silhouette_score(distance_matrix, labels)
    abnormal_data['label'] = labels

    # 轨迹可视化, 定义保存轨迹可视化html的文件名
    save_file_name = 'abnormal_dbscan.html'
    if not os.path.exists(MAP_SAVE_PATH):
        os.mkdir(MAP_SAVE_PATH)
    file_dir = os.path.join(MAP_SAVE_PATH, save_file_name)

    map_plot = plot_map(point_data=abnormal_data,
                        path=file_dir)

    # 将融合了逐桩坐标的试验数据储存在硬盘上
    if not os.path.exists(DATA_SAVE_PATH):
        os.mkdir(DATA_SAVE_PATH)
    dbscan_data_path = os.path.join(DATA_SAVE_PATH, "dbscan_result.csv")
    print("dbscan聚类分析数据保存在临时文件内，临时文件的保存路径为：", dbscan_data_path)
    abnormal_data.to_csv(dbscan_data_path, index=False, sep=',', encoding='utf_8_sig')


