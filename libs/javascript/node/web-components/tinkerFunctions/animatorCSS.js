let animateCSS = (obj)=>{
  /*
    All 'typeof' functions are just checks to see both if the object key was even defined,
     and what type of object it is. This function is set to replace jQuery animations.
     It does take a callback, and removes the animation on end.
  */
  let el = typeof obj.target == 'string' ? document.querySelector(animation.target) : obj.target;
  if (obj.speed) typeof obj.speed == "number" ? el.style.animationDuration = obj.speed : console.error("Speed in animateCSS() must be a number");
  switch(typeof obj.loop){
    case 'number':
      el.style.animationIterationCount = obj.loop;
      break;
    case 'boolean':
      el.style.animationIterationCount = obj.loop ? 'infinate' : 0;
    case 'undefined':
      break;
    default:
      console.error("Loop's in animateCSS() must be a number or 'true'.");
      break;
  }
  el.classList.add('animated', obj.animation);
  el.addEventListener('animationend', ()=> {
      el.classList.remove('animated', obj.animation);
      if (obj.callback) typeof obj.callback == 'function' ? obj.callback() : console.error("Callback's in animateCSS() must be a function");
  });
}