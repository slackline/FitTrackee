FROM node:23-alpine AS node-builder

RUN mkdir -p /usr/src/app/fittrackee_client /usr/src/app/fittrackee
WORKDIR /usr/src/app/fittrackee_client

ENV PATH /usr/src/app/fittrackee_client/node_modules/.bin:$PATH
COPY fittrackee_client/package.json /usr/src/app/fittrackee_client/package.json
COPY fittrackee_client/yarn.lock /usr/src/app/fittrackee_client/yarn.lock
RUN yarn install --silent --network-timeout 300000

COPY fittrackee_client/. /usr/src/app/fittrackee_client
RUN yarn build

FROM python:3.13-alpine AS python-builder

RUN mkdir -p /usr/src/app/
WORKDIR /usr/src/app/

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV=/opt/venv

COPY pyproject.toml poetry.lock README.md /usr/src/app/
COPY fittrackee/. /usr/src/app/fittrackee/

RUN python3 -m venv $VIRTUAL_ENV && pip install --upgrade pip
RUN pip install poetry==1.8.5 && . $VIRTUAL_ENV/bin/activate && poetry install --only main --no-interaction --quiet

FROM python:3.13-alpine AS runtime

RUN apk add --no-cache tini

RUN addgroup -g 1000 -S fittrackee && \
    adduser -H -D -u 1000 -S fittrackee -G fittrackee

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:$PATH"

COPY --chown=fittrackee --from=python-builder /opt/venv "$VIRTUAL_ENV"
COPY --chown=fittrackee --from=python-builder /usr/src/app/fittrackee /usr/src/app/fittrackee
COPY --chown=fittrackee --from=node-builder /usr/src/app/fittrackee/dist /usr/src/app/fittrackee/dist
COPY --chown=fittrackee docker-entrypoint.sh /usr/src/app/

RUN chmod 555 /usr/src/app/docker-entrypoint.sh

USER fittrackee

ENTRYPOINT ["/sbin/tini", "--"]