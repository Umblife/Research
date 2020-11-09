# マシン本体：CUDA >= 11.1.0，NVIDIA Driver Version >= 455.32.00
FROM nvcr.io/nvidia/pytorch:20.10-py3

LABEL maintainer="Umblife" \
      mail="umblife@gmail.com" \
      description="Dockerfile reproduces my environment"

# tmuxと必要なパッケージのインストール．tzdataはtimezone気にしないなら入れなくてもOK
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y tmux tzdata
RUN apt-get install -y sqlite3 libsqlite3-dev libcurl4-gnutls-dev libtiff5-dev

# PROJのインストール
RUN cd /workspace
ADD https://download.osgeo.org/proj/proj-6.2.1.tar.gz /workspace/proj-6.2.1.tar.gz
RUN tar -zxvf proj-6.2.1.tar.gz
RUN cd ./proj-6.2.1 \
    && ./configure --prefix=/usr \
    && make -j$(nproc) \
    && make install

# GEOSのインストール
RUN cd /workspace
ADD http://download.osgeo.org/geos/geos-3.8.1.tar.bz2 /workspace/geos-3.8.1.tar.bz2
RUN tar -jxvf geos-3.8.1.tar.bz2
RUN cd ./geos-3.8.1 \
    && ./configure --prefix=/usr \
    && make -j$(nproc) \
    && make install

# 余分なファイルの削除
RUN rm -rf /workspace/proj-6.2.1
RUN rm -rf /workspace/geos-3.8.1
RUN rm -f /workspace/proj-6.2.1.tar.gz
RUN rm -f /workspace/geos-3.8.1.tar.bz2

# pythonライブラリのインストール
RUN pip install --upgrade pip
RUN pip install folium==0.11.0 Pillow==7.2.0 pyshp==2.1.2 cryptography==3.2.1
RUN pip install shapely==1.7.1 --no-binary shapely
RUN pip install cartopy==0.18.0 --no-binary cartopy