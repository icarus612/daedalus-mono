import React from "react";
// nodejs library that concatenates classes
import classNames from "classnames";
// @material-ui/core components
import withStyles from "@material-ui/core/styles/withStyles";

// @material-ui/icons

// core components
import GridContainer from "components/Grid/GridContainer.jsx";
import GridItem from "components/Grid/GridItem.jsx";
import Button from "components/CustomButtons/Button.jsx";
import Card from "components/Card/Card.jsx";
import CardBody from "components/Card/CardBody.jsx";
import CardFooter from "components/Card/CardFooter.jsx";

import teamStyle from "assets/jss/material-kit-react/views/landingPageSections/teamStyle.jsx";

import matthew from "newTestament/MATTHEW.doc";
import mark from "newTestament/MARK.doc";
import luke from "newTestament/LUKE.doc";
import john from "newTestament/JOHN.doc";
import john1 from "newTestament/I_John.doc";
import john2 from "newTestament/II_John.doc";
import john3 from "newTestament/III_John.doc";
import acts from "newTestament/ACTS.doc";
import colossians from "newTestament/COLOSSIANS.doc";
import ephesians from "newTestament/EPHESIANS.doc";
import galatians from "newTestament/GALATIANS.doc";
import hebrews from "newTestament/HEBREWS.doc";
import corinthians1 from "newTestament/I_Corinthians.doc";
import corinthians2 from "newTestament/II_CORINTHIANS.doc";
import peter1 from "newTestament/I_Peter.doc";
import peter2 from "newTestament/II_Peter.doc";
import thessalonians1 from "newTestament/I_THESSALONIANS.doc";
import thessalonians2 from "newTestament/II_Thessalonians.doc";
import timothy1 from "newTestament/MATTHEW.doc";
import timothy2 from "newTestament/MATTHEW.doc";
import james from "newTestament/JAMES.doc";
import jude from "newTestament/JUDE.doc";
import philemon from "newTestament/PHILEMON.doc";
import revelation from "newTestament/REVELATION.doc";
import romans from "newTestament/ROMANS.doc";
import titus from "newTestament/TITUS.doc";
import philippians from "newTestament/PHILIPPIANS.doc";

import team1 from "assets/img/faces/avatar.jpg";
import team2 from "assets/img/faces/avatar.jpg";
import team3 from "assets/img/faces/avatar.jpg";
import team4 from "assets/img/faces/avatar.jpg";
import team5 from "assets/img/faces/avatar.jpg";
import team6 from "assets/img/faces/avatar.jpg";
import team7 from "assets/img/faces/avatar.jpg";
import team8 from "assets/img/faces/avatar.jpg";
import team9 from "assets/img/faces/avatar.jpg";
import team10 from "assets/img/faces/avatar.jpg";
import team11 from "assets/img/faces/avatar.jpg";
import team12 from "assets/img/faces/avatar.jpg";
import team13 from "assets/img/faces/avatar.jpg";
import team14 from "assets/img/faces/avatar.jpg";
import team15 from "assets/img/faces/avatar.jpg";
import team16 from "assets/img/faces/avatar.jpg";
import team17 from "assets/img/faces/avatar.jpg";
import team18 from "assets/img/faces/avatar.jpg";
import team19 from "assets/img/faces/avatar.jpg";
import team20 from "assets/img/faces/avatar.jpg";
import team21 from "assets/img/faces/avatar.jpg";
import team22 from "assets/img/faces/avatar.jpg";
import team23 from "assets/img/faces/avatar.jpg";
import team24 from "assets/img/faces/avatar.jpg";
import team25 from "assets/img/faces/avatar.jpg";
import team26 from "assets/img/faces/avatar.jpg";
import team27 from "assets/img/faces/avatar.jpg";

class TeamSection extends React.Component {
  render() {
    const { classes } = this.props;
    const imageClasses = classNames(
      classes.imgRaised,
      classes.imgRoundedCircle,
      classes.imgFluid
    );
    return (
      <div className={classes.section}>

        <div>
          <GridContainer>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={matthew} ><img src={team1} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Matthew
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={mark} ><img src={team2} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Mark
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={luke} ><img src={team3} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Luke
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={john} ><img src={team4} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                John
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={acts} ><img src={team5} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Acts
              </h4>
                <br />
            </Card>
          </GridItem>

          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={romans} ><img src={team6} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Romans
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={corinthians1} ><img src={team7} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                1st Corinthians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={corinthians2} ><img src={team8} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                2nd Corinthians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={galatians} ><img src={team9} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Galatians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={ephesians} ><img src={team10} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Ephiesians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={philippians} ><img src={team11} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Philippians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={colossians} ><img src={team12} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Colossians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={thessalonians1} ><img src={team13} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                1st Thessalonians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={thessalonians2} ><img src={team14} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                2nd Thessalonians
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={timothy1} ><img src={team15} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                1st Timothy
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={timothy2} ><img src={team16} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                2nd Timothy
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={titus} ><img src={team17} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Titus
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={philemon} ><img src={team18} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Philemon
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={hebrews} ><img src={team19} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Hebrews
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={james} ><img src={team20} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                James
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={peter1} ><img src={team21} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                1st Peter
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={peter2} ><img src={team22} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                2nd Peter
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={john1} ><img src={team23} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                1st John
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={john2} ><img src={team24} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                2nd John
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={john3} ><img src={team25} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                3rd John
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={jude} ><img src={team26} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Jude
              </h4>
                <br />
            </Card>
          </GridItem>
          <GridItem xs={6} sm={4} md={3}>
            <Card plain>
              <GridItem xs={12} sm={12} md={6} className={classes.itemGrid}>
                <a href={revelation} ><img src={team27} alt="..." className={imageClasses} /></a>
              </GridItem>
              <h4 className={classes.cardTitle}>
                Revelation
              </h4>
                <br />
            </Card>
          </GridItem>
          </GridContainer>
        </div>
      </div>
    );
  }
}

export default withStyles(teamStyle)(TeamSection);
