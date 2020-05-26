openprocurement.bridge.rbot
=====================================

## Development

```bash
$ git clone git@gitlab.qg:op/e-contracting/openprocurement.bridge.rbot.git
$ virtualenv -p python .venv
$ source .venv/bin/activate
$ pip install -r requirements-dev.txt
$ pip install -e .
```

## Run tests
```
$ pytest openprocurement/bridge/rbot/tests/ --cov=openprocurement/bridge/rbot
```

## How to use

```bash
$ databrige configuration.yaml
```