import { useEffect, useRef } from 'react'
import dotsMovement from 'modules/dots.js'

import global from 'styles/global.module.scss'

const debounce = (func, wait) => {
	let timeout;
	return function executedFunction(...args) {
		const later = () => {
			timeout = null
			func(...args)
		};
		clearTimeout(timeout)
		timeout = setTimeout(later, wait)
	};
};

const Swoosh = (props) => {
	const {
		startElement,
		endElement,
		dots=5,
		height=300,
		width,
	} = props
	const swoosh = useRef(null)
	
	useEffect(() => {
		debounce(dotsMovement({
			el: swoosh, 
			start: startElement.current, 
			end: endElement.current, 
			time: 1000, 
			curve: "cubicX", 
			color: ["#009de4", "#06f3a0", "#f30659"]
		}), 100)
  }, [startElement.current, endElement.current]);    

	return (
		<div style={{height: height + "px"}} ref={swoosh}>
			{[...Array(dots)].map((_, i)=> <div key={i} className={global.dot} />)}
		</div>
	)
}

export default Swoosh;