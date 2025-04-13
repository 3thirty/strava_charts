# Building

## Docker
### Dev Docker Build
To run the application in a docker container in dev mode:

```
make docker-build-dev
make docker-run
```

This will start listening on port 8080, with self-signed certificates

### Prod Docker Build
To build the production docker image:

```
make docker-build
```

This will produce a docker image with the application, expecting to be executed on AWS Lambda

## Github Actions
Github Actions are used to deploy the application to AWS with SAM (see below)

The workflow files are at:

  * `.github/workflows/build.yaml` - Builds the image on each PR
  * `.github/workflows/deploy.yml` - Builds the image and deploys on each merge to `master`


## SAM
For deploying to AWS, we use SAM, defined in `sam-template.yaml`

### Dev
To locally test the SAM setup

```
sam build --template-file build/sam-template.yaml
sam local start-api --template-file .aws-sam/build/template.yaml
```

### Prod

