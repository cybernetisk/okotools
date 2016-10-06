import React from 'react'
import ReactDOM from 'react-dom'

import * as utils from './utils'

import AccountList from './components/AccountList'
import ReportTable from './components/ReportTable'
import ProjectFilter from './components/ProjectFilter'

import './style.scss'

class DataWrapper extends React.Component {
  static reports = {
    contextId: 'context_id',
    projects: 'projects',
    accounts: 'accounts',
    departments: 'departments',
    ledger: 'aggregated',
    budget: 'budget',
    budgetUrl: 'budget_url'
  }

  constructor(props) {
    super(props)

    this.state = {}

    Object.keys(DataWrapper.reports).forEach(stateName => {
      const reportUrl = `reports/${DataWrapper.reports[stateName]}.txt`
      fetch(reportUrl, {
        credentials: 'include'
      })
        .then(response => {
          if (!response.ok) {
            return ''
          } else {
            return response.text()
          }
        })
        .then(responseText => {
          this.setState({
            [stateName]: responseText.trim()
          })
        })
    })
  }

  renderLoading() {
    return (
      <span>Laster data...</span>
    )
  }

  isLoading() {
    let loading = false
    Object.keys(DataWrapper.reports).forEach(stateName => {
      if (this.state[stateName] === undefined) {
        loading = true
      }
    })

    return loading
  }

  render() {
    if (this.isLoading()) {
      return this.renderLoading()
    }

    return (
      <ReportTableWrapper {...this.state} />
    )
  }
}

