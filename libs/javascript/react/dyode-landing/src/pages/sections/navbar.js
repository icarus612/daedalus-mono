import React, {useEffect} from "react";
import logo from "../../assets/images/Logo.png"
import cart from "../../assets/images/Logo.png"
import navLines from "../../assets/images/Logo.png"

const PrimaryNavDesk = () => {
    return (
        <ul className="navbar">
            <li className="logo"><img src={logo} /></li>
            <li><a href="/Womens">Womens</a></li>
            <li><a href="/Mens">Mens</a></li>
            <li><a href="/Accessories">Accessories</a></li>
            <li><a href="/sale">Sale!</a></li>
        </ul>
    )
}

const PrimaryNavMob = () => {
    return (
        <div className="navbar">
            <img src={navLines} />
            <img src={logo} />
            <img src={cart} />
        </div>
    )
}

const NavBar = () => {
    const [width, setWidth] = React.useState(window.innerWidth);
    const breakpoint = 650;
  
    useEffect(()=> {
        window.addEventListener("resize", () => setWidth(window.innerWidth));
    });

    return (
        <div className="navigation">
            <div className="promo">
                <p>
                    FREE SHIPING ON ALL ORDERS OVER $75
                </p>
            </div>
            {width > breakpoint ? <PrimaryNavDesk /> : <PrimaryNavMob />}
        </div>
    );
}

export default NavBar;