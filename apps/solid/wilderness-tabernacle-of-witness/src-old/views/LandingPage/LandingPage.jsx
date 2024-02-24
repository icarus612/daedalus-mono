import React from "react";
// nodejs library that concatenates classes
import classNames from "classnames";
// @material-ui/core components
import withStyles from "@material-ui/core/styles/withStyles";

// @material-ui/icons

// core components
import Header from "components/Header/Header.jsx";
import Footer from "components/Footer/Footer.jsx";
import GridContainer from "components/Grid/GridContainer.jsx";
import GridItem from "components/Grid/GridItem.jsx";
import Button from "components/CustomButtons/Button.jsx";
import HeaderLinks from "components/Header/HeaderLinks.jsx";
import Parallax from "components/Parallax/Parallax.jsx";
import lawProphesied from "assets/Stories/AAATheLawProphesied.pdf";

import landingPageStyle from "assets/jss/material-kit-react/views/landingPage.jsx";

// Sections for this page
import ProductSection from "./Sections/ProductSection.jsx";
import TeamSection from "./Sections/TeamSection.jsx";
import WorkSection from "./Sections/WorkSection.jsx";

const dashboardRoutes = [];

class LandingPage extends React.Component {
  render() {
    const { classes, ...rest } = this.props;
    return (
      <div>
        <Header
          color="transparent"
          routes={dashboardRoutes}
          brand="The Wilderness Tabernacle of Witness"
          rightLinks={<HeaderLinks />}
          fixed
          changeColorOnScroll={{
            height: 400,
            color: "white"
          }}
          {...rest}
        />
        <Parallax filter image={require("assets/img/bg4.jpg")}>
          <div className={classes.container}>
            <GridContainer>
              <GridItem xs={12} sm={12} md={9}>
                <h1 className={classes.title}>A CONSISTENT NEW TESTAMENT</h1>
                <h4>
                  This is the only translation that I have ever seen or heard of in which the translator, Ralph Mount, made a dictionary and card file of each Greek word in the New Testament before he made the translation.  There are 4,839 words in the Greek New Testament.  2,389 of these words only appear two times or less.  This work was the result of a lifetime of study and work by Ralph H. Mount, now with the Lord.  If you are a student of the Word, you will see the benefit of this tremendous work.
                </h4>
                {/*<br />
                <Button
                  color="danger"
                  size="lg"
                  href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <i className="fas fa-play" />Watch video
                </Button>*/}
              </GridItem>
            </GridContainer>
          </div>
        </Parallax>
        <div className={classNames(classes.main, classes.mainRaised)}>
          <div className={classes.container}>

          <GridContainer justify="center" >
            <GridItem xs={6} sm={12}>
              <br />
            </GridItem>
            <GridItem xs={6} sm={12}>
              <br />
            </GridItem>

            <GridItem xs={12} sm={6} md={9}>
              <h4 className={classes.description}> Click the download button to download a copy of "The Law Prophesied" by Ralph Mount.</h4>
            </GridItem>
            <GridItem xs={10} sm={6} md={3}>
                  <Button
                    color="info"
                    size="lg"
                    href={lawProphesied}
                  >
                    <i className="fas fa-download" /> Download
                  </Button>
                </GridItem>
              </GridContainer>

            <TeamSection />
          </div>
        </div>
        <Footer />
      </div>
    );
  }
}

export default withStyles(landingPageStyle)(LandingPage);
