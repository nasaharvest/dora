import React from 'react';
//import ReactDOM from 'react-dom';
import './App.css';
import { DataTable, AggTable } from './Table';

const parse = window.require('csv-parse')
const yaml = window.require('js-yaml');
const fs = window.require('fs');
const path = window.require('path');

const DATALOADERS = ["image"];


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
      case "Gallery View":
        this.props.changeView("gallery");
        break;
      default:
        break;
    }
  }

  render() {
    let configureActive = "";
    let aggregateActive = "";
    let tableActive = "";
    let galleryActive = "";
    if (this.props.currView === "loadConfig" || this.props.currView === "parseConfig") {
      configureActive = "active";
      aggregateActive = tableActive = galleryActive = "";
    } else if (this.props.currView === "aggTable") {
      aggregateActive = "active";
      configureActive = tableActive = galleryActive = "";
    } else if (this.props.currView === "dataTable") {
      tableActive = "active";
      configureActive = aggregateActive = galleryActive = "";
    } else if (this.props.currView === "gallery"){
      galleryActive = "active";
      configureActive = aggregateActive = tableActive = "";
    } else {
      configureActive = aggregateActive = tableActive = galleryActive = "";
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
              <li className="nav-time">
                <a className={"nav-link " + galleryActive} href="#" onClick={this.handleNavClick}>Gallery View</a>
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
      dataLoader: this.props.configData["data_loader"]["name"],
      dataRoot: "",
      dataRootPath: this.props.configData["data_to_score"],
      outDir: "",
      outDirPath: this.props.configData["out_dir"],
      validDataLoader: DATALOADERS.includes(this.props.configData["data_loader"]["name"].trim()),
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
    this.setState({
      dataRoot: e.target.value,
      dataRootPath: path.dirname(e.target.files[0].path)
    });
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
      outDirPath: path.dirname(e.target.files[0].path)
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
      this.state['outDirPath']);
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
      componentDataRoot = <label>{this.state["dataRootPath"]} is a valid data root directory.</label>;
    } else {
      componentDataRoot = 
      <div className="col-md-6">
      <div className="form-group">
        <label htmlFor="dataRootField">Can't locate {this.props.configData["data_to_score"]}, Specify the root directory of input data</label>
        <input type="file" className="form-control" id="dataRootField" onChange={this.handleDataRootChange} value={this.state["dataRoot"]} required directory="" webkitdirectory=""/>
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
          {componentDataLoader}
          {componentDataRoot}
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

  }

  loadAggData() {
    // Get list of available methods
    const methods = Object.keys(this.state["configData"]["outlier_detection"]);
    let data = [];

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
          if (data.length == 0) {
            for (let row of currData) {
              let currRow = {}
              currRow["rank"] = parseInt(row[0]);
              currRow[methodName] = fs.readFileSync(path.join(this.state["dataRoot"], row[2])).toString('base64');
              currRow[methodName+"Name"] = row[2];
              data.push(currRow);
            }
          } else {
            for (let [ind, row] of currData.entries()) {
              let currRow = {}
              currRow["rank"] = parseInt(row[0]);
              currRow[methodName] = fs.readFileSync(path.join(this.state["dataRoot"], row[2])).toString('base64');
              currRow[methodName+"Name"] = row[2];
              data[ind] = {...data[ind], ...currRow};
            }
          }
          this.setState({aggData: data});
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
        view = <DataTable configData={this.state["configData"]} loadData={this.loadData} data={this.state["data"]}/>;
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
