# vim:set ft=dockerfile:
FROM continuumio/miniconda3
MAINTAINER https://github.com/bird-house/emu
LABEL Description="Emu: Demo PyWPS" Vendor="Birdhouse" Version="0.11.1"

# Update Debian system
RUN apt-get update && apt-get install -y \
 build-essential \
&& rm -rf /var/lib/apt/lists/*

# Update conda
RUN conda update -n base conda

# Copy WPS project
COPY . /opt/wps

WORKDIR /opt/wps

# Create conda environment
RUN conda env create -n wps -f environment.yml

# Install WPS
RUN ["/bin/bash", "-c", "source activate wps && python setup.py develop"]

# Init DB
RUN ["/bin/bash", "-c", "source activate wps && pywps -c /opt/wps/pywps.cfg migrate"]

# Start WPS service on port 5000 on 0.0.0.0
EXPOSE 5000
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["source activate wps && exec pywps -c /opt/wps/pywps.cfg start -b 0.0.0.0"]

# docker build -t birdhouse/emu .
# docker run -p 5000:5000 birdhouse/emu
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
