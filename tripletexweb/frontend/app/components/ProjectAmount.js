import React from 'react'

import { amount as amountFormatter } from '../formatter'

export default class ProjectAmount extends React.Component {

  static propTypes = {
    dataset: React.PropTypes.object.isRequired,
    department: React.PropTypes.object,
    fnSum: React.PropTypes.func.isRequired,
    forceText: React.PropTypes.bool,
    onlyThis: React.PropTypes.bool,
    project: React.PropTypes.object.isRequired,
    projectsWithDatasets: React.PropTypes.object.isRequired,
  }

  getDepartmentSum(departmentNumber) {
    let summer = this.props.projectsWithDatasets[departmentNumber][this.props.project.id][this.props.dataset.key]
    if (this.props.onlyThis) {
      summer = summer.self
    }
    return [this.props.fnSum(summer), summer.count]
  }

  render() {
    let sum, sumCount
    if (this.props.department) {
      [sum, sumCount] = this.getDepartmentSum(this.props.department.number)
    } else {
      [sum, sumCount] = Object.keys(this.props.projectsWithDatasets).reduce((prev, departmentNumber) => {
        let ret = this.getDepartmentSum(departmentNumber)
        prev[0] += ret[0]
        prev[1] += ret[1]
        return prev
      }, [0, 0])
    }

    if (sum !== 0 || (this.props.forceText && this.props.sumCount != 0)) {
      return <span>{amountFormatter(sum, 0)}</span>
    } else {
      return <span></span>
    }
  }
}
