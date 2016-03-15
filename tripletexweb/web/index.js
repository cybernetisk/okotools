import React from 'react'
import ReactDOM from 'react-dom'

import * as data from './data'
import * as utils from './utils'

import ProjectReport from './components/ProjectReport'

import './style.scss'

const accounts = utils.parseAccounts(data.dataAccounts)
const projects = utils.parseProjects(data.dataProjects)
const ledger = utils.parseLedger(data.dataLedger) //.concat(utils.parseLedger(data.dataBudget))
  // filter out egenkapitalendring og hjelpekonto
  .filter(entry => entry.Kontonummer !== 8960 && entry.Kontonummer !== 9999)
const departments = utils.parseDepartments(data.dataDepartments)
//const departments = []

const months = [,'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Des']
const contextId = data.contextId

function resultReportLink(dateFrom, dateTo, departmentId, projectId, showChildProjects) {
  return `https://tripletex.no/execute/resultReport2?javaClass=no.tripletex.tcp.web.ResultReport2Form&documentationComponent=133&isExpandedFilter=true&period.startDate=${dateFrom}&period.endOfPeriodDate=${dateTo}&selectedDepartmentId=${departmentId !== undefined ? departmentId : '-1'}&selectedProjectId=${projectId !== undefined ? projectId : '-1'}&viewAccountingPeriods=true&contextId=${contextId}&includeSubProjectsOfSelectedProject=${showChildProjects ? 'true' : 'false'}`
}

function ledgerLink(dateFrom, dateTo, departmentId, projectId, accountNumber) {
  return `https://tripletex.no/execute/ledger?javaClass=no.tripletex.tcp.web.LedgerForm&documentationComponent=140&contextId=${contextId}&isExpandedFilter=false&onlyOpenPostings=false&period.startDate=${dateFrom}&period.endOfPeriodDate=${dateTo}&period.periodType=0&openPostingsDateBefore=&accountId=-1&startNumber=${accountNumber}&endNumber=${accountNumber}&selectedCustomerId=-1&selectedVendorId=-1&selectedEmployeeId=-1&selectedDepartmentId=${departmentId}&selectedProjectId=${projectId}&includeSubProjectsOfSelectedProject=false&selectedProductId=-1&selectedVatId=-1&minAmountString=&maxAmountString=&amountType=2&orderBy=0&postingCount=500&viewCustomer=true&viewVendor=true&viewEmployee=false&viewDepartment=false&viewProject=false&viewProduct=false`
}

function buildDatasets(ledger) {
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
        resultReportLink: (departmentId) => resultReportLink(dateFrom, dateTo, departmentId),
        ledgerLink: (departmentId, projectId, accountNumber) => ledgerLink(dateFrom, dateTo, departmentId, projectId, accountNumber),
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
        resultReportLink: (departmentId) => resultReportLink(dateFrom, dateTo, departmentId),
        ledgerLink: (departmentId, projectId, accountNumber) => ledgerLink(sumDateFrom, sumDateTo, departmentId, projectId, accountNumber),
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

const datasets = buildDatasets(ledger)


const projectsWithHovedbok = utils.groupHovedbokByDepartmentAndProject(ledger, departments, projects)
const projectsWithDatasets = utils.populateCache(datasets, projects, departments, projectsWithHovedbok)

ReactDOM.render(
    <ProjectReport
      projects={projects}
      accounts={accounts}
      departments={departments}
      projectsWithDatasets={projectsWithDatasets}
      projectsWithHovedbok={projectsWithHovedbok}
      datasets={datasets} />,
    document.getElementById('app')
)
