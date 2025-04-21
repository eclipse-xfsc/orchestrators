ARG BASE_IMAGE_PREFIX=""
FROM ${BASE_IMAGE_PREFIX}library/golang:1.19.3-alpine3.16 AS build

# set workdir and copy files
WORKDIR /terraform-api
COPY . ./

# install packages, generate API docs and build the API
RUN apk update && apk add --no-cache git \
    && go mod download \
    && go install github.com/swaggo/swag/cmd/swag@v1.8.9 \
    && $GOPATH/bin/swag init --parseDependency --parseInternal --parseDepth 1 \
    && CGO_ENABLED=0 GOOS=linux go build -v -a -installsuffix cgo -o main main.go

FROM ${BASE_IMAGE_PREFIX}library/golang:1.19.3-alpine3.16

# set workdir and copy files from build
WORKDIR /terraform-api
COPY --from=build ./terraform-api/main /go/bin

# set API version
ARG API_VERSION="unknown"
ENV TERRAFORM_API_VERSION=${API_VERSION}

# expose API port
EXPOSE 8080

# prepare API for running
CMD ["/go/bin/main"]
