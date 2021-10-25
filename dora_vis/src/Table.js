import React from 'react';
import './Table.css';

import { useTable, useSortBy, usePagination} from 'react-table'

const {clipboard} = window.require('electron');
const Plotly = window.require('plotly.js-dist');

function percentRank(arr, v) {
  /* Get the percentile of a value given a sorted array
     From https://gist.github.com/IceCreamYou/6ffa1b18c4c8f6aeaad2 */
  if (typeof v !== 'number') throw new TypeError('v must be a number');
  for (var i = 0, l = arr.length; i < l; i++) {
      if (v <= arr[i]) {
          while (i < l && v === arr[i]) i++;
          if (i === 0) return 0;
          if (v !== arr[i-1]) {
              i += (v - arr[i-1]) / (arr[i] - arr[i-1]);
          }
          return i / l;
      }
  }
  return 1;
}

function Table({ columns, data, forceUpdate = () => ({}) }) {
  /* Table for showing results from a single method
     ReactTable template, taken from the documentation example */
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    prepareRow,
    page,

    canPreviousPage,
    canNextPage,
    pageOptions,
    pageCount,
    gotoPage,
    nextPage,
    previousPage,
    setPageSize,
    state: { pageIndex, pageSize, sortBy },
  } = useTable(
    {
      columns,
      data,
      initialState: { pageIndex: 0 },
    },
    useSortBy,
    usePagination
  )

  // Render the UI for the table
  return (
    <>
      <table className="table table-striped" {...getTableProps()}>
        <thead>
          {headerGroups.map(headerGroup => (
            <tr className="d-flex" {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <th {...column.getHeaderProps({...column.getSortByToggleProps(),...{className: column.headerClassName}})}>
                {column.render('Header')}
                <span>
                  {column.canSort
                    ? column.isSorted
                      ? column.isSortedDesc
                        ? ' 🔽'
                        : ' 🔼'
                      : ' ⏺️'
                    : '  '}
                </span>
              </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {page.map((row, i) => {
            prepareRow(row)
            return (
              <tr className="d-flex" {...row.getRowProps()}>
                {row.cells.map(cell => {
                  return <td {...cell.getCellProps({className: cell.column.className})}>{cell.render('Cell')}</td>
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
      <div className="pagination">
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => {gotoPage(0); forceUpdate();}} disabled={!canPreviousPage}>
          {'<<'}
        </button>{' '}
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => {previousPage(); forceUpdate();}} disabled={!canPreviousPage}>
          {'<'}
        </button>{' '}
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => {nextPage(); forceUpdate();}} disabled={!canNextPage}>
          {'>'}
        </button>{' '}
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => {gotoPage(pageCount - 1); forceUpdate();}} disabled={!canNextPage}>
          {'>>'}
        </button>{' '}
        <span>
          Page{' '}
          <strong>
            {pageIndex + 1} of {pageOptions.length}
          </strong>{' '}
        </span>
        <span>
          | Go to page:{' '}
          <input
            type="number"
            defaultValue={pageIndex + 1}
            onChange={e => {
              const page = e.target.value ? Number(e.target.value) - 1 : 0
              gotoPage(page)
            }}
            style={{ width: '100px' }}
          />
        </span>{' '}
        <select
          value={pageSize}
          onChange={e => {
            setPageSize(Number(e.target.value))
          }}
        >
          {[5, 10, 20, 50, 100].map(pageSize => (
            <option key={pageSize} value={pageSize}>
              Show {pageSize}
            </option>
          ))}
        </select>
      </div>
    </>
  )
}

class AggTable extends React.Component {
  /* Table component for showing results from all methods of image dataloader */
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    // Load aggregate data once component is mounted
    this.props.loadAggData();
  }

  render() {
    // Define columns of the table
    const columns = [{
      Header: "Rank",
      accessor: "rank",
      className: "rankCell",
      headerClassName: "rankHeader",
      sortType: "number"
    }]
    if (this.props.configData != null) {
      for (let methodName of Object.keys(this.props.configData["outlier_detection"])) {
        // Add a column for each method
        columns.push({
          Header: methodName,
          className: "imageCell",
          headerClassName: "imageHeader",
          Cell: (row) => {
            // custom html for viewing an image encoded in base64, and click-to-copy
            return(
            <div>
              <a className="imageLink" onClick={() => {clipboard.writeText(row.row.original[methodName+"Name"]);alert(row.row.original[methodName+"Name"]+ " copied to clipboard.");}}>
                <img src={"data:image/png;base64,"+row.row.original[methodName]} title={row.row.original[methodName+"Name"]}/>
              </a>
            </div>
            );
          }
        });
      }
    }

    // Display the table
    let datapass = null;
    if (this.props.data === null) {
      // Message if table has not loaded or there is an error
      datapass =
      <>
        <h1> Loading Aggregate Table... </h1>
        <br/>
        <p> If stuck, it may be due to: </p>
        <ul>
          <li><b>A dataloader that is not "image"</b></li>
          <li>No configuration being loaded</li>
          <li>Mismatch between the configuration, data, and results</li>
          <li>A very large data set</li>
        </ul>
      </>;
    } else {
      // Show the table once data is not null
      datapass = <>
        <h1>Aggregate Results</h1>
        <Table columns={columns} data={this.props.data}/>
      </>;
    }

    return (
    <div className="container">
      {datapass}
      <br/>
    </div>
    );
  }
}

class DataTable extends React.Component {
  /* Table component for showing results from a single method */
  constructor(props) {
    super(props);

    // change which method's results are shown
    this.switchMethod = this.switchMethod.bind(this);
    // force the component to update, redrawing plotly plots
    this.updateWrapper = this.updateWrapper.bind(this);

    /* Component States
    methods:      Methods for which results are available
    currMethod:   Current method displayed in table
    */
    this.state = {
      methods: [],
      currMethod: null
    };
  }

  componentDidMount() {
    // Initialize states and load data for first method
    if (this.props.configData != null) {
      this.props.loadData(this.props.configData["outlier_detection"], Object.keys(this.props.configData["outlier_detection"])[0]);
      this.setState({
        methods: Object.keys(this.props.configData["outlier_detection"]),
        currMethod: Object.keys(this.props.configData["outlier_detection"])[0]
      });
    }
  }

  componentDidUpdate() {
    /* Refresh plots if dataloader is featurevector or time series */
    if (this.props.dataLoader === "featurevector" || this.props.dataLoader === "time series") {

      // get dimension of each feature
      var featLength = this.props.featNames != null ? this.props.featNames.length : 0;
      // get number of rows in the data
      var numRows = this.props.data != null ? this.props.data.length : 0;
      
      for (let i = 0; i < numRows; i=i+1) {
        // only plot if it is currently visible
        if (!!document.getElementById(i.toString()+'table')) {
          var traces = [];
          var featDistCache = {};
          // build feature distribution cache if it doesn't exist
          for (let j = 0; j < featLength; j=j+1) {
            if (!(j in featDistCache)) {
              let currDist = this.props.data.map(row => {
                return row["feature"][j];
              })
              featDistCache[j] = currDist;
            }
            console.log(this.state['distCache'])

            // calculate percentile of current data point w.r.t. full feature distribution
            var percentile = (percentRank(featDistCache[j].sort(), this.props.data[i]["feature"][j]) * 100).toFixed(0)
            
            // box plot
            traces.push({
              name: this.props.featNames[j],
              y: featDistCache[j],
              type: 'box',
              boxpoints: false,
              line: {
                color: 'black',
                width: 1
              },
              fillcolor: 'white'
            });

            // marker for current data point
            traces.push({
              name: this.props.featNames[j],
              x: [this.props.featNames[j]],
              y: [this.props.data[i]["feature"][j]],
              text: [percentile.toString() + "th"],
              mode: 'markers',
              marker: {
                autocolorscale: false,
                color: [percentile],
                colorscale: 'RdBu',
                cmin: 0,
                cmax: 100
              }
            });
          }

          // plotly layout parameters
          var layout = {
            showlegend: false,
            width: 80 * featLength,
            dragmode: 'pan',
            title: {
              text: this.props.data[i]["fileName"]
            }
          };
          
          // plotly plot
          Plotly.react(i.toString()+"table", traces, layout);
        }
      }
    }
  }

  switchMethod(e) {
    /* Switch to results from a different method */
    this.props.loadData(this.props.configData["outlier_detection"], e.target.value);
    this.setState({currMethod: e.target.value});
  }

  updateWrapper() {
    this.forceUpdate();
  }

  render() {
    var columns = []
    if (this.props.dataLoader === "image") {
      // columns for an image dataloader
      columns = [
        {
          Header: "Rank",
          accessor: "rank",
          className: "rankCell",
          headerClassName: "rankHeader",
          sortType: "number"
        },
        {
          Header: "ID",
          accessor: "id",
          className: "idCell",
          headerClassName: "idHeader",
          sortType: "number"
        },
        {
          Header: "Image",
          Cell: (row) => {
            return (
            <div>
              <a className="imageLink" onClick={() => {clipboard.writeText(row.row.original.fileName);alert(row.row.original.fileName+ " copied to clipboard.");}}>
                <img src={"data:image/png;base64,"+row.row.original.imageData} title={row.row.original.fileName}/>
              </a>
            </div>
            );
          },
          id: "image",
          className: "imageCell",
          headerClassName: "imageHeader"
        },
        {
          Header: "Score",
          Cell: (row) => {
            return (
              <p>
                {row.row.original.score.toFixed(4)}
              </p>
            );
          },
          accessor: "score",
          className: "scoreCell",
          headerClassName: "scoreHeader",
          sortType: "number"
        }
      ];
    } else if (this.props.dataLoader === "featurevector" || this.props.dataLoader === "time series") {
      // columns for a 1D vector dataloader
      columns = [
        {
          Header: "Rank",
          accessor: "rank",
          className: "rankCell",
          headerClassName: "rankHeader",
          sortType: "number",
          disableSortBy: true
        },
        {
          Header: "ID",
          accessor: "id",
          className: "idCell",
          headerClassName: "idHeader",
          sortType: "number",
          disableSortBy: true
        },
        {
          Header: "Features",
          Cell: (row) => {
            return (<div id={row.row.original.rank+"table"}></div>);
          },
          id: "features",
          className: "featureCell",
          headerClassName: "featureHeader",
          disableSortBy: true
        },
        {
          Header: "Score",
          Cell: (row) => {
            return (
              <p>
                {row.row.original.score.toFixed(4)}
              </p>
            );
          },
          accessor: "score",
          className: "scoreCell",
          headerClassName: "scoreHeader",
          sortType: "number",
          disableSortBy: true
        }
      ];
    }

    let datapass = null;
    if (this.props.data == null) {
      // message shown if table is loading or there is an error
      datapass =
      <>
        <h1> Loading Data Table... </h1>
        <br/>
        <p> If stuck, it may be due to: </p>
        <ul>
          <li>No configuration being loaded</li>
          <li>Mismatch between the configuration, data, and results</li>
          <li>A very large data set</li>
        </ul>
      </>;
    } else {
      datapass = 
      <>
      <div className="col-md-4 methodSelect">
        <label>Results from method:</label>
        <select className="form-select form-select-lg" id="methodSel" onChange={this.switchMethod}>
          {this.state["methods"].map((method) => <option value={method}>{method}</option>)}
        </select>
      </div>
      <Table columns={columns} data={this.props.data} forceUpdate={this.updateWrapper}/>
      </>;
    }

    return (
    <div className="container">
      {datapass}
      <br/>
    </div>
    );
    
  }
}

export { DataTable, AggTable };
