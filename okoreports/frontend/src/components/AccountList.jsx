import React from 'react'
import PropTypes from 'prop-types'

export default class AccountList extends React.Component {
  static propTypes = {
    accounts: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props)
    this.state = {
      show: false,
    }
  }

  render() {
    const accounts = Object.keys(this.props.accounts).map(accountKey => {
      const account = this.props.accounts[accountKey]
      return `${account.number}\t${account.name}\t${account.type}\t${account.active ? '1' : '0'}`
    }).join("\n")

    return (
      <div className="accountList">
        {!this.state.show ? (
          <a onClick={() => {this.setState({show: true})}}>Vis liste over kontoer til kontrollfane i kontoplanen</a>
        ) : (
          <div>
            <a onClick={() => {this.setState({show: false})}}>Skjul liste</a>
            <textarea value={accounts} readOnly />
          </div>
        )}
      </div>
    )
  }
}
