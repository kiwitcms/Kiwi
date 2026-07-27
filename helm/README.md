# Helm charts for Kiwi TCMS

**WARNING:** this directory is a community contribution and isn't very well tested -
use at your own risk!

Please open a pull request for any improvements and/or problems you may have with this
chart - the Kiwi TCMS isn't going to actively maintain it!


## TL;DR

```console
git clone https://github.com/kiwitcms/Kiwi.git

cd Kiwi/helm

helm dependency update

helm upgrade --install kiwi --namespace kiwi --create-namespace .  --set database.password=$(pwgen 30 1)
```

## Introduction

This chart bootstraps a Kiwi TCMS instance on a Kubernetes cluster using the Helm package manager.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure

## Installing the Chart

To install the chart with the release name `my-release`:

ATTENTION: make sure you have `pwgen` utility installed. Otherwise consider to supply a pre-generated password

```console
git clone https://github.com/kiwitcms/Kiwi.git

cd Kiwi/helm

helm dependency update

helm upgrade --install kiwi --namespace kiwi --create-namespace .  --set database.password=$(pwgen 30 1)

# Once kiwi pod is running:
kubectl [--namespace kiwi] exec -it kiwi-0 -c kiwi -- /Kiwi/manage.py set_domain kiwi.example.com
```

The command deploys Kiwi TCMS on the Kubernetes cluster in the default configuration.
Please check values.yaml file to see which parameters can be configured during an installation.

> **Tip**: List all releases using `helm list [--namespace kiwi]`

## Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

```console
helm delete my-release [--namespace kiwi]
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Known bugs
* MariaDB does not ignite init DB scripts. If you see the kiwi-mariadb-0 pod not Running (just 0/1), execute the following command:
```
kubectl [--namespace kiwi] exec -it kiwi-mariadb-0 -- bash /docker-entrypoint-initdb.d/prepare.sh
```
