import React from 'react';
import './App.css';
import { DataTable, AggTable } from './Table';

const parse = window.require('csv-parse');
const yaml = window.require('js-yaml');
const fs = window.require('fs');
const path = window.require('path');
const hdf5 = window.require('jsfive');

/* Define Supported Data Loaders
image: data is directory of image files
featurevector: data is hdf5 export of pandas dataframe
time series: data is a csv file, first column is dropped
*/
const DATALOADERS = ["image", "featurevector", "time series"];
// These dataloaders require a directory path for data
const DIRLOADERS = ["image"];


class NavBar extends React.Component {
  /* Navigation bar component */
  constructor(props) {
    super(props);

    // Handle changing views
    this.handleNavClick = this.handleNavClick.bind(this);
  }

  handleNavClick(e) {
    /* Handle changing views */
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
    // Logic to bold current view
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

    // NavBar JSX
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
  /* Initial configuration loader component */
  constructor(props) {
    super(props);

    // Handle config file input field change
    this.handleConfigPathChange = this.handleConfigPathChange.bind(this);
    // Handle submission of file input field
    this.handleConfigPathSubmit = this.handleConfigPathSubmit.bind(this);
    
    /* Component states
    configFile:   Filename of config
    configPath:   Filepath of config
    */
    this.state = {configFile: "",
                  configPath: ""
    };
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
    /* Configuration loader JSX */
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
  /* Configuration parsing and resolving component */
  constructor(props) {
    super(props);

    // Verify that the data root directory exists
    this.checkDataRoot = this.checkDataRoot.bind(this);
    // Verify that the results directory exists
    this.checkOutDir = this.checkOutDir.bind(this);
    // Handle data root input change
    this.handleDataRootChange = this.handleDataRootChange.bind(this);
    // Handle data root input submission
    this.handleDataRootSubmit = this.handleDataRootSubmit.bind(this);
    // Handle results directory input change
    this.handleOutDirChange = this.handleOutDirChange.bind(this);
    // Handle results directory input submission
    this.handleOutDirSubmit = this.handleOutDirSubmit.bind(this);
    // Handle resolved configuration submission
    this.handleConfigSubmit = this.handleConfigSubmit.bind(this);

    /* Component states
    dataLoader:       specified DORA data loader
    dataRoot:         directory name OR filename of data
    dataRootPath:     filepath OR dirpath of data
    outDir:           name of results directory
    outDirPath:       path of results directory
    validDataLoader:  boolean, whether a dataloader is supported
    validDataRoot:    boolean, whether the current config or input data path exists
    validOutDir:      boolean, whether the current config or input results dir exists
    */
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
    /* Verify that the data root directory exists */
    fs.access(this.state["dataRootPath"], error => {
      if (error) {
        this.setState({validDataRoot: false});
      } else {
        this.setState({validDataRoot: true});
      }
    });
  }

  checkOutDir() {
    /* Verify that the results directory exists */
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
    /* Handle configuration submission */
    e.preventDefault()
    this.props.setConfig(
      this.state["dataLoader"],
      this.state["dataRootPath"],
      this.state['outDirPath']
    );
  }
  
  render() {
    // Show whether the current data loader is supported
    var componentDataLoader = null;
    if (this.state["validDataLoader"]) {
      componentDataLoader = <label>{this.state["dataLoader"]} is a supported data loader.</label>;
    } else {
      componentDataLoader = <label>Fatal: {this.state["dataLoader"]} is not a supported data loader.</label>;
    }

    // Show whether the current datapath is valid
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
      // Other dataloaders require a single file
      componentDataRoot = 
      <div className="col-md-6">
      <div className="form-group">
        <label htmlFor="dataRootField">Can't locate {this.props.configData["data_to_score"]}, Specify the filepath of input data</label>
        <input type="file" className="form-control" id="dataRootField" onChange={this.handleDataRootChange} value={this.state["dataRoot"]} required/>
        <button type="submit" className="btn btn-primary" onClick={this.handleDataRootSubmit}>Submit</button>
      </div>
      </div>; 
    }

    // Show whether the current results dir is valid
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

    // Submit the resolved configuration
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
  /* Main application component */
  constructor(props) {
    super(props);

    // load a configuration file
    this.loadConfig = this.loadConfig.bind(this);
    // set a configuration file
    this.setConfig = this.setConfig.bind(this);
    // load results from a single method for the table
    this.loadData = this.loadData.bind(this);
    // load data for the aggregate table
    this.loadAggData = this.loadAggData.bind(this);
    // change the current view of the application
    this.changeView = this.changeView.bind(this);

    /* Component states
    viewset:      list of available application views
    view:         current view
    configData:   full YAML configuration data
    dataLoader:   specified DORA dataloader
    dataRoot:     path to data file or directory
    outDir:       path to results directory
    data:         data structure to be shown in results table
    aggData:      data structure to be shown in aggregate table
    */
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
    /* Load a configuration file */
    try {
      const doc = yaml.load(fs.readFileSync(configPath, "utf8"));
      this.setState({ configData: doc });
      this.changeView("parseConfig");
    } catch (e) {
      console.log(e);
    }
  }

  setConfig(setDataLoader, setDataRoot, setOutDir) {
    /* Set a configuration file */
    this.setState({
      dataLoader: setDataLoader,
      dataRoot: setDataRoot,
      outDir: setOutDir
    })
    this.changeView("dataTable");
  }

  changeView(view) {
    /* Change the current view of the application */
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
    /* Load results from a single method to be shown in results table */

    // From the list of methods, build paths to result CSVs
    const methodOptions = [methodName];
    // Build "methodName-parameter=value"
    if (methodObject[methodName] != null) {
      for (const [key, value] of Object.entries(methodObject[methodName])) {
        methodOptions.push(key + '=' + value);
      }
    }
    // method results directory name
    const methodDirName = methodOptions.join('-');
    // method CSV file name
    const methodCSVName = "selections-" + methodName + ".csv";
    // method CSV full filepath
    const methodCSVPath = path.join(this.state["outDir"], methodDirName, methodCSVName);

    // Depending on dataloader, fill data
    if (this.state["dataLoader"] === "image") {
      // buffer for results csv
      let data = [];

      // read csv
      fs.createReadStream(methodCSVPath)
        .pipe(parse({delimiter: ', '}))
        .on('data', csvrow => {
          data.push(csvrow);
        })
        .on('end', () => {
          // for each row, build data objects
          // for imageData, image is read and stored as a base64 string
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
    } else if (this.state["dataLoader"] === "featurevector" || this.state["dataLoader"] === "time series") {
      if (this.state["dataRoot"].split('.').pop() === "h5") {
        // buffer for results csv
        let data = [];

        // jsfive data reading for hdf5
        var rawData = fs.readFileSync(this.state["dataRoot"]);
        var h5File = new hdf5.File(rawData.buffer);
        var flatArray = h5File.get("data/block0_values").value != null ? h5File.get("data/block0_values").value : [];
        var featDim = h5File.get("data/axis0").value != null ? h5File.get("data/axis0").value.length : 0;

        // read csv
        fs.createReadStream(methodCSVPath)
          .pipe(parse({delimiter: ', '}))
          .on('data', csvrow => {
            data.push(csvrow);
          })
          .on('end', () => {
            // for each row, slice feature from h5 array
            const dataObj = data.map(row => {
              let elementId = parseInt(row[1]);
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
      } else if (this.state["dataRoot"].split('.').pop() === "csv") {
        // buffer for results csv
        let data = [];
        // buffer for data csv
        let dataArray = [];

        // read data csv
        fs.createReadStream(this.state["dataRoot"])
          .pipe(parse({delimiter: ','}))
          .on('data', datarow => {
            // drop first column, which is row index
            dataArray.push(datarow.slice(1));
          })
          .on('end', () => {
            // read results csv
            fs.createReadStream(methodCSVPath)
              .pipe(parse({delimiter: ', '}))
              .on('data', csvrow => {
                data.push(csvrow);
              })
              .on('end', () => {
                const dataObj = data.map(row => {
                  // for each row, get csv row
                  return {
                    rank: parseInt(row[0]),
                    id: parseInt(row[1]),
                    fileName: row[2],
                    feature: dataArray[parseInt(row[1])].map(num => Number(num)),
                    score: parseFloat(row[3])
                  };
                });
                this.setState({
                  featNames: [...Array(dataArray[0].length).keys()],
                  data: dataObj
                });
              });
          });
      }
    }
  }

  loadAggData() {
    /* Load data from all methods for display in aggregate table */

    if (this.state["dataLoader"] !== "image") {
      // only image dataloader is supported
      this.setState({aggData: null});
      return;
    }

    // Get list of available methods
    const methods = this.state["configData"] != null ? Object.keys(this.state["configData"]["outlier_detection"]) : [];
    let dataList = [];

    // For each method available
    for (let methodName of methods) {
      const currData = [];
      var currRow = {};
      
      // From the list of methods, build paths to result CSVs
      const methodOptions = [methodName];
      if (this.state["configData"]["outlier_detection"][methodName] != null) {
        for (const [key, value] of Object.entries(this.state["configData"]["outlier_detection"][methodName])) {
          methodOptions.push(key + '=' + value);
        }
      }
      // method results directory name
      const methodDirName = methodOptions.join('-');
      // method CSV file name
      const methodCSVName = "selections-" + methodName + ".csv";
      // method CSV full filepath
      const methodCSVPath = path.join(this.state["outDir"], methodDirName, methodCSVName);
      
      // Read imagepaths from CSV
      fs.createReadStream(methodCSVPath)
        .pipe(parse({delimiter:', '}))
        .on('data', csvrow => {
          currData.push(csvrow)
        })
        .on('end', () => {
          if (dataList.length === 0) {
            // if dataList is empty, initialize with first column of methods
            for (let row of currData) {
              currRow = {};
              currRow["rank"] = parseInt(row[0]);
              currRow[methodName] = fs.readFileSync(path.join(this.state["dataRoot"], row[2])).toString('base64');
              currRow[methodName+"Name"] = row[2];
              dataList.push(currRow);
            }
          } else {
            // if dataList is not empty, add column of new method
            for (let [ind, row] of currData.entries()) {
              currRow = {};
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

    // Show different components depending on current view
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
