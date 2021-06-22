FROM python:3.7
RUN mkdir /usr/src/app/
COPY requirements.txt /usr/src/app/requirements.txt
EXPOSE 5000
WORKDIR /usr/src/app/
RUN pip install -r requirements.txt
COPY . /usr/src/app/
CMD ["python", "app.py"]