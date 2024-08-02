import React from 'react';
import '../assets/css/application.scss';
import NavBar from './sections/navbar.js';
import HomeHero from'./sections/homeHero.js';
import Collections from'./sections/collections.js';
import Products from'./sections/products.js';
import ShopNow from'./sections/shopNow.js';
import InstaReel from'./sections/instaReel.js';
import Subscribe from'./sections/subscribe.js';
import Footer from'./sections/footer.js';



const Home = () => {

	return (
		<div>
			<NavBar />
			<HomeHero />
			<Collections />
			<Products />
			<ShopNow />
			<InstaReel />
			<Subscribe />
			<Footer />
		</div>
	)
}

export default Home;
