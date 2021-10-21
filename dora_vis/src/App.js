import React from 'react';
import './App.css';
import { DataTable, AggTable } from './Table';

const parse = window.require('csv-parse');
const yaml = window.require('js-yaml');
const fs = window.require('fs');
const path = window.require('path');
const hdf5 = window.require('jsfive');

// All supported data loaders
// image - imageset, data is directory of image files
// featurevector - h5 export of pandas dataframe
const DATALOADERS = ["image", "featurevector", "time series"];
// Dataloaders that require a directory data root
const DIRLOADERS = ["image"];


class NavBar extends React.Component {
  constructor(props) {
    super(props);

    this.handleNavClick = this.handleNavClick.bind(this);
  }

  handleNavClick(e) {
    e.preventDefault();
    switch(e.target.innerText) {
      case "Configure":
        this.props.changeView("loadConfig");
        break;
      case "Aggregate View":
        this.props.changeView("aggTable");
        break;
      case "Table View":
        this.props.changeView("dataTable");
        break;
      default:
        break;
    }
  }

  render() {
    let configureActive = "";
    let aggregateActive = "";
    let tableActive = "";
    if (this.props.currView === "loadConfig" || this.props.currView === "parseConfig") {
      configureActive = "active";
      aggregateActive = tableActive = "";
    } else if (this.props.currView === "aggTable") {
      aggregateActive = "active";
      configureActive = tableActive = "";
    } else if (this.props.currView === "dataTable") {
      tableActive = "active";
      configureActive = aggregateActive = "";
    } else {
      configureActive = aggregateActive = tableActive = "";
    }
    return(
      <nav className="navbar navbar-expand-lg navbar-light bg-light">
        <div className="container-fluid">
          <span className="navbar-brand mb-0 h1">DORA Visualizer</span>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav mr-auto">
              <li className="nav-item">
                <a className={"nav-link " + configureActive} href="#" onClick={this.handleNavClick}>Configure</a>
              </li>
              <li className="nav-item">
                <a className={"nav-link " + aggregateActive} href="#" onClick={this.handleNavClick}>Aggregate View</a>
              </li>
              <li className="nav-item">
                <a className={"nav-link " + tableActive} href="#" onClick={this.handleNavClick}>Table View</a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    );
  }
}

class ConfigLoader extends React.Component {
  constructor(props) {
    super(props);
    this.handleConfigPathChange = this.handleConfigPathChange.bind(this);
    this.handleConfigPathSubmit = this.handleConfigPathSubmit.bind(this);

    this.state = {configFile: "",
                  configPath: ""};
  }

  handleConfigPathChange(e) {
    /* Handle config file input field change */
    e.preventDefault();
    this.setState({
      configPath: e.target.files[0].path,
      configFile: e.target.value
    });
  }

  handleConfigPathSubmit(e) {
    /* Handle submission of file input field */
    e.preventDefault();
    this.props.loadConfig(this.state["configPath"]);
  }

  render() {
    return(
      <div className="container-fluid">
        <h1>Load DORA Config</h1>
        <form>
          <div className="col-md-6">
            <div className="form-group">
              <label htmlFor="configPath">Specify path to the DORA Config</label>
              <input type="file" className="form-control" id="configPath" onChange={this.handleConfigPathChange} value={this.state["configFile"]} required />
              <button type="submit" className="btn btn-primary" onClick={this.handleConfigPathSubmit}>Submit</button>
            </div>
          </div>
        </form>
      </div>
    );
  }
}

class ConfigParser extends React.Component {
  constructor(props) {
    super(props);

    this.checkDataRoot = this.checkDataRoot.bind(this);
    this.checkOutDir = this.checkOutDir.bind(this);
    this.handleDataRootChange = this.handleDataRootChange.bind(this);
    this.handleDataRootSubmit = this.handleDataRootSubmit.bind(this);
    this.handleOutDirChange = this.handleOutDirChange.bind(this);
    this.handleOutDirSubmit = this.handleOutDirSubmit.bind(this);
    this.handleConfigSubmit = this.handleConfigSubmit.bind(this);

    this.state = {
      dataLoader: this.props.configData["data_loader"]["name"].trim().toLowerCase(),
      dataRoot: "",
      dataRootPath: this.props.configData["data_to_score"],
      outDir: "",
      outDirPath: this.props.configData["out_dir"],
      validDataLoader: DATALOADERS.includes(this.props.configData["data_loader"]["name"].trim().toLowerCase()),
      validDataRoot: false,
      validOutDir: false
    };
  }

