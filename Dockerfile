FROM python:3.8.5
RUN pip install \
    beautifulsoup4==4.9.1 \
    folium==0.11.0 \
    lxml==4.5.2 \
    moviepy==1.0.3 \
    selenium==3.141.0
RUN \
    curl -L https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz -o /tmp/geckodriver.tar.gz && \
    tar -xf /tmp/geckodriver.tar.gz && \
    mv /geckodriver /usr/bin/geckodriver
WORKDIR /app
ENTRYPOINT ["python", "combined-routes.py"]
