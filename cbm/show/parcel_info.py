#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import json
import rasterio
from matplotlib import gridspec
import matplotlib.pyplot as plt
from copy import copy
from os.path import join, normpath, isfile, getsize
from descartes import PolygonPatch
from rasterio.plot import show

from cbm.utils import config, spatial_utils
from cbm.get import background as get_bg
from cbm.get import parcel_info


def overlay_parcel(geom):
    """Create parcel polygon overlay"""
    patche = [PolygonPatch(feature, edgecolor="yellow",
                           facecolor="none", linewidth=2
                           ) for feature in geom['geom']]
    return patche


def by_pid(aoi, year, pid, ptype=None, tms='osm', debug=False):
    """Show parcel information with an image with polygon overlay by selected
    parcel id. This function will get an image from the center of the polygon.

    Examples:
        from cbm.show import parcel_info
        parcel_info.by_id(aoi, year, pid)

    Arguments:
        aoi, the area of interest (str)
        year, the year of parcels table
        pid, the parcel id (str).
        ptype, parcel type
        debug, print or not procedure information (Boolean).
    """

    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            aoi, str(year), str(pid)))
    bg_path = normpath(join(workdir, 'backgrounds'))

    file_info = normpath(join(workdir, 'info.json'))
    if not isfile(file_info):
        if not parcel_info.by_pid(aoi, str(year), str(pid), ptype,
                                  True, False, debug):
            return "No parcel found, please check the parcel ID"
    with open(normpath(join(workdir, 'info.json')), 'r') as f:
        parcel = json.load(f)

    plt.rcParams['font.size'] = 14
    plt.figure(figsize=(10, 3))
    gs = gridspec.GridSpec(1, 2)
    ax1 = plt.subplot(gs[0, 0])
    ax2 = plt.subplot(gs[0, 1])

    try:
        if not isfile(normpath(join(bg_path, f'{tms}.tif'))):
            get_bg.by_pid(aoi, year, pid, 256, 1024, tms, ptype, True, debug)
        elif getsize(normpath(join(bg_path, f'osm.tif'))) < 1000:
            get_bg.by_pid(aoi, year, pid, 256, 1024, tms, ptype, True, debug)
        with rasterio.open(normpath(join(bg_path, f'{tms}.tif'))) as img:
            img_epsg = img.crs.to_epsg()
            geom = spatial_utils.transform_geometry(parcel, img_epsg)
            patches = overlay_parcel(geom)
            for patch in patches:
                ax2.add_patch(copy(patch))
            show(img, ax=ax2)
    except Exception as err:
        print("Could not get image. ", err)

    text = [
        f"AOI: {aoi}",
        f"Year: {year}",
        f"Parcel ID: {pid}",
        f"Crop type: {parcel['cropname'][0]}",
        f"Crop type code: {parcel['cropcode'][0]}",
        f"Area: {parcel['area'][0]} sqm",
        f"Centroid (Lat/Lon): {parcel['clat'][0]:.6f}, {parcel['clon'][0]:.6f}",
        f"Geometry SRID: {parcel['srid'][0]}"
    ]
    first_line = 0.9
    for t in text:
        ax1.text(0, first_line, t)
        first_line -= 0.12

    ax1.axis('off')
    ax2.axis('off')
    plt.show()
