import React from 'react'
import Project from './Project'

export default class ReportTable extends React.Component {
  static childContextTypes = {
    projectsWithDatasets: React.PropTypes.object.isRequired,
    projectsWithHovedbok: React.PropTypes.object.isRequired,
    accounts: React.PropTypes.object.isRequired,
  }

  getChildContext() {
    return {
      projectsWithDatasets: this.props.projectsWithDatasets,
      projectsWithHovedbok: this.props.projectsWithHovedbok,
      accounts: this.props.accounts,
    }
  }

  constructor(props) {
    super(props)
    this.setExpanded = this.setExpanded.bind(this)
    this.state = {
      expanded: []
    }
  }

  setExpanded(projectKey, expand) {
    if (!expand) {
      let start = this.state.expanded.indexOf(projectKey)
      if (start !== -1) {
        this.state.expanded.splice(start, 1)
        this.forceUpdate()
      }
    } else if (this.state.expanded.indexOf(projectKey) === -1) {
      this.state.expanded.push(projectKey)
      this.forceUpdate()
    }
  }

  buildDepartmentTree() {
    if (Object.keys(this.props.projectsWithDatasets).length === 1) {
      return this.buildProjectTree({
        id: -1,
        number: 0,
        name: 'Mangler avdeling'
      }, this.props.projects[0], 0)
    }

    let elms = []

    const addDepartment = department => {
      const expandKey = department.number
      const isExpanded = this.state.expanded.indexOf(expandKey) !== -1

      elms.push(
        <tbody key={expandKey}>
          <Project
            isTotalSum={true}
            level={1}
            project={this.props.projects[0]}
            department={department}
            isExpanded={isExpanded}
            setExpanded={this.setExpanded}
            expandKey={expandKey}
            datasets={this.props.datasets} />
        </tbody>
      )

      if (isExpanded) {
        elms = elms.concat(this.buildProjectTree(department, this.props.projects[0], 1))
      }
    }

    Object.keys(this.props.departments).forEach(departmentNumber => {
      const depDatasets = this.props.projectsWithDatasets[departmentNumber]
      const haveAnyData = Object.keys(depDatasets).map(key => depDatasets[key]).some(project => {
        return Object.keys(project).map(key => project[key]).some(summer => summer.count > 0);
      });

      if (haveAnyData) {
        addDepartment(this.props.departments[departmentNumber])
      }
    })

    const hasMissingDepartment = Object.keys((this.props.projectsWithDatasets[0] || {})[0] || {})
      .map(key => this.props.projectsWithDatasets[0][0][key])
      .some(summer => summer.count > 0)
    if (hasMissingDepartment) {
      addDepartment({
        id: 0,
        number: 0,
        name: 'Mangler avdeling'
      })
    }

    return elms
  }

  buildProjectTree(department, project, level) {
    let elms = []
    const departmentNumber = department.number

    const projectSummers = Object.keys(this.props.projectsWithDatasets[departmentNumber][project.id] || {})
      .map(key => this.props.projectsWithDatasets[departmentNumber][project.id][key])
    const projectHaveAnyData = projectSummers.some(summer => summer.count > 0)

    if (!projectHaveAnyData) {
      return elms
    }

    const projectHaveSelfData = projectSummers.some(summer => summer.self.count > 0)
    const projectHaveSubprojectData = projectSummers.some(summer => summer.self.count != summer.count)

    const expandKey = `${departmentNumber}-${project.id}`
    if (project.id !== 0) {
      elms.push(
        <Project
          key={expandKey}
          level={level}
          project={project}
          department={department}
          setExpanded={this.setExpanded}
          isExpanded={this.state.expanded.indexOf(expandKey) !== -1}
          hasChildProjects={projectHaveSubprojectData}
          expandKey={expandKey}
          selfData={projectHaveSelfData}
          datasets={this.props.datasets} />
      )
    }

    if (project.id === 0 || this.state.expanded.indexOf(expandKey) !== -1) {
      project.children.forEach(childProject => {
        elms = elms.concat(this.buildProjectTree(department, childProject, level + 1))
      })

      if ((project.id === 0 || projectHaveSubprojectData) && projectHaveSelfData) {
        const otherExpandKey = `${departmentNumber}-${project.id}-other`
        elms.push(
          <Project
            key={otherExpandKey}
            level={level+1}
            project={project}
            department={department}
            onlyThis={true}
            setExpanded={this.setExpanded}
            isExpanded={this.state.expanded.indexOf(otherExpandKey) !== -1}
            expandKey={otherExpandKey}
            selfData={projectHaveSelfData}
            datasets={this.props.datasets} />
        )
      }
    }

    return elms
  }

  render() {
    return (
      <table className="table table-condensed">
        <thead>
          <tr>
            <th rowSpan={3}>{Object.keys(this.props.departments).length === 0 ? 'Prosjekt' : 'Avdeling / prosjekt'}</th>
            {this.props.datasets.map(dataset => (
              <th key={dataset.key} colSpan={3} className={dataset.haveSum ? 'dataset-have-sum' : ''}>{dataset.description1}</th>
            ))}
          </tr>
          <tr>
            {this.props.datasets.map(dataset => (
              <th key={dataset.key} colSpan={3} className={dataset.haveSum ? 'dataset-have-sum' : ''}>{dataset.description2}</th>
            ))}
          </tr>
          <tr>
            {this.props.datasets.map(dataset => [
              <th key={`${dataset.key}-1`} className={dataset.haveSum ? 'dataset-have-sum' : ''}>Inntekter</th>,
              <th key={`${dataset.key}-2`} className={dataset.haveSum ? 'dataset-have-sum' : ''}>Kostnader</th>,
              <th key={`${dataset.key}-3`} className={dataset.haveSum ? 'project-result dataset-have-sum' : 'project-result'}>Resultat</th>
            ])}
          </tr>
        </thead>
        <tfoot>
          <Project
            isTotalSum={true}
            level={0}
            project={this.props.projects[0]}
            datasets={this.props.datasets} />
        </tfoot>
        {this.buildDepartmentTree()}
      </table>
    )
  }
}
