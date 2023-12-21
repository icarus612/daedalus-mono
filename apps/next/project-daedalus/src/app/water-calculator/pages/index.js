import Link from 'next/link';
import Button from 'components/button';
import cx from 'classnames';
import Header from 'sections/header';

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default (props) => {
	return (
		<div className={cx(layout.f_col, layout.f_wrap, layout.h100_vh, layout.w100_vw)}>
			<Header />
			<div className={cx(global.first_card, layout.container, layout.f_col_mob, layout.f_row, layout.f_wrap, layout.justify_around, layout.align_stretch)}>
				<h1 className={cx(layout.block_12, layout.text_center)}>
					What Type of System do you have?
				</h1>
				<div className={cx(layout.block_12_mob, layout.block_5)}>
					<Link href="/residential">
						<div className={cx(layout.f_col, global.card, layout.align_center, layout.justify_start)}>
							<h3>
								Residential
							</h3>
							<p>
								Click here for Residential rates.
							</p>
							<Button className={global.basic} value="Residential" />
						</div>
					</Link>
				</div>
				<div className={cx(layout.block_12_mob, layout.block_5)}>
					<Link href="/commercial">
						<div className={cx(layout.f_col, global.card, layout.align_center)}>
							<h3>
								Commercial
							</h3>
							<p>
								Click here for commercial rates.
							</p>
							<Button className={global.basic} value="Commercial" />
						</div>
					</Link>
				</div>
			</div>
		</div>
	);
}