import cx from 'classnames';


const Input = (props) => {
	const {
		className="",
		id,
		type,
		value,
		placeholder,
		max,
		min,
		labelBefore=false,
		required=false,
		label,
		onChange,
		checked
	} = props

	return (
		<label className={className} id={id} value={type !== "text" && value}>
			{labelBefore && label}
			<input
				type={type}
				className={labelBefore ? 'ml-2' : 'mr-2'}
				onChange={onChange}
				checked={checked}
				required={required}
				max={max}
				min={min}
				value={value}
				placeholder={placeholder}
				id={id}
			/>
			{labelBefore ? null : label}
		</label>
	)
}
export default Input;