/**
 * Parse CSV of projects into an associative array
 *
 * Also generate reference-list of all child-projects in each project
 */
export function parseProjects(projectsText) {
  const re = /^(\S+);(\S*);(\S+);(\S.+)$/
  let projects = {
    0: {
      id: 0,
      number: 0,
      parent: null,
      title: '* Ikke satt prosjekt',
      children: []
    }
  }
  projectsText.split('\n').forEach(line => {
    let match = line.match(re)
    if (match) {
      let number = parseInt(match[3])
      let id = parseInt(match[1])
      projects[id] = {
        id,
        number,
        parent: parseInt(match[2]) || 0,
        title: match[4],
        children: []
      }
    }
  })

  // build parent-child relations
  Object.keys(projects)
    .sort((idA, idB) => projects[idA].title.localeCompare(projects[idB].title))
    .forEach(projectId => {
      let project = projects[projectId]
      if (project.id != 0) {
        projects[project.parent].children.push(project)
      }
    })

  return projects
}

/**
 * Map project data for budget.
 *
 * Budget data has prosjektnummer while we use prosjektId internally.
 */
export function mapProjectIdsForBudget(projects, parsed_ledger) {
  const projectIdByNumber = Object.fromEntries(
    Object.values(projects).map((project) => [project.number, project.id])
  )

  return parsed_ledger.map((it) => {
    const projectNumber = it.Prosjektnummer || 0
    const projectId = projectIdByNumber[it.Prosjektnummer] || 0

    if (projectNumber !== 0 && projectId === 0) {
      console.warn("Lookup of project failed for row", it)
    }

    const result = {
      ...it,
      ProsjektId: projectId,
    }

    delete result.Prosjektnummer
    return result
  })
}

/**
 * Parse CSV of ledger into an associative array
 *
 * The second parameter determines if this data is from Tripletex,
 * as if we know this we can link to more details in Tripletex
 */
export function parseLedger(ledger, isNotFromTripletex) {
  let first = true
  let headers = null
  let entries = []

  const floats = ['BeløpInn', 'BeløpUt']
  const ints = ['Avdelingsnummer', 'Kontonummer', 'Prosjektnummer', 'ProsjektId', 'År', 'Måned']

  ledger.split('\n').forEach(line => {
    line = line.trim()
    if (first) {
      headers = line.split(';')
      first = false
      return
    }

    let resolved = line.split(';').reduce((prev, val, key) => {
      const header = headers[key]
      if (floats.indexOf(header) !== -1) {
        val = parseFloat(val) || 0
      } else if (ints.indexOf(header) !== -1) {
        val = parseInt(val) || 0
      }

      prev[header] = val
      return prev
    }, {isTripletex: !isNotFromTripletex})

    entries.push(resolved)
  })

  return entries
}

/**
 * Parse CSV of accounts into an associative array
 */
export function parseAccounts(accountsRaw) {
  let entries = {}

  accountsRaw.trim().split('\n').forEach(line => {
    line = line.trim()
    const cols = line.split(';')
    const number = parseInt(cols[0])
    entries[number] = {
      number,
      name: cols[1],
      type: cols[2],
      active: cols[3] == '1'
    }
  })

  return entries
}

/**
 * Parse CSV of departments into an associative array
 */
export function parseDepartments(data) {
  let entries = {}

  data.trim().split('\n').forEach(line => {
    line = line.trim()
    const cols = line.split(';')
    const number = parseInt(cols[1])
    entries[number] = {
      id: parseInt(cols[0]),
      number,
      name: cols[2],
    }
  })

  return entries
}

/**
 * Groups all ledger items into this structure:
 *
 * result[departmentNumber][projectId][accountNumber]
 *
 * where each element is an array containing the ledger items
 */
export function groupHovedbokByDepartmentAndProject(hovedbok, departments, projects, filterByDatasets) {
  const filters = filterByDatasets ? filterByDatasets.map(dataset => dataset.filter) : null

  return hovedbok.reduce((prev, entry) => {
    if (filters && !filters.some(filter => filter(entry))) {
      return prev
    }

    let departmentNumber = entry['Avdelingsnummer'] || 0
    let projectId = entry['ProsjektId'] || 0

    const accountNumber = entry['Kontonummer'] || 0

    if (!departments[departmentNumber]) {
      departmentNumber = 0
    }

    if (!projects[projectId]) {
      projectId = 0
    }

    if (!prev[departmentNumber]) {
      prev[departmentNumber] = []
    }

    if (!prev[departmentNumber][projectId]) {
      prev[departmentNumber][projectId] = []
    }

    if (!prev[departmentNumber][projectId][accountNumber]) {
      prev[departmentNumber][projectId][accountNumber] = []
    }

    prev[departmentNumber][projectId][accountNumber].push(entry)
    return prev
  }, {})
}


/**
 * Creates a structure that contain all projects and a sum of kredit and debet
 * both for this project itself but also including all children
 *
 * The structure generated is:
 * cache[departmentNumber][projectNumber][datasetKey]
 *
 * where each element is a object of type `summer`, see the inner function
 */
export function populateCache(datasets, projects, departments, projectsWithHovedbok) {
  let cache = {}

  function summer(parent) {
    this.in = 0
    this.out = 0
    this.count = 0
    this.self = {
      in: 0,
      out: 0,
      count: 0
    }
    this.add = (item, isParent) => {
      this.in += item['BeløpInn']
      this.out += item['BeløpUt']
      this.count++
      if (!isParent) {
        this.self.in += item['BeløpInn']
        this.self.out += item['BeløpUt']
        this.self.count++
      }
      if (parent) {
        parent.add(item, true)
      }
    }
  }

  const parseProject = (departmentNumber, project, parentId) => {
    cache[departmentNumber][project.id] = datasets.reduce((prev, dataset) => {
      const parentSummer = parentId !== null ? cache[departmentNumber][parentId][dataset['key']] : null
      const projectSummer = new summer(parentSummer)
      prev[dataset['key']] = projectSummer

      const d = ((projectsWithHovedbok[departmentNumber] || [])[project.id] || [])
      d.forEach(accountSet => (
        accountSet
          .filter(dataset.filter)
          .forEach(entry => projectSummer.add(entry))
      ))

      return prev
    }, {})

    project.children.forEach(childProject => {
      parseProject(departmentNumber, childProject, project.id)
    })
  }

  Object.keys(departments).forEach(departmentNumber => {
    cache[departmentNumber] = {}
    parseProject(departmentNumber, projects[0], null)
  })

  cache[0] = {}
  parseProject(0, projects[0], null)

  return cache
}

/**
 * Filter ledger by project including subprojects
 */
export function filterLedgerByProject(ledger, filterByProject) {
  function getProjectIds(project) {
    return project.children.reduce((prev, cur) => {
      return prev.concat(getProjectIds(cur))
    }, [project.id])
  }

  if (filterByProject === false) {
    return ledger.filter(entry => entry.Prosjektnummer === 0)
  } else {
    const projectIdList = getProjectIds(filterByProject)
    return ledger.filter(entry => projectIdList.indexOf(entry.Prosjektnummer) !== -1)
  }
}
