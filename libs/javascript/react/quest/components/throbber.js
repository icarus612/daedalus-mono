import { useEffect, forwardRef} from 'react'
import cx from 'classnames'
import anime from 'animejs';

import local from 'styles/components/throbber.module.scss'

export default forwardRef((props, ref)=> {
		const {
			placement="top",
			mobile=false,
		} = props

	useEffect(() => {
    anime({
			targets: `.${local.inner}`,
			scale: .5,
			border: "2px",
			easing: "easeInCubic",
			direction: "alternate",
			loop: true,
			duration: 1500
		});
	});

	return (
		<div className={cx(local[placement], {[local[mobile]]: mobile})} ref={ref}>
			<div className={local.inner}></div>
		</div>
	)
})

