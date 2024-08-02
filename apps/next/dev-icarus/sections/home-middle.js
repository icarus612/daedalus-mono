import React from "react";
import Throbber from '../components/throbber.js';
import Swoosh from '../components/swoosh.js';
import quest from '../../assets/images/quest.png';
import daedalus from '../../assets/images/daedalus.png';
import Button from '../components/button.js'

export default class HomeMiddle extends React.Component {
    constructor(props){
		super(props);
		
	}
    render(){
        return(
            <section className="overflow-visible">
				<div  className="color-change-bg">
					<div className="container d-flex flex-row flex-wrap align-items-center justify-content-center crazy-container" >
						<div className="col-none col-md-4 d-lg-6"></div>
						<div className="col-12 col-md-8 col-lg-6">
							<div className="purple-gradient d-flex flex-column p-5 text-left overflow-visible">
								<h1 className="my-4">
									Need web development? We Can Help. 
								</h1>
								<h2 className="my-4">
									Scroll through to learn more about what sets apart. 
								</h2>
								<div className="d-flex flex-column flex-md-row justify-content-between align-items-around">
									<div className="my-4 col-12 dark">
										<Button simple size='lg' link="/contact-us">Contact Us</Button>
										<Button size='lg' link="/get-quote">Get Quote</Button>
									</div>
								</div>
							</div>
							<Throbber bottom id="first" mobile="right" />
						</div>
						<Swoosh id="mv1" startEl="#first" endEl="#second" />
						<div className="col-12 col-md-8 col-lg-6">
							<Throbber top id="second" mobile="left" />
							<div className="purple-gradient d-flex flex-column p-5 text-left overflow-visible">
								<h3 className="bold">
									How we differ.
								</h3>
								<h2 className="text-blue">
									JavaScript
								</h2>
								<p>
									Javascript as far as the eye can see. These arn't some basic wordpress sites, we use JavaScript to build things from animations, using anime.js, to full sites, using things like react.js, graphQL, and Gatsby. Not understanding any of this? Thats ok, heres an easier breakdown. Basic websites use things like wordpress or html and css to build their sites, and those things are great for building basic sites. Think of them like brick, wood, paint and furnature. Like building a house, but javascript is like the electricity, and your apliances. Javascript can also use libraries, like the ones mentioned before, to build interactive animations and full sites.
								</p>
								<p className="bold">
									Check out these animated demo landing pages.
								</p>
							</div>
							<Throbber bottom id="third" mobile="left" />
						</div>
						<div className="col-md-4 d-lg-none"></div>
						<div className="col-6 col-md-4 col-lg-3">
							<div className="card hover">
								<a href="https://quest.devicarus.com" target="_blank" > 
									<img className="image" src={quest} />
								</a>
							</div>
						</div>
						<div className="col-6 col-md-4 col-lg-3">
							<div className="card hover">
								<a href="https://daedalus.devicarus.com" target="_blank" > 
									<img className="image" src={daedalus} />
								</a>
							</div>
						</div>
						<Swoosh id="mv2" startEl="#third" endEl="#fourth" />
						<div className="col-none col-md-4 d-lg-6"></div>
						<div className="col-12 col-md-8 col-lg-6">
							<Throbber top id="fourth" mobile="right" />
							<div className="purple-gradient d-flex flex-column p-5 text-left overflow-visible">
								<h3 className="bold">
									A little more on node.js, and why its better we use it.
								</h3>
								
							
							</div>
						</div>
					</div>
				</div>
			</section>
        )
    }
}