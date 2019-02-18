# Grafana MSI Generator

Creates a docker image that can be included within CircleCI or run locally to generate an MSI for Grafana.

## Docker Image

The docker image is created and published via CircleCI, and can also be built locally.

### Building an MSI

The process is automated to expect a dist directory, and will build an msi for first matching grafana-*.windows-amd64.zip file found.

```
grafana-5.4.3.windows-amd64.zip
```

## CircleCI



## Manual

A wrapper script takes a single argument for the path to a zip file, or searches for a file in dist.

A manual build can be initiated using docker-compose
```
cd oss
docker-compose up --build
```
## Automated

## Testing

## Change Log
v1.0.0 - initial commit
