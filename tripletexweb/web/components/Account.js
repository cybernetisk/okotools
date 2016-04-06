import React from 'react'

import { amount as amountFormatter } from '../formatter'

const onlyIn = entry => -entry['BeløpInn']
const onlyOut = entry => entry['BeløpUt']
const inAndOut = entry => -entry['BeløpInn'] - entry['BeløpUt']

function calculateAmount(dataset, kontoSet, fnSum, forceText=false) {
  const amount = kontoSet
    .filter(dataset.filter)
    .reduce((prev, entry) => prev + fnSum(entry), 0)

  if (amount !== 0 || forceText) {
    return amountFormatter(amount, 0)
  }
}

class AccountResult extends React.Component {
  constructor(props) {
    super(props)
    this.state = {hover: false}
    this.changeHover = this.changeHover.bind(this)
  }

  renderResult(dataset) {
    if (!dataset.entry.isTripletex) {
      return calculateAmount(dataset, this.props.kontoSet, inAndOut, true)
    } else {
      return (
        <a href={dataset.ledgerLink(this.props.department.id, this.props.project.sysid, this.props.kontoSet[0].Kontonummer)} target="_blank">
          {calculateAmount(dataset, this.props.kontoSet, inAndOut, true)}
        </a>
      )
    }
  }

  changeHover(state) {
    this.setState({
      hover: state
    })
  }

  renderDetails() {
    if (!this.state.hover) {
      return null
    }

    const entries = this.props.kontoSet.filter(this.props.dataset.filter)

    if (entries.length === 0) {
      return null
    }

    return (
      <div className="account-details">
        <table>
          <tbody>
            {entries.map((entry, i) => (
              <tr key={i}>
                <td>{entry.Beskrivelse || <i>Ingen beskrivelse</i>}</td>
                <td>{amountFormatter(entry.BeløpInn-entry.BeløpUt, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  render() {
    return (
      <td className="project-result" onMouseEnter={() => this.changeHover(true)} onMouseLeave={() => this.changeHover(false)}>
        {this.renderResult(this.props.dataset)}
        {this.renderDetails()}
      </td>
    )
  }
}

export default class Account extends React.Component {
  static propTypes = {
    datasets: React.PropTypes.array.isRequired,
    department: React.PropTypes.object.isRequired,
    kontoSet: React.PropTypes.array.isRequired,
    level: React.PropTypes.number.isRequired,
    project: React.PropTypes.object.isRequired,
  }

  static contextTypes = {
    accounts: React.PropTypes.object.isRequired,
  }

  render() {
    let accountText
    if (this.context.accounts[this.props.kontoSet[0].Kontonummer] === undefined) {
      accountText = 'Konto ikke valgt'
    } else {
      const name = this.context.accounts[this.props.kontoSet[0].Kontonummer].name
      accountText = `${this.props.kontoSet[0].Kontonummer} ${name}`
    }

    return (
      <tr className="project-account">
        <td>{Array(this.props.level).join('     ').replace(/ /g, '\u00a0')}{accountText}</td>
        {this.props.datasets.map(dataset => [
          <td key={`${dataset['key']}-in`}>{calculateAmount(dataset, this.props.kontoSet, onlyIn)}</td>,
          <td key={`${dataset['key']}-out`}>{calculateAmount(dataset, this.props.kontoSet, onlyOut)}</td>,
          <AccountResult key={`${dataset['key']}-inout`} {...this.props} dataset={dataset} />
        ])}
      </tr>
    )
  }
}
