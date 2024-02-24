import React from "react";
// nodejs library that concatenates classes
import classNames from "classnames";
// @material-ui/core components
import withStyles from "@material-ui/core/styles/withStyles";
// @material-ui/icons
import { Link } from "react-router-dom";

// core components
import Header from "components/Header/Header.jsx";
import Footer from "components/Footer/Footer.jsx";
import Button from "components/CustomButtons/Button.jsx";
import GridContainer from "components/Grid/GridContainer.jsx";
import GridItem from "components/Grid/GridItem.jsx";
import HeaderLinks from "components/Header/HeaderLinks.jsx";
import Parallax from "components/Parallax/Parallax.jsx";


import studio1 from "assets/img/barracks.jpg";
import studio2 from "assets/img/israel.jpg";
import studio3 from "assets/img/library.jpg";
import studio4 from "assets/img/tank1.jpg";
import studio5 from "assets/img/Tabernacle.jpg";
import studio6 from "assets/img/tempMount.jpg";
import studio7 from "assets/img/tank2.jpg";
import studio8 from "assets/img/decOfIndp.jpg";



import profilePageStyle from "assets/jss/material-kit-react/views/profilePage.jsx";

class GalleryPage extends React.Component {
  render() {
    const { classes, ...rest } = this.props;
    const imageClasses = classNames(
      classes.imgRaised,
      classes.imgRoundedCircle,
      classes.imgFluid
    );
    const navImageClasses = classNames(classes.imgRounded, classes.imgGallery);
    return (
      <div>
        <Header
          color="transparent"
          brand="The Wilderness Tabernacle of Witness"
          rightLinks={<HeaderLinks />}
          fixed
          changeColorOnScroll={{
            height: 200,
            color: "white"
          }}
          {...rest}
        />
        <Parallax small filter image={require("assets/img/oldromanianbible.jpg")} />
        <div className={classNames(classes.main, classes.mainRaised)}>
          <div>
          <br />
          <br />
          <br />

            <div className={classes.container}>
              <GridContainer justify="center">
                <GridItem xs={12} sm={12} md={10}>
                  <div className={classes.profile}>

                    <div className={classes.name}>
                      <h3 className={classes.title}>Museum Library</h3>
                      <br />
                    </div>
                  </div>
                </GridItem>
              </GridContainer>
              <div className={classes.description}>
                <p>
                The Museum Library collection includes over 1500 religious publications dating back to the early 1800s
                </p>
              </div>
              <GridContainer justify="center">
                <GridItem xs={12} sm={12} md={11} lg={11} className={classes.navWrapper}>

                          <GridContainer justify="center">
                            <GridItem xs={12} sm={12} md={4}>
                            <a  href={studio3}>
                            <img
                              alt="..."
                              src={studio3}
                              className={navImageClasses}
                            /></a>
                            <h4>Museum Library</h4>
                            <p>The Museum Library collection includes over 1500 religious publications dating back to the early 1800s </p>
                            <hr />
                            <br />
                            <a  href={studio2}>
                              <img
                                alt="..."
                                src={studio2}
                                className={navImageClasses}
                              /></a>
                              <h4>Land of Isreal</h4>
                              <p>The struggle to establish a home for the Jewish people began in earnest with the Balfour Declaration of July 18, 1917. </p>
                              <hr />
                              <br />
                              <a  href={studio7}>
                              <img
                                alt="..."
                                src={studio7}
                                className={navImageClasses}
                              /></a>
                              <h4>Study Tank</h4>
                              <p class="text-muted">
                              The Tank provides an excellent place to study and store old books.  It remains at a relative constant temperature and humidity.  Pages of older books contain a high level of acid which makes them susceptible to deterioration in the presence of moisture and heat.</p>
                              <hr />
                              <br />
                            </GridItem>
                            <GridItem xs={12} sm={12} md={4}>
                            <a  href={studio4}>
                            <img
                              alt="..."
                              src={studio4}
                              className={navImageClasses}
                            /></a>
                            <h4>Tank Stairwell</h4>
                            <p>The underground Study Tank, located underneath the Museum is an 8,000 gallon steel tank covered with fiberglass measuring 22 feet long and 8 feet in diameter.</p>
                            <hr />
                            <br />
                            <a  href={studio1}>
                            <img
                              alt="..."
                              src={studio1}
                              className={navImageClasses}
                            /></a>
                            <h4>Auschwitz Barracks</h4>
                        		<p>When most people think of Israel they think of the Holocaust. The word Holocaust is a Greek word that means a whole burnt offering.</p>
                            <hr />
                            <br />
                            </GridItem>
                            <GridItem xs={12} sm={12} md={4}>
                            <a  href={studio8}>
                            <img
                              alt="..."
                              src={studio8}
                              className={navImageClasses}
                            /></a>
                            <h4>Declaration of Independence</h4>
                            <p >Giving the natural right of the Jewish people to be masters of their own fate, like all other nations, in their own sovereign State.</p>
                            <hr />
                            <br />
                            <a  href={studio5}>
                              <img
                                alt="..."
                                src={studio5}
                                className={navImageClasses}
                              /></a>
                              <h4>Tabernacle Replica</h4>
                              <p >A to-scale model replica of the Wilderness Tabernacle!</p>
                              <hr />
                              <br />
                              <a  href={studio6}>
                              <img
                                alt="..."
                                src={studio6}
                                className={navImageClasses}
                              /></a>
                              <h4>Temple Mount</h4>
                              <p >The first picture on top shows the Temple Mount as it is today with the gold Dome of the Rock currently in the location where the Third Temple will be constructed.</p>
                              <hr />
                              <br />
                            </GridItem>
                          </GridContainer>

                </GridItem>
              </GridContainer>
            </div>
          </div>
        </div>
        <Footer />
      </div>
    );
  }
}

export default withStyles(profilePageStyle)(GalleryPage);
