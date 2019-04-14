FROM python:3
RUN mkdir /app
WORKDIR /app
ADD jupyter_notebook_config.py /app/
ADD ta-lib-0.4.0-src.tar.gz /app/
RUN cd ta-lib/ &&  ./configure --prefix=/usr &&  make &&  make install && pip install TA-Lib && cd .. && rm -rf ta-lib/
ADD requirements.txt /app/
RUN pip install -r requirements.txt

RUN useradd -r -g users non_root && chown -R non_root:users /app && mkdir /home/non_root && chown -R non_root:users /home/non_root
ENTRYPOINT jupyter notebook --config=/app/jupyter_notebook_config.py --allow-root