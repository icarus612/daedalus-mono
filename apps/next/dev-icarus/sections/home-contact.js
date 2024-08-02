import React from 'react';
import Button from '../components/button.js';

const HomeContact = (props) => {
	return (
		<section className="py-5 position-relative overflow-hidden pt-5" id='contactMe'>
			<div className="container">
				<div className="col-12 py-md-3 text-center text-white my-4">
					<h3 className="my-4 dark">
						Like what you see? Contact us or get an online quote.
					</h3>
					<div className="d-flex flex-column flex-md-row justify-content-between align-items-around">
						<div className="my-4 col-12 dark">
							<Button size='lg' link="/contact-us">Contact Us</Button>
							<Button size='lg' link="/get-quote">Get Quote</Button>
						</div>
					</div>
				</div>

			</div>
		</section>
	)
}

export default HomeContact;