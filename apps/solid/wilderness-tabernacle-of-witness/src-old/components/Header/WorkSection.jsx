import React from "react";
// @material-ui/core components
import withStyles from "@material-ui/core/styles/withStyles";
// nodejs library that concatenates classes
import classNames from "classnames";
// @material-ui/core components
// @material-ui/icons

// core components
import GridContainer from "components/Grid/GridContainer.jsx";
import GridItem from "components/Grid/GridItem.jsx";
import CustomInput from "components/CustomInput/CustomInput.jsx";
import Button from "components/CustomButtons/Button.jsx";
import workStyle from "assets/jss/material-kit-react/views/landingPageSections/workStyle.jsx";
import axios from 'axios';

class WorkSection extends React.Component {
  constructor(props) {
    super(props);
      this.state = {
        name: '',
        email: '',
        message: ''
      };
      this.updateField = this.updateField.bind(this);
    }
updateField(input, value){
  this.setState({[input]: value });
}
async handleSubmit(event){
  event.precentDefault();
  const {name, email, message} = this.state;

  const form = await axios.post ('/api/form', {
    name,
    email,
    message
  });
}
    render() {
    const { classes } = this.props;
    return (
      <div>
      <div className={classes.centered}> <Button
        justIcon
        color="transparent"
        className={classes.margin5}
      ><i className={classes.socials + " fas fa-envelope"} />
    </Button> <p className={classes.description}> EllisHogan95@gmail.com </p>
      <Button
        justIcon
        color="transparent"
        className={classes.margin5}
      ><i className={classes.socials + " fas fa-phone"} />
    </Button> <p className={classes.description}
> 704-839-1628 </p></div>
            <form onSubmit={this.handleSubmit}>
              <GridContainer>
                <GridItem xs={12} sm={12} md={6}>
                  <CustomInput
                    labelText="Your Name"
                    id="name"
                    type="text"
                    name="name"
                    value={this.state.name}
                    onChange={(event) => this.updateField('name', event.target.value)}
                    formControlProps={{
                      fullWidth: true
                    }}
                  />
                </GridItem>
                <GridItem xs={12} sm={12} md={6}>
                  <CustomInput
                    labelText="Your Email"
                    id="email"
                    type="email"
                    name="email"
                    value={this.state.email}
                    onChange={(event) => this.updateField('email', event.target.value)}
                    formControlProps={{
                      fullWidth: true
                    }}
                  />
                </GridItem>
                <CustomInput
                  labelText="Your Message"
                  id="message"
                  type="text"
                  name="message"
                  value={this.state.message}
                  onChange={(event) => this.updateField('message', event.target.value)}
                  formControlProps={{
                    fullWidth: true,
                    className: classes.textArea
                  }}
                  inputProps={{
                    multiline: true,
                    rows: 5
                  }}
                />
                <GridContainer justify="center">
                  <GridItem
                    xs={12}
                    sm={12}
                    md={4}
                    className={classes.textCenter}
                  >
                    <Button color="primary" formValues={this.state} onClick={(event)=> this.onSubmit()} >Send Message</Button>
                  </GridItem>
                </GridContainer>
              </GridContainer>
            </form></div>

    );
  }
}

export default withStyles(workStyle)(WorkSection);
