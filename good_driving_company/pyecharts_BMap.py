# -*- coding: utf-8 -*-

"""
Created on Tue 2020/09/25
本程序用于新奥公司提供的车在数据终端的数据集的测试，理解数据结构，解析数据含义，转化为方便处理的格式
本程序使用百度地图，pyecharts包
@author: Zhwh-notbook
"""

import platform
import os
import json
from pyecharts.charts import BMap
from pyecharts import options as opts
from pyecharts.faker import Faker

[list(z) for z in zip(Faker.provinces, Faker.values())]
zip(Faker.guangdong_city, Faker.values())


"""
参考地址: https://gallery.echartsjs.com/editor.html?c=bmap-bus
"""

# --------------------------------定义全局变量 开发者key与数字签名 ------------------------

global KEY, EARTH_REDIUS
BAIDU_MAP_AK = 'iHDcbVaHkRo6xz149QBiqlrn2FAbwX6b'


# 读取项目中的 json 文件
def get_map_data():
    operating_system = platform.system()
    scrip_dir = os.path.abspath('.')

    # 读取位于当前目录下的json格式的数据文件
    if operating_system == 'Windows':
        file_name = os.path.join(scrip_dir, "busRoutines.json")
    elif operating_system == 'Linux':
        file_name = os.path.join(scrip_dir, "busRoutines.json")
    else:
        pass

    with open("busRoutines.json", "r", encoding="utf-8") as f:
        bus_lines = json.load(f)

    f.close()
    return bus_lines


bus_lines = get_map_data()



c = (
    BMap(init_opts=opts.InitOpts(width="1200px", height="800px"))
    .add_schema(
        baidu_ak=BAIDU_MAP_AK,
        center=[116.40, 40.04],
        zoom=10,
        is_roam=True,
        map_style={
            "styleJson": [
                {
                    "featureType": "water",
                    "elementType": "all",
                    "stylers": {"color": "#031628"},
                },
                {
                    "featureType": "land",
                    "elementType": "geometry",
                    "stylers": {"color": "#000102"},
                },
                {
                    "featureType": "highway",
                    "elementType": "all",
                    "stylers": {"visibility": "off"},
                },
                {
                    "featureType": "arterial",
                    "elementType": "geometry.fill",
                    "stylers": {"color": "#000000"},
                },
                {
                    "featureType": "arterial",
                    "elementType": "geometry.stroke",
                    "stylers": {"color": "#0b3d51"},
                },
                {
                    "featureType": "local",
                    "elementType": "geometry",
                    "stylers": {"color": "#000000"},
                },
                {
                    "featureType": "railway",
                    "elementType": "geometry.fill",
                    "stylers": {"color": "#000000"},
                },
                {
                    "featureType": "railway",
                    "elementType": "geometry.stroke",
                    "stylers": {"color": "#08304b"},
                },
                {
                    "featureType": "subway",
                    "elementType": "geometry",
                    "stylers": {"lightness": -70},
                },
                {
                    "featureType": "building",
                    "elementType": "geometry.fill",
                    "stylers": {"color": "#000000"},
                },
                {
                    "featureType": "all",
                    "elementType": "labels.text.fill",
                    "stylers": {"color": "#857f7f"},
                },
                {
                    "featureType": "all",
                    "elementType": "labels.text.stroke",
                    "stylers": {"color": "#000000"},
                },
                {
                    "featureType": "building",
                    "elementType": "geometry",
                    "stylers": {"color": "#022338"},
                },
                {
                    "featureType": "green",
                    "elementType": "geometry",
                    "stylers": {"color": "#062032"},
                },
                {
                    "featureType": "boundary",
                    "elementType": "all",
                    "stylers": {"color": "#465b6c"},
                },
                {
                    "featureType": "manmade",
                    "elementType": "all",
                    "stylers": {"color": "#022338"},
                },
                {
                    "featureType": "label",
                    "elementType": "all",
                    "stylers": {"visibility": "off"},
                },
            ]
        },
    )
    .add(
        "",
        type_="lines",
        is_polyline=True,
        data_pair=bus_lines,
        linestyle_opts=opts.LineStyleOpts(opacity=0.2, width=0.5),
        # 如果不是最新版本的话可以注释下面的参数（效果差距不大）
        progressive=200,
        progressive_threshold=500,
    )
    .render("bmap_beijing_bus_routines.html")
)