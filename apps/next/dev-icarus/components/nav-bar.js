import React from 'react';

let NavBar = (props) => {
	return (
		<nav>
			<div className="flex flex-row justify-end items-center">
				<a href="/">Home</a> |
				<a href="/get-quote">Get Quote</a> |
				<a href="/contact-us">Contact Us</a>
			</div>
		</nav>

	)
}
export default NavBar;