class ReportTableWrapper extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      showOnlyDatasets: JSON.parse(window.localStorage.showOnlyDatasets || '[]'),
      showHistoricalAccounts: false,
      projectFilter: null,
      showMenu: false
    }
    this.changeHistoricalAccounts = this.changeHistoricalAccounts.bind(this)
    this.changeProjectFilter = this.changeProjectFilter.bind(this)
  }

  componentWillMount() {
    this.updateState()
  }

  componentWillReceiveProps(nextProps) {
    this.updateState()
  }

  updateState() {
    const accounts = utils.parseAccounts(this.props.accounts)
    const projects = utils.parseProjects(this.props.projects)

    const ledger = utils.parseLedger(this.props.ledger).concat(utils.parseLedger(this.props.budget, true))
    //const ledger = utils.parseLedger(this.props.budget)
      // filter out egenkapitalendring og hjelpekonto
      .filter(entry => entry.Kontonummer !== 8960 && entry.Kontonummer !== 9999)

    let departments = utils.parseDepartments(this.props.departments)
    if (Object.keys(departments).length === 1) {
      // if only one department ignore departments
      departments = {}
    }

    const datasets = this.buildDatasets(ledger)

    this.setState({
      accounts,
      projects,
      ledger,
      departments,
      datasets
    })
  }

  resultReportLink(dateFrom, dateTo, departmentId, projectId, showChildProjects) {
    return `https://tripletex.no/execute/resultReport2?javaClass=no.tripletex.tcp.web.ResultReport2Form&documentationComponent=133&isExpandedFilter=true&period.startDate=${dateFrom}&period.endOfPeriodDate=${dateTo}&selectedDepartmentId=${departmentId !== undefined ? departmentId : '-1'}&selectedProjectId=${projectId !== undefined ? projectId : '-1'}&viewAccountingPeriods=true&contextId=${this.props.contextId}&includeSubProjectsOfSelectedProject=${showChildProjects ? 'true' : 'false'}`
  }

  ledgerLink(dateFrom, dateTo, departmentId, projectId, accountNumber) {
    return `https://tripletex.no/execute/ledger?javaClass=no.tripletex.tcp.web.LedgerForm&documentationComponent=140&contextId=${this.props.contextId}&isExpandedFilter=false&onlyOpenPostings=false&period.startDate=${dateFrom}&period.endOfPeriodDate=${dateTo}&period.periodType=0&openPostingsDateBefore=&accountId=-1&startNumber=${accountNumber}&endNumber=${accountNumber}&selectedCustomerId=-1&selectedVendorId=-1&selectedEmployeeId=-1&selectedDepartmentId=${departmentId}&selectedProjectId=${projectId}&includeSubProjectsOfSelectedProject=false&selectedProductId=-1&selectedVatId=-1&minAmountString=&maxAmountString=&amountType=2&orderBy=0&postingCount=500&viewCustomer=true&viewVendor=true&viewEmployee=false&viewDepartment=false&viewProject=false&viewProduct=false`
  }

  buildDatasets(ledger) {
    return ledger.reduce((prev, entry) => {
      const key = entry['År'] + entry['Type'] + entry['Versjon'] + (entry['Måned'] == 0 ? 0 : (entry['Måned'] < 7 ? 1 : 2))

      if (!prev.some(elm => elm.key === key)) {
        const filter = test => test['Type'] == entry['Type']
          && test['Versjon'] == entry['Versjon']
          && test['År'] === entry['År']
          && (entry['Måned'] == 0 ? test['Måned'] == 0 : (entry['Måned'] < 7 ? test['Måned'] < 7 : test['Måned'] >= 7))

        const semester = entry['Måned'] == 0 ? 'År' : (entry['Måned'] < 7 ? 'Vår' : 'Høst')
        const dateFrom = `${entry['År']}-${entry['Måned'] < 7 ? '01-01' : '01-06'}`
        const dateTo = `${entry['År']}-${entry['Måned'] < 7 && entry['Måned'] !== 0 ? '06-30' : '12-31'}`

        prev.push({
          key,
          type: entry['Type'],
          entry,
          description1: `${semester} ${entry['År']}`,
          description2: `${entry['Type']} (${entry['Versjon']})`,
          isYear: entry['Måned'] == 0,
          filter,
          resultReportLink: (departmentId, projectId, showChildProjects) => this.resultReportLink(dateFrom, dateTo, departmentId, projectId, showChildProjects),
          ledgerLink: (departmentId, projectId, accountNumber) => this.ledgerLink(dateFrom, dateTo, departmentId, projectId, accountNumber),
        })
      }

      return prev
    }, [])
      .sort((a, b) => b.key.localeCompare(a.key))
  }

  aggregateDatasets(datasets) {
    let newDatasets = datasets.slice(0)
    let sumDetails = []

    datasets.forEach(dataset => {
      const entry = dataset.entry
      const sumKey = entry['År'] + entry['Type'] + entry['Versjon'] + '3'
      const sumDateFrom = `${entry['År']}-01-01`
      const sumDateTo = `${entry['År']}-12-31`

      sumDetails.push({
        key: sumKey,
        type: entry['Type'],
        description1: `År ${entry['År']}`,
        description2: `${entry['Type']} (${entry['Versjon']})`,
        filter: test => test['År'] === entry['År'] && test['Type'] == entry['Type'] && test['Versjon'] == entry['Versjon'],
        resultReportLink: (departmentId, projectId, showChildProjects) => this.resultReportLink(sumDateFrom, sumDateTo, departmentId, projectId, showChildProjects),
        ledgerLink: (departmentId, projectId, accountNumber) => this.ledgerLink(sumDateFrom, sumDateTo, departmentId, projectId, accountNumber),
        sumItem: dataset,
        isSum: true,
        isYear: true,
        entry
      })

      dataset.haveSum = false
    })

    // add sum columns if needed (more than one column is being summed)
    let sumAdded = []
    sumDetails.forEach(item => {
      if (sumAdded.indexOf(item.key) === -1) {
        const allItems = sumDetails.filter(i => i.key === item.key)
        if (allItems.length > 1) {
          allItems.forEach(otheritem => {
            otheritem.sumItem.haveSum = true
          })
          delete item.sumItem
          newDatasets.push(item)
          sumAdded.push(item.key)
        }
      }
    })

    return newDatasets.sort((a, b) => b.key.localeCompare(a.key))
  }

  changeHistoricalAccounts() {
    this.setState({
      showHistoricalAccounts: !this.state.showHistoricalAccounts
    })

    window.localStorage.showHistoricalAccounts = JSON.stringify(!this.state.showHistoricalAccounts)
  }

  changeProjectFilter(newValue) {
    this.setState({
      projectFilter: newValue
    })
  }

  changeDatasetVisibility(dataset) {
    let showOnlyDatasets = this.state.showOnlyDatasets
    const pos = showOnlyDatasets.indexOf(dataset.key)
    if (pos !== -1) {
      showOnlyDatasets.splice(pos, 1)
    } else {
      showOnlyDatasets.push(dataset.key)
    }

    this.setState({
      showOnlyDatasets
    })

    window.localStorage.showOnlyDatasets = JSON.stringify(showOnlyDatasets)
  }

  showMenu(state) {
    this.setState({
      showMenu: state
    })
  }

  filterDatasets(datasets, showOnly) {
    return datasets.filter(dataset => showOnly.indexOf(dataset.key) !== -1)
  }

  renderProjectFilter() {
    if (this.state.projectFilter === null) {
      return null
    }

    let projectText
    if (this.state.projectFilter === false) {
      projectText = '(Føringer som ikke er tilordnet prosjekt)'
    } else {
      const generateProjectTree = () => {
        let isFirst = true
        let projectList = []
        let project = this.state.projectFilter
        while (project.id !== 0) {
          let title = project.title
          if (isFirst) {
            isFirst = false
            title += ' (' + project.id + ')'
          }

          projectList.push(title)

          project = this.state.projects[project.parent]
        }
        return projectList.reverse()
      }

      projectText = generateProjectTree().join(' -> ')
    }

    return (
      <p className="visible-print">
        Filtrert etter prosjekt: {projectText}
      </p>
    )
  }

  render() {
    let allDatasets = this.aggregateDatasets(this.state.datasets)

    let filteredDatasets = this.filterDatasets(allDatasets, this.state.showOnlyDatasets)

    const filterByDatasets = this.state.showHistoricalAccounts ? null : filteredDatasets
    const ledger = this.state.projectFilter !== null ? utils.filterLedgerByProject(this.state.ledger, this.state.projectFilter) : this.state.ledger
    const projectsWithHovedbok = utils.groupHovedbokByDepartmentAndProject(ledger, this.state.departments, this.state.projects, filterByDatasets)
    const projectsWithDatasets = utils.populateCache(filteredDatasets, this.state.projects, this.state.departments, projectsWithHovedbok)

    const datasetsYears = [ ...new Set(allDatasets.map(dataset => dataset.entry['År'])) ]

    return (
      <div className={this.state.showMenu ? 'showMenu' : ''}>
        <div className="hidden-print menu">
          <h1>Budsjett- og regnskapsrapporter</h1>
          <p>
            <a href={`${BACKEND_URL}api/fetch-accounting`}>Last ny data fra Tripletex</a>
          </p>
          <p>
            <a href={`${BACKEND_URL}api/fetch-budget`}>Last ny data fra budsjett</a>
            {this.props.budgetUrl ? (
              <span> (<a href={this.props.budgetUrl} target="_blank">rediger budsjett</a>)</span>
            ) : null}
          </p>
          <p>
            Filtrer etter prosjekt:
            {' '}
            <ProjectFilter
              currentFilter={this.state.projectFilter}
              onChange={this.changeProjectFilter}
              projects={this.state.projects}
            />
          </p>
          <p className="checkbox">
            <label>
              <input
                type="checkbox"
                onChange={this.changeHistoricalAccounts}
                checked={this.state.showHistoricalAccounts}
              /> Vis også tidligere kontoer benyttet i prosjektene
            </label>
          </p>
          {datasetsYears.map(year => (
            <div key={year}>
              <p>{year}</p>
              <ul>
                {allDatasets.filter(dataset => dataset.entry['År'] === year).map(dataset => (
                  <li key={dataset.key} className={`checkbox${dataset.isYear ? ' dataset-year' : ''}`}>
                    <label>
                      <input
                        type="checkbox"
                        onChange={ev => this.changeDatasetVisibility(dataset)}
                        checked={this.state.showOnlyDatasets.indexOf(dataset.key) !== -1}
                      />
                      {' '}
                      {dataset.description1} {dataset.description2} {dataset.isSum}
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          <AccountList accounts={this.state.accounts} />
        </div>
        <div className="page-content">
          <div className="top-bar">
            <a className={"menu-toggle" + (this.state.showMenu ? ' menu-active' : '')} onClick={() => this.showMenu(!this.state.showMenu)}>
              <span className="sr-only">Vis meny</span>
              <span className="icon-bar"></span>
              <span className="icon-bar"></span>
              <span className="icon-bar"></span>
            </a>
            <h1>Resultatrapport</h1>
          </div>
          {this.renderProjectFilter()}

          {filteredDatasets.length == 0 ? (
            <div>
              <p>Velg ett eller flere datasett fra menyen for å vise rapport.</p>
              <p>Husk at du må laste ny data fra regnskapet/budsjettet (se i menyen) for å få nyeste rapportene.</p>
            </div>
          ) : (
            <ReportTable
              projects={this.state.projects}
              accounts={this.state.accounts}
              departments={this.state.departments}
              projectsWithDatasets={projectsWithDatasets}
              projectsWithHovedbok={projectsWithHovedbok}
              datasets={filteredDatasets}
            />
          )}
          <div className="hidden-print">
            <hr />
            <p>
              <a href="https://github.com/cybrairai/okotools/tree/master/tripletexweb">GitHub-prosjekt</a> - utviklet for <a href="http://cyb.no/">Cybernetisk Selskab</a> og <a href="http://foreningenbs.no/">Foreningen Blindern Studenterhjem</a>
            </p>
          </div>
        </div>
      </div>
    )
  }
}

ReactDOM.render(
    <DataWrapper />,
    document.getElementById('app')
)
