import React from 'react'
import ReactDOM from 'react-dom'

import * as utils from './utils'

import ProjectReport from './components/ProjectReport'

import './style.scss'

class DataWrapper extends React.Component {
  static reports = {
    contextId: 'context_id',
    projects: 'projects',
    accounts: 'accounts',
    departments: 'departments',
    ledger: 'aggregated',
    //budget: 'budget',
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
          return response.text()
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
      <ProjectReportWrapper {...this.state} />
    )
  }
}

class ProjectReportWrapper extends React.Component {
  resultReportLink(dateFrom, dateTo, departmentId, projectId, showChildProjects) {
    return `https://tripletex.no/execute/resultReport2?javaClass=no.tripletex.tcp.web.ResultReport2Form&documentationComponent=133&isExpandedFilter=true&period.startDate=${dateFrom}&period.endOfPeriodDate=${dateTo}&selectedDepartmentId=${departmentId !== undefined ? departmentId : '-1'}&selectedProjectId=${projectId !== undefined ? projectId : '-1'}&viewAccountingPeriods=true&contextId=${this.props.contextId}&includeSubProjectsOfSelectedProject=${showChildProjects ? 'true' : 'false'}`
  }

  ledgerLink(dateFrom, dateTo, departmentId, projectId, accountNumber) {
    return `https://tripletex.no/execute/ledger?javaClass=no.tripletex.tcp.web.LedgerForm&documentationComponent=140&contextId=${this.props.contextId}&isExpandedFilter=false&onlyOpenPostings=false&period.startDate=${dateFrom}&period.endOfPeriodDate=${dateTo}&period.periodType=0&openPostingsDateBefore=&accountId=-1&startNumber=${accountNumber}&endNumber=${accountNumber}&selectedCustomerId=-1&selectedVendorId=-1&selectedEmployeeId=-1&selectedDepartmentId=${departmentId}&selectedProjectId=${projectId}&includeSubProjectsOfSelectedProject=false&selectedProductId=-1&selectedVatId=-1&minAmountString=&maxAmountString=&amountType=2&orderBy=0&postingCount=500&viewCustomer=true&viewVendor=true&viewEmployee=false&viewDepartment=false&viewProject=false&viewProduct=false`
  }

  buildDatasets(ledger) {
    let sumDetails = []
    let datasets = ledger.reduce((prev, entry) => {
      const key = (entry['År'] * 100 + (entry['Måned'] < 7 ? 1 : 2)) + entry['Type'] + entry['Versjon']
      if (!prev.some(elm => elm.key === key)) {
        const filter = test => test['Type'] == entry['Type'] && test['Versjon'] == entry['Versjon'] && test['År'] === entry['År'] && (entry['Måned'] < 7
          ? test['Måned'] < 7
          : test['Måned'] >= 7)
        const semester = entry['Måned'] < 7 ? 'Vår' : 'Høst'
        const dateFrom = `${entry['År']}-${entry['Måned'] < 7 ? '01-01' : '01-06'}`
        const dateTo = `${entry['År']}-${entry['Måned'] < 7 ? '06-30' : '12-31'}`

        const item = {
          key,
          description1: `${semester} ${entry['År']}`,
          description2: `${entry['Type']} (${entry['Versjon']})`,
          filter,
          resultReportLink: (departmentId) => this.resultReportLink(dateFrom, dateTo, departmentId),
          ledgerLink: (departmentId, projectId, accountNumber) => this.ledgerLink(dateFrom, dateTo, departmentId, projectId, accountNumber),
        }
        prev.push(item)

        const sumKey = (entry['År'] * 100 + 99) + entry['Type'] + entry['Versjon']
        const sumDateFrom = `${entry['År']}-01-01`
        const sumDateTo = `${entry['År']}-12-31`

        sumDetails.push({
          key: sumKey,
          description1: `Sum ${entry['År']}`,
          description2: `${entry['Type']} (${entry['Versjon']})`,
          filter: test => test['År'] === entry['År'] && test['Type'] == entry['Type'] && test['Versjon'] == entry['Versjon'],
          resultReportLink: (departmentId) => this.resultReportLink(dateFrom, dateTo, departmentId),
          ledgerLink: (departmentId, projectId, accountNumber) => this.ledgerLink(sumDateFrom, sumDateTo, departmentId, projectId, accountNumber),
          sumItem: item,
          isSum: true,
        })
      }

      return prev
    }, [])

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
          datasets.push(item)
          sumAdded.push(item.key)
        }
      }
    })

    return datasets.sort((a, b) => b.key.localeCompare(a.key))
  }

  render() {
    const accounts = utils.parseAccounts(this.props.accounts)
    const projects = utils.parseProjects(this.props.projects)
    const ledger = utils.parseLedger(this.props.ledger) //.concat(utils.parseLedger(this.props.budget))
      // filter out egenkapitalendring og hjelpekonto
      .filter(entry => entry.Kontonummer !== 8960 && entry.Kontonummer !== 9999)

    let departments = utils.parseDepartments(this.props.departments)
    if (Object.keys(departments).length === 1) {
      // if only one department ignore departments
      departments = {}
    }

    //const months = [,'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Des']

    const datasets = this.buildDatasets(ledger)

    const projectsWithHovedbok = utils.groupHovedbokByDepartmentAndProject(ledger, departments, projects)
    const projectsWithDatasets = utils.populateCache(datasets, projects, departments, projectsWithHovedbok)

    return (
      <ProjectReport
        projects={projects}
        accounts={accounts}
        departments={departments}
        projectsWithDatasets={projectsWithDatasets}
        projectsWithHovedbok={projectsWithHovedbok}
        datasets={datasets} />
    )
  }
}

ReactDOM.render(
    <DataWrapper />,
    document.getElementById('app')
)
