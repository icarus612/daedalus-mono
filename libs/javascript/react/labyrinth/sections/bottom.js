import { useEffect } from 'react';
import cx from 'classnames'

import { animateLI } from 'modules/list-item.js';
import Card from 'components/card';

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default (props) => {

	useEffect(() => {
		animateLI({
			dot: global.animated_dot,
			topThrobber: global.top_throbber,
			midThrobber: global.mid_throbber,
			listStart: global.pulsar2,
			li1: global.animated_li1,
			li2: global.animated_li2,
			li3: global.animated_li3,
			mv1: global.mv_1,
			mv2: global.mv_2,
			mv3: global.mv_3,
		});
	})

	return (
		<div className={cx(global.content_bottom, layout.container)}>
			<div className={cx(layout.f_row, layout.f_wrap, layout.justify_center, layout.align_stretch, global.position_relative)}>
				<div className={cx(layout.block_12)}>
					<div className={global.hidden_block} />
				</div> 
				<div className={cx(layout.block_2)}>
					<div className={cx(global.throbber, global.top_throbber)}>
						<div className={cx(global.throbber_inner, global.pulsar1)} />
						<div className={cx(global.animated_dot, global.mv_1)}></div>
						<div className={cx(global.animated_dot, global.mv_2)}></div>
						<div className={cx(global.animated_dot, global.mv_3)}></div>
					</div>
				</div>
				<div className={cx(layout.block_10, global.step2)}>
					<div className={global.hidden_block} />
				</div> 
			</div>

			<div className={cx(layout.f_col, layout.justify_center, layout.align_end, global.position_relative)}>
				<div className={cx(global.throbber, global.mid_throbber)}>
					<div className={cx(global.throbber_inner, global.pulsar2)}></div>
				</div>
				<Card
					title="Speed"
					description="
					Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin et risus sapien. Aliquam tempus sapien non laoreet posuere. Fusce dolor nulla, interdum ultricies quam vitae, sagittis interdum enim. Nulla a nunc enim. Vestibulum mollis sodales tincidunt. Nulla ullamcorper dui quis magna feugiat, vel fringilla libero tristique. Nulla aliquet aliquam nisl, et aliquam nibh lacinia quis.    
					"
					pulsar={cx(global.throbber_inner, global.animated_li1)}
				/>
				<Card
					title="Depth"
					description="
					Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin et risus sapien. Aliquam tempus sapien non laoreet posuere. Fusce dolor nulla, interdum ultricies quam vitae, sagittis interdum enim. Nulla a nunc enim. Vestibulum mollis sodales tincidunt. Nulla ullamcorper dui quis magna feugiat, vel fringilla libero tristique. Nulla aliquet aliquam nisl, et aliquam nibh lacinia quis.    
					"
					pulsar={cx(global.throbber_inner, global.animated_li2)}
				/>
				<Card
					title="Functionality"
					description="
					Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin et risus sapien. Aliquam tempus sapien non laoreet posuere. Fusce dolor nulla, interdum ultricies quam vitae, sagittis interdum enim. Nulla a nunc enim. Vestibulum mollis sodales tincidunt. Nulla ullamcorper dui quis magna feugiat, vel fringilla libero tristique. Nulla aliquet aliquam nisl, et aliquam nibh lacinia quis.    
					"
					pulsar={cx(global.throbber_inner, global.animated_li3)}
				/>
			</div>
		</div>
	)
}