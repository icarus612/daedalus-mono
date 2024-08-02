import React, { useEffect } from "react";
import social1 from "../../assets/images/Social1.jpg";
import social2 from "../../assets/images/Social2.jpg";
import social3 from "../../assets/images/Social3.jpg";
import social4 from "../../assets/images/Social4.jpg";
import social5 from "../../assets/images/Social5.jpg";

const InstaDesk = () => {
    return (
        <div className="insta-container">
            <img className="insta-image" src={social1}></img>
            <img className="insta-image" src={social2}></img>
            <img className="insta-image" src={social3}></img>
            <img className="insta-image" src={social4}></img>
            <img className="insta-image" src={social5}></img>
        </div>
    )
}


const InstaMob = () => {
    return (
        <div className="insta-container">
            <img className="insta-image" src={social1}></img>
            <img className="insta-image" src={social2}></img>
            <img className="insta-image" src={social3}></img>
        </div>
    )
}

const InstaReel = () => {
    const [width, setWidth] = React.useState(window.innerWidth);
    const breakpoint = 1100;

    useEffect(()=> {
        window.addEventListener("resize", () => setWidth(window.innerWidth));
    });

    return (
        <section className="insta container">
            <h1 className="insta-title">Follow us on Instagram!</h1>
            { width > breakpoint ? <InstaDesk /> : <InstaMob /> }
        </section>
    );
}

export default InstaReel;