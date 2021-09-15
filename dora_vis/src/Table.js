import React from 'react';
import './Table.css';

import { useTable, useSortBy, usePagination} from 'react-table'

const fs = window.require('fs');
const path = window.require('path');


function Table({ columns, data }) {
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
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => gotoPage(0)} disabled={!canPreviousPage}>
          {'<<'}
        </button>{' '}
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => previousPage()} disabled={!canPreviousPage}>
          {'<'}
        </button>{' '}
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => nextPage()} disabled={!canNextPage}>
          {'>'}
        </button>{' '}
        <button type="button" className="btn btn-outline-dark btn-sm" onClick={() => gotoPage(pageCount - 1)} disabled={!canNextPage}>
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
          {[10, 20, 30, 40, 50].map(pageSize => (
            <option key={pageSize} value={pageSize}>
              Show {pageSize}
            </option>
          ))}
        </select>
      </div>
    </>
  )
}

class DataTable extends React.Component {
  constructor(props) {
    super(props);
    this.switchMethod = this.switchMethod.bind(this);

    this.state = {
      methods: [],
      currMethod: null
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

  switchMethod(e) {
    this.props.loadData(this.props.configData["outlier_detection"], e.target.value);
    this.setState({currMethod: e.target.value});
  }

  render() {
    const columns = [
      {
        Header: "Rank",
        accessor: "rank",
        className: "rankCell",
        headerClassName: "rankHeader"
      },
      {
        Header: "ID",
        accessor: "id",
        className: "idCell",
        headerClassName: "idHeader"
      },
      {
        Header: "Image",
        Cell: (row) => {
          return (
          <div>
            <a className="imageLink" onClick={() => {navigator.clipboard.writeText(row.row.original.fileName);alert(row.row.original.fileName+ " copied to clipboard.");}}>
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
        headerClassName: "scoreHeader"
      }
    ];

    let datapass = null;
    if (this.props.data == null) {
      datapass = <h1> No DORA configuration loaded </h1>;
    } else {
      datapass = 
      <>
      <div className="col-md-4 methodSelect">
        <label for="methodSel">Results from method:</label>
        <select className="form-select form-select-lg" id="methodSel" onChange={this.switchMethod}>
          {this.state["methods"].map((method) => <option value={method}>{method}</option>)}
        </select>
      </div>
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

export default DataTable;