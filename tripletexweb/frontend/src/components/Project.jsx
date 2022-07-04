import React from 'react'
import PropTypes from 'prop-types'
import Account from './Account.jsx'
import ProjectAmount from './ProjectAmount'

import { amount as amountFormatter } from '../formatter'

const onlyIn = entry => -entry.in
const onlyOut = entry => entry.out
const inAndOut = entry => -entry.in - entry.out

export default class Project extends React.Component {
  static contextTypes = {
    projectsWithDatasets: PropTypes.object.isRequired,
    projectsWithHovedbok: PropTypes.object.isRequired,
    accounts: PropTypes.object.isRequired,
  }

  static propTypes = {
    datasets: PropTypes.array.isRequired,
    department: PropTypes.object,
    hasChildProjects: PropTypes.bool,
    isExpanded: PropTypes.bool,
    isTotalSum: PropTypes.bool,
    level: PropTypes.number.isRequired,
    onlyThis: PropTypes.bool,
    project: PropTypes.object,
    setExpanded: PropTypes.func,
  }

  constructor(props) {
    super(props)
    this.handleClick = this.handleClick.bind(this)
  }

  handleClick(e) {
    if (e.target.parentNode.tagName === 'A') {
      return
    }

    if (this.props.setExpanded) {
      this.props.setExpanded(this.props.expandKey, !this.props.isExpanded)
    }
  }

  renderAccounts() {
    const showAccounts = this.props.isExpanded && (!this.props.hasChildProjects || this.props.onlyThis)
    if (showAccounts) {
      return (this.context.projectsWithHovedbok[this.props.department.number][this.props.project.id] || []).map(account => (
        <Account
          key={account[0].Kontonummer}
          department={this.props.department}
          project={this.props.project}
          kontoSet={account}
          level={this.props.level + 1}
          datasets={this.props.datasets} />
      ))
    }
  }

  renderTotalSum() {
    let className = `project-level-${this.props.level}`
    if (this.props.setExpanded) {
      className += ' pointer'
    }

    return (
      <tr className={className} onClick={this.handleClick}>
        <th>{this.props.department ? this.props.department.name : 'Sum'}</th>
        {this.props.datasets.map(dataset => [
          <th key={`${dataset['key']}-in`}>
            <ProjectAmount
              dataset={dataset}
              department={this.props.department}
              fnSum={onlyIn}
              project={this.props.project}
              projectsWithDatasets={this.context.projectsWithDatasets} />
          </th>,
          <th key={`${dataset['key']}-out`}>
            <ProjectAmount
              dataset={dataset}
              department={this.props.department}
              fnSum={onlyOut}
              project={this.props.project}
              projectsWithDatasets={this.context.projectsWithDatasets} />
          </th>,
          <th key={`${dataset['key']}-inout`} className="project-result">
            {this.getResultText(dataset)}
          </th>
        ])}
      </tr>
    )
  }

  getResultText(dataset) {
    const totalAmount = (
      <ProjectAmount
        dataset={dataset}
        department={this.props.department}
        fnSum={inAndOut}
        forceText={true}
        onlyThis={this.props.onlyThis}
        project={this.props.project}
        projectsWithDatasets={this.context.projectsWithDatasets} />
    )

    if (!dataset.entry.isTripletex) {
      return totalAmount
    }

    let link

    // department links
    if (this.props.isTotalSum) {
      link = dataset.resultReportLink(this.props.department ? this.props.department.id : undefined)
    }

    // project specific links
    else if (this.props.selfData && (this.props.onlyThis || !this.props.hasChildProjects)) {
      link = dataset.resultReportLink(this.props.department.id, this.props.project.id)
    }

    // accumulated projects links
    else {
      link = dataset.resultReportLink(this.props.department.id, this.props.project.id, true)
    }

    return (
      <a href={link} target="_blank">
        {totalAmount}
      </a>
    )
  }

  getTitle() {
    const title = this.props.onlyThis
      ? 'Uspesifisert'
      : (
        <span>
          {this.props.project.title}
          {' '}
          <span className="project-number">{this.props.project.number}</span>
        </span>
      )


    const expand = !this.props.isExpanded && this.props.hasChildProjects && !this.props.onlyThis
      ? ' +'
      : ''

    return (
      <span>
        {Array(this.props.level).join('     ').replace(/ /g, '\u00a0')}
        {title}
        {expand}
      </span>
    )
  }

  render() {
    if (this.props.isTotalSum) {
      return this.renderTotalSum()
    }

    let className = `project-level-${this.props.level}`
    if (this.props.setExpanded) {
      className += ' pointer'
    }

    return (
      <tbody>
        <tr className={className} onClick={this.handleClick}>
          <td>{this.getTitle()}</td>
          {this.props.datasets.map(dataset => [
            <td key={`${dataset['key']}-in`}>
              <ProjectAmount
                dataset={dataset}
                department={this.props.department}
                fnSum={onlyIn}
                onlyThis={this.props.onlyThis}
                project={this.props.project}
                projectsWithDatasets={this.context.projectsWithDatasets} />
              </td>,
            <td key={`${dataset['key']}-out`}>
              <ProjectAmount
                dataset={dataset}
                department={this.props.department}
                fnSum={onlyOut}
                onlyThis={this.props.onlyThis}
                project={this.props.project}
                projectsWithDatasets={this.context.projectsWithDatasets} />
            </td>,
            <td key={`${dataset['key']}-inout`} className="project-result">
              {this.getResultText(dataset)}
            </td>
          ])}
        </tr>
        {this.renderAccounts()}
      </tbody>
    )
  }
}
