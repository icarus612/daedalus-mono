import { useEffect } from 'react';
import cx from 'classnames'

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

import { catapult } from 'modules/catapult.js';

export default (props) => {

	useEffect(() => {
		catapult({
			_start: global.pulsar8,
			_middle: global.pulsar7,
			_end: global.top_throbber,
			_wall: global.step4,
			_path: global.path_bottom,
			catapultItem: global.catapult,
			pulse1: global.pulsar1, 
			mv_5: global.mv_5,
			catapultThrobber: global.catapult_throbber
		});
	})

	return (
		<div className={cx(global.content_middle, layout.container, layout.f_col, layout.justify_center, layout.align_end)}>
			<div className={cx(layout.block_8, global.step2, global.path_top, global.position_relative)}>
				<div className={global.hidden_block} />
			</div>
			<div className={cx(layout.f_col, layout.justify_center, layout.align_end, global.position_relative, layout.block_12)}>
				<div className={cx(global.throbber, global.catapult_throbber)}>
					<div className={cx(global.throbber_inner, global.pulsar8)}></div>
					<div className={cx(global.catapult)}></div>
					<div className={cx(global.animated_dot2, global.mv_5)}></div>
				</div>
				<div className={layout.block_3}>
					<div className={global.step3}></div>
				</div>
				<div className={cx(layout.block_5, global.position_relative)}>
					<div className={cx(global.step4)}>
						<div className={cx(global.throbber, global.wheel_end_throbber)}>
							<div className={cx(global.throbber_inner, global.pulsar7)}></div>
						</div>
					</div>
				</div>
				<div className={cx(layout.f_col, layout.justify_center, layout.align_start, layout.block_12)}>
					<div className={cx(layout.block_10, global.step2,  global.path_bottom)}>
						<div className={global.hidden_block} />
					</div>
				</div>
			</div>
		</div>
	)
}

