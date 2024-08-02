import React from "react";
import icon from "../../assets/images/EmailIcon.png"
const Subscribe = () => {
    return (
        <section className="subscribe">
            <div className="h2-wrapper">
                <img src={icon} /><h2>Sign up &amp; Stay Connected</h2>
            </div>
            <div className="subscribe-container">
                <div className="subscribe-box">
                    <p>Sign up for the newsletter and get 20% off! Gain access to exclusive offers and be the first to know when new stuff drops!</p>
                </div>
                <div className="subscribe-box">
                    <input type="text" placeholder="Your Email Address" />
                    <input type="submit" value="Subscribe" />
                </div>      
            </div>
        </section>

    );
}

export default Subscribe;