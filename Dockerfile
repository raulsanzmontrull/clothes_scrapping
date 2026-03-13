FROM python:3.10

RUN mkdir /srv/project/

WORKDIR /srv/project/

COPY requirements.txt pyproject.toml README.md ./

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY assets ./assets
COPY infra ./infra
COPY schema ./schema
COPY src ./src
COPY tests ./tests

RUN chmod +x /srv/project/infra/get_last_price.sh
RUN chmod +x /srv/project/tests/test__infra__get_last_price.sh

RUN mkdir output/

EXPOSE 34617

WORKDIR /srv/project

CMD ["python", "-m", "src.scrapper.scrap", "--help"]
