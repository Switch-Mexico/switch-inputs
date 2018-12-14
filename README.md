<div align="center">
<h1>
  <img src="./static/img/logo-b.png" alt="SWITCH" width="200">
  <h3>A capacity expansion model for the electricity sector.</h4>
  <h4>Input file creation</h4>
  <br>
</h1>

[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](http://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](http://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/as-seen-on-tv.svg)](https://forthebadge.com)

[![GitHub last commit](https://img.shields.io/github/last-commit/google/skia.svg?style=flat-square)](https://github.com/Switch-Mexico/switch-inputs)
</div>

# SWITCH inputs for Mexico

Update: 05/01/2018

Repo for SWITCH-Mexico including code and data

Todo:
- [x] Implement git lfs,
- [x] Verify switch input files creation,
- [x] Clean folders,
- [x] Update switch input creation,
- [ ] Create function that check if folders exists
- [ ] Create sanity check for default inputs 
- [ ] Create fuel cost inputs
- [ ] Update switch folder,
- [ ] Publish runs,
- [ ] Write Readme and documentation for the codes.


Collaborators:
Sergio, Pedro, Hector and others.

## How to use

### Installation

With pip:

```bash
pip install switch-inputs

With pipenv:

```bash
pipenv install switch-inputs
```

### How to run

First we need to download all the default data files:

```bash
inputs init
```

To create the switch inputs and create different scenarios run:

```bash
inputs create
```

The `data/switch\_inputs` will be copy for switch-model


### How to run Renewable Ninja:

Create a file in src/ called secrets.yml with your API\_KEY for using renewable
ninja API.

The file should look like this:

```yaml
API_KEY: "YOUR_API_KEY"
```
