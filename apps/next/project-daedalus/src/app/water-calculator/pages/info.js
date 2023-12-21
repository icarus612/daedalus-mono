import cx from 'classnames';
import Header from 'sections/header';

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

  
export default () => {

	return (
		<>
			<Header />
			<div className={cx(layout.container, layout.f_col_mob, layout.f_row, layout.f_wrap, layout.justify_center, layout.align_stretch, global.info_card)}>
				<div className={cx(layout.block_10, layout.block_12_mob, layout.text_center)}>
					<h1>Water Utility Calculator App</h1>
					<h4>A basic breakdown of how your bill is calculated. For more information visit <a target="_blank" href="https://charlottenc.gov/Water/RatesBilling/Pages/CLTWRates.aspx">Charlotte Water</a>.</h4>				
				</div>
				<div className={cx(layout.f_row, layout.f_wrap, layout.justify_center, layout.align_stretch, layout.block_12)}>
					<h3 className={cx(layout.block_10, layout.block_12_mob, layout.text_center)}>
						Universal Rates &amp; Fees
					</h3>
					<div className={cx(layout.block_5, layout.block_12_mob)}>
						<h4>Irrigation Meter Rates</h4>
						<ul>
							<li>Tier 1: (1-16 Ccf): $5.04</li>
							<li>Tier 2: (17+ CCf): $9.55</li>
						</ul>
					</div>
					<div className={cx(layout.block_5, layout.block_12_mob)}>
						<h4>Fixed Fees</h4>
						<ul>
							<li>Water: $4.22/month</li>
							<li>Sewer: $4.22/month</li>
						</ul>
					</div>
				</div>

				<div className={cx(layout.block_12_mob, layout.block_5)}>
					<h3>
						Residential Rates &amp; Fees
					</h3>
					<h4>Water Usage:</h4>
					<ul>
						<li>Tier 1 (1-4 Ccf ): $1.69/Ccf</li>
						<li>Tier 2 (5-8 Ccf): $2.18/Ccf</li>
						<li>Tier 3 (9-16 Ccf): $5.04/Ccf</li>
						<li>Tier 4 (Over 16 Ccf): $9.55/Ccf</li>
					</ul>
					<h4>Sewer Usage:</h4>
					<ul>
						<li>$5.19 Per Ccf of Water Used (up to 16 Ccf)</li>
					</ul>

					<h4>Availability Fees</h4>
					<ul>
						<li>Water 5/8" Connection Size: $1.29/month</li>
						<li>Water 1" Connection Size: $3.22/month</li>
						<li>Sewer 5/8" Connection Size: 8.70/month</li>
						<li>Sewer 1" Connection Size: $21.76/month</li>
					</ul>
				</div>

				<div className={cx(layout.block_12_mob, layout.block_5)}>
					<h3>
						Commercial Rates &amp; Fees
					</h3>
					<h4>Water and Sewer Usage:</h4>
					<ul>
						<li>Water Charge per Ccf: $2.92</li>
						<li>Sewer Charge per Ccf: $5.19</li>
					</ul>
					<h4>Water Availability Fees</h4>
					<ul>
						<li>Water 3/4" and 5/8" Connection Size: $1.29/month</li>
						<li>Water 1" Connection Size: $3.22/month</li>
						<li>Water 1 1/2" Connection Size: $6.45/month</li>
						<li>Water 2" Connection Size: $10.32/month</li>
						<li>Water 3" Connection Size: $21.28/month</li>
						<li>Water 4" Connection Size: $35.03/month</li>
						<li>Water 6" Connection Size: $70.92/month</li>
						<li>Water 8" Connection Size: $141.84/month</li>
						<li>Water 10" Connection Size: $270.76/month</li>
						<li>Water 12" Connection Size: $341.70/month</li>
					</ul>

					<h4>Sewer Availability Fees</h4>
					<ul>
						<li>Sewer 3/4" and 5/8" Connection Size: 8.70/month</li>
						<li>Sewer 1" Connection Size: $21.76/month</li>
						<li>Sewer 1 1/2" Connection Size: $43.52/month</li>
						<li>Sewer 2" Connection Size: $69.63/month</li>
						<li>Sewer 3" Connection Size: $143.61/month</li>
						<li>Sewer 4" Connection Size: $236.45/month</li>
						<li>Sewer 6" Connection Size: $478.70/month</li>
						<li>Sewer 8" Connection Size: $957.40/month</li>
						<li>Sewer 10" Connection Size: $1,828.00/month</li>
						<li>Sewer 12" Connection Size: $2,306.00/month</li>
					</ul>
				</div>
			</div>
		</>
	);
}

