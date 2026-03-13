FROM python:3.10

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && mv /root/.local/bin/poetry /usr/local/bin/

RUN mkdir /srv/project/

WORKDIR /srv/project/

COPY pyproject.toml README.md /srv/project/

RUN poetry install --no-root

COPY app /srv/project/app
COPY assets /srv/project/assets
COPY infra /srv/project/infra
COPY schema /srv/project/schema
COPY src /srv/project/src
COPY tests /srv/project/tests

RUN chmod +x /srv/project/infra/get_last_price.sh
RUN chmod +x /srv/project/tests/test__infra__get_last_price.sh

RUN mkdir output/

ENV PATH="/srv/project/.venv/bin:$PATH"

EXPOSE 34617

WORKDIR /srv/project

CMD ["python", "-m", "src.scrapper.scrap", "--help"]