  componentDidMount() {
    /* Verify directories in config */
    this.checkDataRoot();
    this.checkOutDir();
  }
  
  checkDataRoot() {
    /* Verify that the submitted data root directory exists */
    fs.access(this.state["dataRootPath"], error => {
      if (error) {
        this.setState({validDataRoot: false});
      } else {
        this.setState({validDataRoot: true});
      }
    });
  }

  checkOutDir() {
    /* Verify that the submitted output directory exists */
    fs.access(this.state["outDirPath"], error => {
      if (error) {
        this.setState({validOutDir: false});
      } else {
        this.setState({validOutDir: true});
      }
    });
  }

  handleDataRootChange(e) {
    /* Handle data root input change */
    if (DIRLOADERS.includes(this.state["dataLoader"])) {
      this.setState({
        dataRoot: e.target.value,
        dataRootPath: path.dirname(e.target.files[0].path)
      });
    } else {
      this.setState({
        dataRoot: e.target.value,
        dataRootPath: e.target.files[0].path
      });
    }
  }

  handleDataRootSubmit(e) {
    /* Handle data root submission
    Verify that the submitted data root directory exists */
    e.preventDefault();
    this.checkDataRoot();
  }

  handleOutDirChange(e) {
    /* Handle output directory input change */
    this.setState({
      outDir: e.target.value,
      outDirPath: e.target.files != null ? path.dirname(e.target.files[0].path) : null
    });
  }

  handleOutDirSubmit(e) {
    /* Handle output directory submission
    Verify that the submitted output directory exists */
    e.preventDefault();
    this.checkOutDir();
  }

  handleConfigSubmit(e) {
    e.preventDefault()
    this.props.setConfig(
      this.state["dataLoader"],
      this.state["dataRootPath"],
      this.state['outDirPath']
    );
  }
  
  render() {
    // Set data loader output
    var componentDataLoader = null;
    if (this.state["validDataLoader"]) {
      componentDataLoader = <label>{this.state["dataLoader"]} is a supported data loader.</label>;
    } else {
      componentDataLoader = <label>Fatal: {this.state["dataLoader"]} is not a supported data loader.</label>;
    }

    // Set data root output/input
    var componentDataRoot = null;
    if (this.state["validDataRoot"]) {
      componentDataRoot = <label>{this.state["dataRootPath"]} is a valid data root path.</label>;
    } else if (DIRLOADERS.includes(this.state["dataLoader"])) {
      // Only the image dataloader requires a directory data root path.
      componentDataRoot = 
      <div className="col-md-6">
      <div className="form-group">
        <label htmlFor="dataRootField">Can't locate {this.props.configData["data_to_score"]}, Specify the root directory of input data</label>
        <input type="file" className="form-control" id="dataRootField" onChange={this.handleDataRootChange} value={this.state["dataRoot"]} required directory="" webkitdirectory=""/>
        <button type="submit" className="btn btn-primary" onClick={this.handleDataRootSubmit}>Submit</button>
      </div>
      </div>;
    } else {
      // Other dataloaders require a single file.
      componentDataRoot = 
      <div className="col-md-6">
      <div className="form-group">
        <label htmlFor="dataRootField">Can't locate {this.props.configData["data_to_score"]}, Specify the filepath of input data</label>
        <input type="file" className="form-control" id="dataRootField" onChange={this.handleDataRootChange} value={this.state["dataRoot"]} required/>
        <button type="submit" className="btn btn-primary" onClick={this.handleDataRootSubmit}>Submit</button>
      </div>
      </div>; 
    }

    // Set output directory output/input
    var componentOutDir = null;
    if (this.state["validOutDir"]) {
      componentOutDir = <label>{this.state["outDirPath"]} is a valid output directory.</label>;
    } else {
      componentOutDir = 
      <div className="col-md-6">
      <div className="form-group">
        <label htmlFor="outDirField">Can't locate {this.props.configData["out_dir"]}, Specify the root directory of DORA results.</label>
        <input type="file" className="form-control" id="outDirField" onChange={this.handleOutDirChange} value={this.state["outDir"]} required directory="" webkitdirectory=""/>
        <button type="submit" className="btn btn-primary" onClick={this.handleOutDirSubmit}>Submit</button>
      </div>
      </div>;
    }

    var componentConfigButton = null;
    if (this.state["validDataLoader"] && this.state["validDataRoot"] && this.state["validOutDir"]) {
      componentConfigButton = <button type="submit" className="btn btn-primary" onClick={this.handleConfigSubmit}>Continue</button>;
    } else {
      componentConfigButton = <button type="submit" className="btn btn-primary" disabled>Resolve Issues</button>;
    }

    return(
      <div className="container-fluid">
        <h1>Parse DORA Config</h1>
        <form>
          <h2> Dataloader Check </h2>
          {componentDataLoader}
          <br/>
          <h2> Data Root Check </h2>
          {componentDataRoot}
          <br/>
          <h2> Results Dir Check </h2>
          {componentOutDir}
          <br/>
          {componentConfigButton}
        </form>
      </div>
    );
  }
}

