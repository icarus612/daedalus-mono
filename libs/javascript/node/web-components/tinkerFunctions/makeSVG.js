
const addArrClass = (e, c) => { //e is element and c is classes to add
  for (let i = 0; i < c.length; i++) {
    i != 0 ? e.setAttributeNS(null, "class", " "): null; //doesnt add a space to the first element for class name seperation
    e.setAttributeNS(null, "class", c[i]); //add the classes
  }
}

const makeSVG = (el, howMany, classSVG, classElement, w, h, apnd) => {
  let svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttributeNS(null, 'width', w);
  svg.setAttributeNS(null, 'height', h);
  //checks to see if the cssSVG comes in as a string and adds the class if so. if not it adds all the classes in the array
  typeof classSVG === "string" ?  svg.setAttributeNS(null, "class", classSVG) : addArrClass(svg, classSVG);
  // default svg animation builder
  switch (el){


    default:
      let dot = []
      for (let i = 0; i < howMany; i++){
        let circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.push(circle);
        dot[i].className += classElement[i % classElement.length];
        dot[i].setAttributeNS(null, 'cy', -5);
        dot[i].setAttributeNS(null, 'cx', w - 15);
        dot[i].setAttributeNS(null, 'r', 5);
        svg.appendChild(dot[i]);
        dot[i].className +=  ` dot dotNo${i}`;
      }
  }
  return document.querySelector(apnd).appendChild(svg);
}