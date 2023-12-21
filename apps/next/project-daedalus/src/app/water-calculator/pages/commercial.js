import { useEffect, useState } from 'react';
import Link from 'next/link';
import cx from 'classnames';

import Input from 'components/input';
import Button from 'components/button';
import PriceBox from 'components/price-box';
import Header from 'sections/header';

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default (props) => {
	const [meterSize, setMeterSize] = useState(.75);
	const [usage, setUsage] = useState(0);
	const [subtotal, setSubtotal] = useState(0);
	const [irrigation, setIrrigation] = useState(0);
	const [sewer, setSewer] = useState(false);
	const meter = {
		"0.75": [1.29, 8.7],
		"1": [3.22, 21.76],
		"1.5": [6.45, 43.52],
		"2": [10.32, 69.63],
		"3": [21.28, 143.61],
		"4": [35.03, 236.45],
		"6": [70.92, 478.7],
		"8": [141.84, 957.4],
		"10": [270.76, 1828],
		"12": [341.7, 2306]
	};


	const handleIrrigation = (e) => {
		let x = 0;
		for (let i = 0; i < e; i++) {
			x += i < 16 ? 5.04 : 9.55;
		}
		return Number(x);
	}

	const setPrice = ({ u = usage, ms = meterSize, i = irrigation, s = sewer }) => {
		setIrrigation(i);
		setSewer(s);
		setUsage(u);
		setMeterSize(ms);
	}

	useEffect(() => {
		const newSewer = sewer ? 8.01 : 2.92;
		const h = handleIrrigation(irrigation);
		const availability = usage > 0 &&
			(sewer ? meter[meterSize][0] + meter[meterSize][1] : meter[meterSize][0])

		setSubtotal(
			usage + h > 0 ?
				(Number(usage) * newSewer) + Number(h) + availability
				: 0
		);
	}, [meterSize, usage, irrigation, sewer])

	return (
		<div className={cx(layout.f_row, layout.justify_center, layout.align_center, layout.f_wrap, layout.h100_vh, layout.w100_vw)}>
			<Header />
			<div className={cx(layout.block_12_mob, layout.block_8, global.info_card)}>
				<Link href="/">
					<span className={global.back_btn}>back</span>
				</Link>
				<div className={cx(global.card_content, layout.f_col, layout.justify_start, layout.align_start)}>
					<h3>
						Commercial Rates
					</h3>
					<Input 
						label="Sewer?" 
						type="checkbox" 
						className={cx(layout.block_6, layout.align_center, layout.f_row)} 
						value={sewer} 
						onChange={() => setPrice({ s: !sewer })} 
					/>
					<div className={layout.block_6}>
						<Button
							type="select"
							className="select"
							value={meterSize}
							options={[0.75, 1, 1.5, 2, 3, 4, 6, 8, 10, 12]}
							onChange={(e) => setPrice({ ms: e })}
						/>
						<span>Meter Size</span>
					</div>
					<Input
						label="Water Usage"
						type="number"
						className={layout.block_6}
						placeholder={0}
						min={0}
						max={10000}
						onChange={(e) => setPrice({ u: Number(e.target.value) })}
					/>
					<Input
						label="Irrigation"
						type="number"
						className={layout.block_6}
						placeholder={0}
						min={0}
						max={10000}
						onChange={(e) => setPrice({ i: Number(e.target.value) })}
					/>
					<PriceBox
						sewerFee={usage > 0 && sewer}
						waterFee={usage > 0}
						meter={meter[meterSize]}
						irrigationUsage={irrigation > 0 && handleIrrigation(irrigation)}
						waterUsage={usage > 0 && (usage * 2.92)}
						sewerUsage={(sewer && usage > 0) && (usage * 5.19)}
						subtotal={subtotal > 0 ? subtotal : 0}
					/>
				</div>
			</div>
		</div>
	)
}