class App extends React.Component {
  constructor(props) {
    super(props);

    this.loadConfig = this.loadConfig.bind(this);
    this.setConfig = this.setConfig.bind(this);
    this.loadData = this.loadData.bind(this);
    this.loadAggData = this.loadAggData.bind(this);
    this.changeView = this.changeView.bind(this);

    this.state = {
      viewset: ["loadConfig", "parseConfig", "dataTable", "aggTable"],
      view: "loadConfig",
      configData: null,
      dataLoader: null,
      dataRoot: null,
      outDir: null,
      data: null,
      aggData: null
    };
  }

  loadConfig(configPath) {
    try {
      const doc = yaml.load(fs.readFileSync(configPath, "utf8"));
      this.setState({
        configData: doc
      });
      this.changeView("parseConfig");
    } catch (e) {
      console.log(e);
    }
  }

  setConfig(setDataLoader, setDataRoot, setOutDir) {
    this.setState({
      dataLoader: setDataLoader,
      dataRoot: setDataRoot,
      outDir: setOutDir
    })
    this.changeView("dataTable");
  }

  changeView(view) {
    if (this.state["viewset"].includes(view)) {
      this.setState({
        view: view
      });
      return(0);
    } else {
      return(1);
    }
  }

  loadData(methodObject, methodName) {
    const methodOptions = [methodName];
    if (methodObject[methodName] != null) {
      for (const [key, value] of Object.entries(methodObject[methodName])) {
        methodOptions.push(key + '=' + value);
      }
    }

    const methodDirName = methodOptions.join('-');
    const methodCSVName = "selections-" + methodName + ".csv";
    const methodCSVPath = path.join(this.state["outDir"], methodDirName, methodCSVName);
    console.log(methodCSVPath);
    if (this.state["dataLoader"] === "image") {
      let data = [];
      fs.createReadStream(methodCSVPath)
        .pipe(parse({delimiter: ', '}))
        .on('data', csvrow => {
          data.push(csvrow);
        })
        .on('end', () => {
          const dataObj = data.map(row => {
            return {
              rank: parseInt(row[0]),
              id: parseInt(row[1]),
              fileName: row[2],
              imageData: fs.readFileSync(path.join(this.state["dataRoot"], row[2])).toString('base64'),
              score: parseFloat(row[3])
            };
          });
          this.setState({data: dataObj});
        });
    } else if (this.state["dataLoader"] === "featurevector") {
      let data = [];
      // jsfive
      var rawData = fs.readFileSync(this.state["dataRoot"]);
      var h5File = new hdf5.File(rawData.buffer);

      fs.createReadStream(methodCSVPath)
        .pipe(parse({delimiter: ', '}))
        .on('data', csvrow => {
          data.push(csvrow);
        })
        .on('end', () => {
          const dataObj = data.map(row => {
            let elementId = parseInt(row[1]);
            let flatArray = h5File.get("data/block0_values").value != null ? h5File.get("data/block0_values").value : [];
            let featDim = h5File.get("data/axis0").value != null ? h5File.get("data/axis0").value.length : 0;
            
            return {
              rank: parseInt(row[0]),
              id: elementId,
              fileName: row[2],
              feature: flatArray.slice(elementId * featDim, (elementId + 1) * featDim),
              score: parseFloat(row[3])
            };
          });
          this.setState({
            featNames: h5File.get("data/axis0").value,
            data: dataObj.sort((a,b) => a.rank < b.rank ? -1 : 1)
          });
        });
    } else if (this.state["dataLoader"] === "time series") {
      let dataArray = [];
      let data = [];

      fs.createReadStream(this.state["dataRoot"])
        .pipe(parse({delimiter: ','}))
        .on('data', datarow => {
          dataArray.push(datarow.slice(1));
        })
        .on('end', () => {
          fs.createReadStream(methodCSVPath)
            .pipe(parse({delimiter: ', '}))
            .on('data', csvrow => {
              data.push(csvrow);
            })
            .on('end', () => {
              const dataObj = data.map(row => {
                return {
                  rank: parseInt(row[0]),
                  id: parseInt(row[1]),
                  fileName: row[2],
                  feature: dataArray[parseInt(row[1])].map(num => Number(num)),
                  score: parseFloat(row[3])
                };
              });
              console.log(dataArray);
              this.setState({
                featNames: [...Array(dataArray[0].length).keys()],
                data: dataObj
              });
            });
        });

    }
  }

