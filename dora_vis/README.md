# DORA Visualizer

This is a visualization tool for DORA results. 

## Usage Instructions

**OS X:** Install from `dora_vis/release/dora-vis-0.1.0.dmg`

**Windows:** A windows binary is not yet available.

## Development Instructions

### Dependencies

* `node` 14.17.6 LTS
  * Install from https://nodejs.org/en/
* `yarn` ~=1.22.11
  * `npm install yarn`

### Launching the development server
1. `cd dora_vis`
2. `yarn`
3. `yarn electron-dev`

### Building and packaging
1. Delete `node_modules`
2. `yarn install --production`
3. `yarn build`
4. `yarn dist`