import layout from 'styles/layout.module.scss'
import global from 'styles/global.module.scss'

export default (props) => {
	let subtotal = Number(props.subtotal)
	if (props.sewerUsage) subtotal += 4.22
	if (props.waterUsage) subtotal += 4.22
	return (
		<div className={global.price_card}>
			{props.waterUsage && (
				<h4>
					Water Usage:  <span className={global.float_right}>$ {props.waterUsage.toFixed(2)}</span>
				</h4>	
			)}
			{props.waterUsage && (
				<h4>
					 Water Fixed Fees:  <span className={global.float_right}>$ 4.22</span>
				</h4>	
			)}
			{props.meter && (props.waterFee || props.irrigationUsage) && (
				<h4>
					Water Availability Fee:  <span className={global.float_right}>$ {props.meter[0].toFixed(2)}</span>
				</h4>	
			)}
			{(props.waterUsage || props.waterFee) && (props.sewerUsage || props.sewerFee || props.irrigationUsage || props.stormWater) && <hr />}
			{props.sewerUsage && (
				<h4>
					Sewer Usage:  <span className={global.float_right}>$ {props.sewerUsage.toFixed(2)}</span>
				</h4>	
			)}
			{props.sewerUsage && (
				<h4>
					Sewer Fixed Fees:  <span className={global.float_right}>$ 4.22</span>
				</h4>	
			)}
			{props.sewerFee && (
				<h4>
					Sewer Availability Fee:  <span className={global.float_right}>$ {props.meter[1].toFixed(2)}</span>
				</h4>	
			)}
			{(props.irrigationUsage || props.stormWater) && (props.sewerUsage || props.sewerFee) && <hr />}
			{props.irrigationUsage && (
				<h4>
					Irrigation Usage:  <span className={global.float_right}>$ {props.irrigationUsage.toFixed(2)}</span>
				</h4>	
			)}
			{props.stormWater && (
				<h4>
					Storm Water Runnoff:  <span className={global.float_right}>$ {props.stormWater.toFixed(2)}</span>
				</h4>	
			)}
			<hr />
			<h4>
				Subtotal:  <span className={global.float_right}>$ {subtotal.toFixed(2)}</span>
			</h4>				
		</div>
	);
}
