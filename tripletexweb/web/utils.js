export function parseProjects(projectsText) {
  const re = /^(\S+);(\S*);(\S+);(\S.+)$/
  let projects = {
    0: {
      sysid: 0,
      id: 0,
      parent: null,
      title: '* Ikke satt prosjekt',
      children: []
    }
  }
  projectsText.split('\n').forEach(line => {
    let match = line.match(re)
    if (match) {
      if (!parseInt(match[3])) {
        console.error(`Project ${match[4]} missing ID! Will cause unexpected results`)
      }
      let id = parseInt(match[3])
      let sysid = parseInt(match[1])
      projects[id] = {
        sysid,
        id,
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

export function parseLedger(ledger) {
  let first = true
  let headers = null
  let entries = []

  const floats = ['BeløpInn', 'BeløpUt']
  const ints = ['Avdelingsnummer', 'Kontonummer', 'Prosjektnummer', 'År', 'Måned']

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
    }, {})

    entries.push(resolved)
  })

  return entries
}

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

export function groupHovedbokByDepartmentAndProject(hovedbok, departments, projects) {
  return hovedbok.reduce((prev, entry) => {
    let departmentNumber = entry['Avdelingsnummer'] || 0
    let projectNumber = entry['Prosjektnummer'] || 0
    const accountNumber = entry['Kontonummer'] || 0

    if (!departments[departmentNumber]) {
      departmentNumber = 0
    }

    if (!projects[projectNumber]) {
      projectNumber = 0
    }

    if (!prev[departmentNumber]) {
      prev[departmentNumber] = []
    }

    if (!prev[departmentNumber][projectNumber]) {
      prev[departmentNumber][projectNumber] = []
    }

    if (!prev[departmentNumber][projectNumber][accountNumber]) {
      prev[departmentNumber][projectNumber][accountNumber] = []
    }

    prev[departmentNumber][projectNumber][accountNumber].push(entry)
    return prev
  }, {})
}

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
