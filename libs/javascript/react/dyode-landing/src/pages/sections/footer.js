import React, {useEffect} from "react";
import facebook from "../../assets/images/Group3.png";
import instagram from "../../assets/images/Group8.png";
import twitter from "../../assets/images/Group15.png";

const Footer = () => {
    const [width, setWidth] = React.useState(window.innerWidth);
    const breakpoint = 650;
    
    const openNav = (e) => {
        if (width < breakpoint) {
            let list = document.getElementById(e.target.dataset.value).querySelector("ul");
            list.style.marginTop = list.style.marginTop !== "0px" ? "0px" : `-${list.offsetHeight}px`;
        }
    }

    useEffect(()=> {
        window.addEventListener("resize", () => setWidth(window.innerWidth));
        [... document.querySelector(".footer").querySelectorAll(".collapsible")].map((e)=> {
            e.querySelector("ul").style.marginTop = "0px";
        });
    });

    return (
        <section className="footer">
            <div className="footer-links-left">
                <div>
                    <h4 className="title" data-value="l1" onClick={openNav}>Customer Service</h4>
                    <div className="collapsible" id="l1">
                        <ul>
                            <li><a href="#">Accessibility</a></li>
                            <li><a href="#">Contact Us</a></li>
                            <li><a href="#">Return Policy</a></li>
                            <li><a href="#">FAQ</a></li>
                            <li><a href="#">Gift Certificates</a></li>
                            <li><a href="#">Wishlist</a></li>
                        </ul>
                    </div>
                </div>
                <div>
                    <h4 className="title" data-value="l2" onClick={openNav}>Company</h4>
                    <div className="collapsible" id="l2">
                        <ul>
                            <li><a href="#">About Us</a></li>
                            <li><a href="#">Careers</a></li>
                            <li><a href="#">Press</a></li>
                            <li><a href="#">Affiliates</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div className="footer-links-right">
                <h4>Follow Us</h4>
                <div className="footer-links-right-img">
                    <img src={facebook} />
                    <img src={instagram} />
                    <img src={twitter} />
                </div>
            </div>
        </section>
    );
}

export default Footer;