import React, { Component } from 'react';
import logo from './logo.svg';
import './App.css';
import FormGroup from 'react-bootstrap/lib/FormGroup';
import ControlLabel from 'react-bootstrap/lib/ControlLabel';
import FormControl from 'react-bootstrap/lib/FormControl';

let marked = require('marked');

class App extends Component {
  state={
    markdown:""
  }
  Update = (markdown) => {
    this.setState({markdown})
  }
  render() {
    let {markdown} = this.state;
    return (
      <div className="App">
        <FormGroup controlId="formControlsTextarea">
          <ControlLabel>Markdown Input</ControlLabel>
          <FormControl componentClass="textarea" placeholder="Add Markdown" value={markdown} onChange={(event)=> this.Update(event.target.value)}></FormControl>
        </FormGroup>
        <h1>Viewer</h1>
        <div>{marked(markdown)}</div>
      </div>
    );
  }
}

export default App;
