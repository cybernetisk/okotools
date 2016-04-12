import React from 'react'

export default class ProjectFilter extends React.Component {
  static propTypes = {
    currentFilter: React.PropTypes.any,
    onChange: React.PropTypes.func.isRequired,
    projects: React.PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props)
    this.handleSelection = this.handleSelection.bind(this)

    console.log(props)
  }

  handleSelection(ev) {
    if (ev.target.value === '-1') {
      this.props.onChange(null)
    } else if (ev.target.value === '0') {
      this.props.onChange(false)
    } else {
      this.props.onChange(this.props.projects[ev.target.value])
    }
  }

  renderTree(node, prefix='') {
    return node.children.reduce((prev, cur) => {
      prev.push(
        <option key={cur.id} value={cur.id}>{prefix}{cur.title}</option>
      )

      prev = prev.concat(this.renderTree(cur, prefix + '.. '))
      return prev
    }, [])
  }

  render() {
    const currentFilter = this.props.currentFilter ? this.props.currentFilter.id : (this.props.currentFilter === false ? '0' : '-1')

    return (
      <span className="form-inline">
        <select className="form-control" onChange={this.handleSelection} value={currentFilter}>
          <option value="-1">Vis alt</option>
          <option value="0">Føringer som mangler prosjekt</option>
          {this.renderTree(this.props.projects[0])}
        </select>
      </span>
    )
  }
}
