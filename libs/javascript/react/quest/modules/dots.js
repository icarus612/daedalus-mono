import anime from 'animejs';

const where = (e) => {
  return (e[1] + e[0]) / 2;
}

const translateY = (mv, t, crv) => {
  switch (crv) {
    case "cubic":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 3.5,
            easing: "easeInOutCubic",
          },
        ]
      )
      break;
    case "cubicY":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 3.5,
            easing: "easeInOutCubic",
          },
        ]
      )
      break;
    case "cubicX":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 3.5,
            easing: "linear",
          },
        ]
      )
      break;
    case "linear":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 1.5,
            easing: "linear",
            delay: t,
          },
        ]
      )
      break;
    case "linearX":
      return (
        [
          {
            value: [mv[0], where(mv)],
            duration: t,
            easing: "linear",
          },
          {
            value: [where(mv), mv[1]],
            duration: t,
            delay: t * 1.5,
            easing: "linear",
          },
        ]
      )
      break;
    case "linearY":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 1.5,
            easing: "linear",
            delay: t,
          },
        ]
      )
      break;

    default:
      return (
        [
          {
            value: [mv[0], where(mv)],
            duration: t,
            easing: "linear",
          },
          {
            value: [where(mv), mv[1]],
            duration: t,
            delay: t * 1.5,
            easing: "linear",
          },
        ]
      )
      break;
  }
}

const translateX = (mv, t, crv) => {
  switch (crv) {
    case "cubic":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 3.5,
            easing: "easeInOutCubic",
          },
        ]
      )
      break;
    case "cubicX":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 3.5,
            easing: "easeInOutCubic",
          },
        ]
      )
      break;
    case "cubicY":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 3.5,
            easing: "linear",
          },
        ]
      )
      break;
    case "linear":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 1.5,
            easing: "linear",
            delay: anime.stagger(t / 2, { start: t }),
          },
        ]
      )
      break;
    case "linearX":
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 1.5,
            easing: "linear",
            delay: anime.stagger(t / 2, { start: t }),
          },
        ]
      )
      break;
    case "linearY":
      return (
        [
          {
            value: [mv[0], where(mv)],
            duration: t,
            easing: "linear",
          },
          {
            value: [where(mv), mv[1]],
            duration: t,
            delay: t * 1.5,
            easing: "linear",
          },
        ]
      )
      break;
    default:
      return (
        [
          {
            value: [mv[0], mv[1]],
            duration: t * 1.5,
            easing: "linear",
            delay: t,
          },
        ]
      )
      break;
  }
}

let fillColor = (e, t, svg) => {


  let obj = [
    {
      value: e[0],
      duration: (t * 1.5) / e.length,
      easing: "linear",
      delay: anime.stagger(t / 2)
    },
  ]

  for (let i = 1; i < e.length; i++) {
    obj.push({
      value: e[i],
      duration: (t * 1.5) / e.length,
      easing: "linear",
      delay: t / e.length
    });
  }
  return obj;

}

const whereTarget = (position, el) => {
  let currentPosition = position.getBoundingClientRect()
  let element = el.getBoundingClientRect()
  let x = position.offsetLeft;
  let y = ((currentPosition.top + currentPosition.bottom) / 2 - (element.top + element.bottom) / 2);
  return [x, y]
}

const animation = (e, t, svg, start, end, crv, clr, d) => {

  const _start = whereTarget(start, svg.children[e])
  const _end = whereTarget(end, svg.children[e])

  let animate = anime.timeline({
    targets: svg.children[e]
  }).add({
      translateX: translateX([_start[0], _end[0]], t, crv),
      translateY: translateY([_start[1], _end[1]], t, crv),
      fill: fillColor(clr, t, svg),
      backgroundColor: fillColor(clr, t, svg),
      complete: function (anim) {
        animate.reset()
        animation(e, t, svg, start, end, crv, clr, 0)
      },
    }, d);

  return animate
}

export default ({el, start, end, time, curve, color}) => {
  let delay = (e, time, n) => {
    return 3.5 * time / e.children.length * n
  }
  const item = el.current
  if (!item) return 
  //mobile functions for distance
  [...item.children].forEach((_, i)=> animation(i, time, item, start, end, curve, color, delay(item, time, i)))
}
