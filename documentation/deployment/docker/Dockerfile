# build Sphinx documentation
FROM sphinxdoc/sphinx:5.3.0 as build

RUN apt-get update && apt-get install -y libpq-dev gcc
WORKDIR /docs

ADD docs /docs/source
ADD requirements.txt /docs

RUN pip3 install --upgrade pip \
    && pip3 install -r requirements.txt \
    && sphinx-build -M html source build

# serve the documentation with nginx
FROM nginx:1.23.2-alpine

COPY --from=build /docs/build/html /usr/share/nginx/html
