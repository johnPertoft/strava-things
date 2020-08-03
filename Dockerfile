FROM python:3.8.5
RUN pip install folium==0.11.0
WORKDIR /app
ENTRYPOINT ["python", "combined-routes.py"]
