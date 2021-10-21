import React from 'react';
import './Table.css';

import { useTable, useSortBy, usePagination} from 'react-table'

const fs = window.require('fs');
const path = window.require('path');
const {clipboard} = window.require('electron');
const Plotly = window.require('plotly.js-dist');

function percentRank(arr, v) {
  // https://gist.github.com/IceCreamYou/6ffa1b18c4c8f6aeaad2
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
  // Use the state and functions returned from useTable to build your UI
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    prepareRow,
    page, // Instead of using 'rows', we'll use page,
    // which has only the rows for the active page

    // The rest of these things are super handy, too ;)
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

  // Render the UI for your table
  return (
    <>
      <table className="table table-striped" {...getTableProps()}>
        <thead>
          {headerGroups.map(headerGroup => (
            <tr className="d-flex" {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <th {...column.getHeaderProps({...column.getSortByToggleProps(),...{className: column.headerClassName}})}>
                {column.render('Header')}
                {/* Add a sort direction indicator */}
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
      {/* 
        Pagination can be built however you'd like. 
        This is just a very basic UI implementation:
      */}
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
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    this.props.loadAggData();
  }

  render() {
    const columns = [{
      Header: "Rank",
      accessor: "rank",
      className: "rankCell",
      headerClassName: "rankHeader",
      sortType: "number"
    }]
    if (this.props.configData != null) {
      for (let methodName of Object.keys(this.props.configData["outlier_detection"])) {
        columns.push({
          Header: methodName,
          className: "imageCell",
          headerClassName: "imageHeader",
          Cell: (row) => {
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

    let datapass = null;
    if (this.props.data === null) {
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
  constructor(props) {
    super(props);
    this.switchMethod = this.switchMethod.bind(this);
    this.updateWrapper = this.updateWrapper.bind(this);

    this.state = {
      methods: [],
      currMethod: null,
      distCache: []
    };
  }

  componentDidMount() {
    if (this.props.configData != null) {
      this.props.loadData(this.props.configData["outlier_detection"], Object.keys(this.props.configData["outlier_detection"])[0]);
      this.setState({
        methods: Object.keys(this.props.configData["outlier_detection"]),
        currMethod: Object.keys(this.props.configData["outlier_detection"])[0]
      });
    }
  }

  componentDidUpdate() {
    // Feature vector dataloader requires plotly plots
    if (this.props.dataLoader === "featurevector") {

      // get dimension of each feature
      var featLength = this.props.featNames != null ? this.props.featNames.length : 0;
      var numRows = this.props.data != null ? this.props.data.length : 0;
      // distribution cache
      var featDistCache = {};
      // traces to plot
      // for each data row...
      for (let i = 0; i < numRows; i=i+1) {
        // assuming current graph is shown
        if (!!document.getElementById(i.toString()+'table')) {
          // bars to show
          var traces = [];
          // for each feature
          for (let j = 0; j < featLength; j=j+1) {
            if (!(j in featDistCache)) {
              let currDist = this.props.data.map(row => {
                return row["feature"][j];
              })
              featDistCache[j] = currDist;
            }

            // x_labels.push(this.props.featNames[j]);
            // y_values.push(this.props.dataArray[(i*featLength)+j]);
            var percentile = (percentRank(featDistCache[j].sort(), this.props.data[i]["feature"][j]) * 100).toFixed(0)
            // y_texts.push(this.props.dataArray[(i*featLength)+j].toFixed(1).toString() + "@" + percentile.toString() + "th");
            
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

          var layout = {
            showlegend: false,
            width: 80 * featLength,
            dragmode: 'pan',
            title: {
              text: this.props.data[i]["fileName"]
            }
          };
          Plotly.react(i.toString()+"table", traces, layout);
        }
      }
    }
  }

  switchMethod(e) {
    this.props.loadData(this.props.configData["outlier_detection"], e.target.value);
    this.setState({currMethod: e.target.value});
  }

  updateWrapper() {
    this.forceUpdate();
  }

  render() {
    var columns = []
    if (this.props.dataLoader === "image") {
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
    } else if (this.props.dataLoader === "featurevector") {
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
