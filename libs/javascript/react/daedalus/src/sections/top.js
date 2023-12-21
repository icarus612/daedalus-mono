import { useEffect } from 'react'
import cx from 'classnames'
import anime from 'animejs'
import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'
import { firstAnimation } from 'modules/first-animation.js';

const Top = (props) => {
	useEffect(() => {
		anime({
			targets: `.${global.first_throbber} .${global.throbber_inner}`,
			scale: 1.6,
			border: "0px",
			easing: "easeInCubic",
			direction: "alternate",
			loop: true,
			duration: 1500,
		});
		firstAnimation({
			_start: global.first_throbber,
			_end: global.catapult_throbber,
			mv_2: global.second_throbber,
			_spring: global.spring,
			container: global.content_top,
			bouncePath: global.path_top,
			mv_6: global.mv_6,
			startPulsar: global.pulsar6
		});
	});

	return (
		<div className={cx(global.content_top, layout.container, layout.f_row, layout.f_wrap)}>
			<div className={cx(layout.block_4, global.position_relative, global.top_box, layout.text_center)}>
				<h1>
					Quest: A Creative Landing Page Theme For Easy Use
				</h1>
				<h3>
					TL;DR: Scroll through to see some cool interactive and reactive Javascript.
				</h3>
				<h5>
					A Project Icarus Design
				</h5>
				<div className={cx(global.throbber, global.first_throbber)}>
					<div className={cx(global.animated_dot2, global.mv_6)}></div>
					<div className={cx(global.throbber_inner)}></div>
				</div>
			</div>
			<div className={cx(layout.block_6)} />
			<div className={cx(layout.block_1, global.position_relative)}>
				<div className={cx(global.throbber, global.second_throbber)}>
					<div className={cx(global.throbber_inner, global.pulsar6)}></div>
				</div>
			</div>
			<div className={cx(layout.block_10, global.hidden_block)} />
			<div className={cx(layout.block_10, global.hidden_block)} />
			<div className={cx(layout.block_1, global.position_relative)}>
				<div className={global.spring}></div>
			</div>
		</div>
	)
}
export default Top;