import { useState, useEffect } from 'react';
import Link from 'next/link';
import cx from 'classnames';

import Input from 'components/input';
import Button from 'components/button';
import PriceBox from 'components/price-box';
import Header from 'sections/header';

import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default (props) => {
	const [water, setWater] = useState(0);
	const [sewer, setSewer] = useState(0);
	const [withSewer, setWithSewer] = useState(0);
	const [withoutSewer, setWithoutSewer] = useState(0);
	const [irrigation, setIrrigation] = useState(0);
	const [stormWater, setStormWater] = useState(0);
	const [subtotal, setSubtotal] = useState(0);
	const [meterSize, setMeterSize] = useState(.75);

	const rates = [1.69, 2.18, 5.04, 5.04, 9.55];

	const handleWithSewer = (e) => {
		let s = 5.19 * (e > 16 ? 16 : e);
		let x = 0;
		for (let i = 0; i < (Number(e) + Number(withoutSewer)); i++) {
			x += i < 16 ? rates[Math.floor(i / 4)] : rates[4];
		}
		setWithSewer(e);
		setWater(x);
		setSewer(s);
	}

	const handleWithoutSewer = (e) => {
		let x = 0;
		for (let i = 0; i < (Number(e) + Number(withSewer)); i++) {
			x += i < 16 ? rates[Math.floor(i / 4)] : rates[4];
		}
		setWithoutSewer(e);
		setWater(x);
	}

	const handleIrrigation = (e) => {
		let x = 0;
		for (let i = 0; i < e; i++) {
			x += i < 16 ? rates[3] : rates[4];
		}
		setIrrigation(x);
	}

	const stormWaterPrice = {
		"None": 0,
		"Tier 1": 7.57,
		"Tier 2": 10.77,
		"Tier 3": 15.44,
		"Tier 4": 25.02,
	}

	const meter = {
		"0.75": [1.29, 8.7],
		"1": [3.22, 21.76]
	};

	useEffect(() => {
		const availability = water > 0 &&
			(sewer > 0 ? meter[meterSize][0] + meter[meterSize][1] : meter[meterSize][0])
		setSubtotal(water + sewer + irrigation + stormWater + availability);
	}, [water, sewer, irrigation, stormWater, meterSize])
	return (
		<div className={cx(layout.f_row, layout.justify_center, layout.align_center, layout.f_wrap, layout.h100_vh, layout.w100_vw)}>
			<Header />
			<div className={cx(layout.block_12_mob, layout.block_8, global.info_card)}>
				<Link href="/">
					<span className={global.back_btn}>back</span>
				</Link>
				<div className={cx(global.card_content, layout.f_col, layout.justify_start, layout.align_start)}>
					<h3>
						Residential Rates
					</h3>
					<div className={layout.block_6}>
						<Button
							type="select"
							className="select"
							value={meterSize}
							options={[0.75, 1]}
							onChange={(e) => setMeterSize(e)}
						/>
						<span>Meter Size</span>
					</div>
					<div className={layout.block_6}>
						<Button
							type="select"
							className="select"
							options={["None", "Tier 1", "Tier 2", "Tier 3", "Tier 4"]}
							onChange={(e) => setStormWater(stormWaterPrice[e])}
						/>
						<span>Storm Water Runnoff</span>
					</div>
					<Input
						label="With Sewer"
						type="number"
						className={layout.block_6}
						placeholder={0}
						min={0}
						max={10000}
						onChange={(e) => handleWithSewer(e.target.value)}
					/>
					<Input
						label="Without Sewer"
						type="number"
						className={layout.block_6}
						placeholder={0}
						min={0}
						max={10000}
						onChange={(e) => handleWithoutSewer(e.target.value)}
					/>
					<Input
						label="Irrigation"
						type="number"
						className={layout.block_6}
						placeholder={0}
						min={0}
						max={10000}
						onChange={(e) => handleIrrigation(e.target.value)}
					/>
					<PriceBox
						sewerUsage={sewer > 0 && sewer}
						waterUsage={water > 0 && water}
						sewerFee={sewer > 0}
						waterFee={water > 0}
						meter={meter[meterSize]}
						irrigationUsage={irrigation > 0 && irrigation}
						stormWater={stormWater > 0 && stormWater}
						subtotal={subtotal}
						/>
				</div>
			</div>
		</div>
	)
}