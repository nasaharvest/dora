import React from 'react';
import './App.css';

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
      <table {...getTableProps()}>
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <th {...column.getHeaderProps(column.getSortByToggleProps())}>
                {column.render('Header')}
                {/* Add a sort direction indicator */}
                <span>
                  {column.isSorted
                    ? column.isSortedDesc
                      ? ' 🔽'
                      : ' 🔼'
                    : ''}
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
              <tr {...row.getRowProps()}>
                {row.cells.map(cell => {
                  return <td {...cell.getCellProps()}>{cell.render('Cell')}</td>
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
        <button onClick={() => gotoPage(0)} disabled={!canPreviousPage}>
          {'<<'}
        </button>{' '}
        <button onClick={() => previousPage()} disabled={!canPreviousPage}>
          {'<'}
        </button>{' '}
        <button onClick={() => nextPage()} disabled={!canNextPage}>
          {'>'}
        </button>{' '}
        <button onClick={() => gotoPage(pageCount - 1)} disabled={!canNextPage}>
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
    this.props.loadData(this.props.configData["outlier_detection"], Object.keys(this.props.configData["outlier_detection"])[0]);
    this.setState({
      methods: Object.keys(this.props.configData["outlier_detection"]),
      currMethod: Object.keys(this.props.configData["outlier_detection"])[0]
    });
  }

  switchMethod(e) {
    this.props.loadData(this.props.configData["outlier_detection"], e.target.value);
    this.setState({currMethod: e.target.value});
  }

  render() {
    const columns = [
      {
        Header: "Rank",
        accessor: "rank"
      },
      {
        Header: "ID",
        accessor: "id"
      },
      {
        Header: "Filename",
        accessor: "fileName"
      },
      {
        Header: "Image",
        Cell: (row) => {
          return <div><img height={100} src={"data:image/png;base64,"+row.row.original.imageData}/></div>;
        },
        id: "image"
      },
      {
        Header: "Score",
        accessor: "score"
      }
    ];

    return (
    <div>
      <h1>{this.state["currMethod"]}</h1>
      <Table columns={columns} data={this.props.data}/>
      <select onChange={this.switchMethod}>
        {this.state["methods"].map((method) => <option value={method}>{method}</option>)}
      </select>
    </div>
    );
    
  }
}

export default DataTable;