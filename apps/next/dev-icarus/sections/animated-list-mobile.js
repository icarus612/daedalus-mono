import React from 'react';
import { PulseCardMobile } from '../components/card.js';
import { animateLIMobile } from '../../assets/js/listItemMobile.js';

export default class AnimatedListMobile extends React.Component {
	componentDidMount() {
		animateLIMobile();
	}

	render() {
		return (
			<section className="background-dotsLI px-5 flex-nowrap d-flex flex-column pb-5 text-left overflow-visible" id="list-dot-outer">

				<div className="container" id="list-dot-start">
					<div className="d-flex flex-column flex-nowrap justify-content-start align-items-stretch" >


						<div className="col-12 py-5 text-left">
							<h3 className="">
								A little more on node.js, and why <span style={{ 'textDecoration': 'line-through' }} >its better</span> we use it.
							</h3>
						</div>
						<div className='col-12'>
							<div className="throbber li-throbber-start mobile">
								<div className="throbber-inner pulse1"></div>
							</div>
						</div>
					</div>

					<div className="animated-dot mv-1"></div>
					<PulseCardMobile
						title="Speed"
						description="
							Building sits off Google Chrome's node.js runtime allows for sites to be built on the back end and use much more javascript than before. 
							Using frameworks like react sites are built optimal for load speeds, and javascript animations load faster and are more interactive than video's or gif's. 
            "
						pulsar="throbber-bullets pulse3"
						mobile='left'
					/>
					<div className="animated-dot mv-2"></div>

					<PulseCardMobile
						title="Depth"
						description="
              Building sites that maxamize the use of functional languages like JavaScript, 
							and not just static HTML and CSS, can lead to more dynamic and interactive sites. 
							This is also how more complex sites, like ecommerce or sites that require user to login's.
            "
						pulsar="throbber-bullets pulse4"
						mobile='right'
					/>
					<div className="animated-dot mv-3"></div>
					<PulseCardMobile
						title="Functionality"
						description="
              From the more complex asspects of web development (ie. ecommerce, user login, encryption and databases), 
							to the basic nesesities, like contact forms, carousels, search bars, ect. 
							Javascript is responsible for most if not all of your sites functionality. 
            "
						pulsar="throbber-bullets pulse5"
						mobile='left'
					/>
					<div className="animated-dot mv-4"></div>


				</div>
			</section>
		)
	}
}