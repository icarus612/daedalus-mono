import cx from 'classnames'

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default(props) => {
  const {
    pulsar,
    title,
    description
  } = props
  return (
    <div className={cx(global.card, layout.block_7)}>
      <div className={global.throbber}>
        <div className={pulsar}></div>
      </div>
      <div>
        <h4>{title}</h4>
        <p>{description}</p>
      </div>
    </div>
  )
}