  loadAggData() {
    if (this.state["dataLoader"] !== "image") {
      this.setState({aggData: null});
      return;
    }

    // Get list of available methods
    const methods = this.state["configData"] != null ? Object.keys(this.state["configData"]["outlier_detection"]) : [];
    let dataList = [];

    // For each method available
    for (let methodName of methods) {
      const currData = [];
      // Define and find CSV
      const methodOptions = [methodName];
      if (this.state["configData"]["outlier_detection"][methodName] != null) {
        for (const [key, value] of Object.entries(this.state["configData"]["outlier_detection"][methodName])) {
          methodOptions.push(key + '=' + value);
        }
      }
      const methodDirName = methodOptions.join('-');
      const methodCSVName = "selections-" + methodName + ".csv";
      const methodCSVPath = path.join(this.state["outDir"], methodDirName, methodCSVName);
      
      // Read imagepaths from CSV
      fs.createReadStream(methodCSVPath)
        .pipe(parse({delimiter:', '}))
        .on('data', csvrow => {
          currData.push(csvrow)
        })
        .on('end', () => {
          if (dataList.length === 0) {
            for (let row of currData) {
              var currRow = {};
              currRow["rank"] = parseInt(row[0]);
              currRow[methodName] = fs.readFileSync(path.join(this.state["dataRoot"], row[2])).toString('base64');
              currRow[methodName+"Name"] = row[2];
              dataList.push(currRow);
            }
          } else {
            for (let [ind, row] of currData.entries()) {
              var currRow = {};
              currRow["rank"] = parseInt(row[0]);
              currRow[methodName] = fs.readFileSync(path.join(this.state["dataRoot"], row[2])).toString('base64');
              currRow[methodName+"Name"] = row[2];
              dataList[ind] = {...dataList[ind], ...currRow};
            }
          }
          this.setState({aggData: dataList});
        });
    }
  }

  render() {
    var view = null;
    switch(this.state["view"]) {
      case "loadConfig":
        view = <ConfigLoader loadConfig={this.loadConfig} />;
        break;
      case "parseConfig":
        view = <ConfigParser configData={this.state["configData"]} setConfig={this.setConfig}/>;
        break;
      case "dataTable":
        view = <DataTable 
                  configData={this.state["configData"]}
                  loadData={this.loadData} data={this.state["data"]}
                  dataLoader={this.state["dataLoader"]}
                  dataArray={this.state["dataArray"]}
                  featNames={this.state["featNames"]}
               />;
        break;
      case "aggTable":
        view = <AggTable configData={this.state["configData"]} loadAggData={this.loadAggData} data={this.state["aggData"]}/>;
        break;
      default:
        view = <h1> This view has not been implemented.</h1>;
    }

    return(
      <div> 
        <NavBar changeView={this.changeView} currView={this.state["view"]}/>
        {view}
      </div>
    );
  }
}

export default App;
