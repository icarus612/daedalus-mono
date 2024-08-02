import React from 'react';
import {scrollBG} from '/modules/color-changer';
import HomeHeader from '/sections/home-header'
import HomeMiddle from '/sections/home-middle'
import AnimatedList from '/sections/animated-list'
import HomeContact from '/sections/home-contact'
import AnimatedListMobile from '/sections/animated-list-mobile'

class Home extends React.Component {

	constructor(props){
		super(props);
		this.state ={
			dotslist: (window.innerWidth > 700 ? <AnimatedList /> : <AnimatedListMobile />)
		}
	}
	componentDidMount(){
		anime({
			targets: ".throbber-inner",
			scale: .5,
			border: "2px",
			easing: "easeInCubic",
			direction: "alternate",
			loop: true,
			duration: 1500,
		})
		scrollBG(".color-change-bg", ["#9932CC", "#4B0082", "#9370DB", "#8068D8"], 3000)
		window.addEventListener('resize', ()=>  {
			this.setState({dotslist: (window.innerWidth > 700 ? <AnimatedList /> : <AnimatedListMobile />)});
		})
	}
	
	render(){
		
		return (
			<article id="home" className="overflow-hidden">
				<HomeHeader />
				<HomeMiddle />
				{this.state.dotslist}	
				<HomeContact />
			</article>
		);
	}
  
}

export default Home;