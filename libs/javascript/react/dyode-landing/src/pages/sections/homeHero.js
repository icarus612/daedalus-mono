import React, { useEffect } from "react";
import Flickity from 'flickity';
import image1 from '../../assets/images/HeroImage1.jpg';
import image2 from '../../assets/images/HeroImage2.jpg';
import image1Mob from '../../assets/images/HeroImage1Mobile.jpg';
import image2Mob from '../../assets/images/HeroImage2Mobile.jpg';

const HomeHero = () => {
    const [width, setWidth] = React.useState(window.innerWidth);
    const breakpoint = 650;
  
    useEffect(()=> {
        let flkty = new Flickity('.hero-flickity', {
            wrapAround: true,
            cellAlign: 'left',
            setGallerySize: false,
            prevNextButtons: false,
            lazyLoad: 0,
            freeScroll: true,
            draggable: true
        });
        window.addEventListener("resize", () => setWidth(window.innerWidth));
    });
    let imageDif = [image1, image2],
        imageDifMob = [image1Mob, image2Mob],
        flickityGal = [];

    for (let i = 0; i < 4; i++) {
        flickityGal.push(
            <div key={i} className="hero-cell">
                <img src={width > breakpoint ? imageDif[i % 2] : imageDifMob[i % 2]} />
            </div>
        )
    }
    return (
        <section className="hero">
            <div className="hero-flickity">
                {flickityGal.map((i)=>  i)}
            </div>
            <div className="hero-container">
                <h1 className="hero-title">Title Goes Here</h1>
                <h2 className="lato">Tagline will go right here</h2>
                <button className="hero-button">SHOP NOW</button>
            </div>
        </section>
    );
}

export default HomeHero;