import anime from 'animejs';

export let animateLI = ({ dot, topThrobber, midThrobber, listStart, li1, li2, li3, mv1, mv2, mv3 }) => {
	let top = document.querySelector(`.${topThrobber}`).getBoundingClientRect(),
		start = document.querySelector(`.${midThrobber}`).getBoundingClientRect(),
		end1 = document.querySelector(`.${li1}`).getBoundingClientRect(),
		end2 = document.querySelector(`.${li2}`).getBoundingClientRect(),
		end3 = document.querySelector(`.${li3}`).getBoundingClientRect(),
		endY = (s, e, p = 0) => (e.top + e.bottom) / 2 - (s.top + s.bottom) / 2 + p,
		endX = (s, e, p = 0) => (e.left + e.right) / 2 - (s.left + s.right) / 2 + p,
		steps = [];
	let animation = anime.timeline({
		easing: "easeInOutCubic",
		complete: function (anim) {
			animateLI({ dot, topThrobber, midThrobber, listStart, li1, li2, li3, mv1, mv2, mv3 })
		}
	}).add({
		targets: `.${dot}`,
		translateY: [0, endY(top, start)],
		translateX: [2, 2],
		duration: 1000,
		easing: "easeOutCubic",
	}, 887).add({
		targets: `.${listStart}`,
		opacity: [1, 0],
		scale: [
			{ value: [1, 2] },
		],
		easing: "easeOutCubic",
		duration: 1000,
	}).add({
		targets: `.${mv1}`,
		translateX: [0, endX(start, end1)],
		translateY: [endY(top, start), endY(top, end1)],
		skew: {value: -55, duration: 400},
		duration: 600,
		easing: "easeInElastic"
	}).add({
		targets: `.${mv1}`,
		skew: 0,
		opacity: [1, 0],
		duration: 1,
		easing: "linear"
	}).add({
		targets: `.${li1}`,
		opacity: [1, 0],
		scale: [
			{ value: [1, 2] },
		],
		easing: "easeOutCubic",
		duration: 1000,
	}).add({
		targets: `.${mv3}`,
		translateY: [
			{ value: [endY(top, start), endY(top, end1, -20)] },
			{ value: [endY(top, end1, -20), endY(top, end3, 20)] },
			{ value: [endY(top, end3, 20), endY(top, end2)] }
		],
		translateX: {
			value: [0, endX(start, end2)],
			easing: "linear",
		},
		duration: 1300,
		delay: 100
	}).add({
		targets: `.${mv3}`,
		opacity: [1, 0],
		duration: 1,
		easing: "linear"
	}).add({
		targets: `.${li2}`,
		opacity: [1, 0],
		scale: [
			{ value: [1, 2] },
		],
		easing: "easeOutCubic",
		duration: 1000,
	}).add({
		targets: `.${mv2}`,
		translateX: [
			{
				value: [0, endX(start, end3) / 3],
				duration: 500,
				easing: "linear"
			},
			{
				value: [endX(start, end3)],
				duration: 910,
				easing: "linear"
			},
		],
		translateY: [
			{
				value: [endY(top, start), endY(top, end3)],
				duration: 500,
				easing: "easeInQuad"
			},
			{
				value: [endY(top, end3), endY(top, start)],
				duration: 450,
				easing: "easeOutCirc"
			},
			{
				value: [endY(top, start), endY(top, end3)],
				duration: 450,
				easing: "easeInCirc"
			},
		],
		height: [
			{
				value: ["10px", "1px"],
				delay: 480,
				duration: 30
			},
			{
				value: ["1px", "10px"],
				duration: 30
			},
		],
		backgroundColor: {
			value: ["#AF46D3", "#fff"],
			delay: 450,
			duration: 100
		},
		border: [0, "2px solid #AF46D3"],
		borderRadius: {
			value: ["50%", "0px"],
			delay: 450,
			duration: 100
		},
		rotateZ: {
			value: [0, 720],
			delay: 500,
			duration: 800,
			easing: "easeInOutCirc"
		},

	}).add({
		targets: `.${mv2}`,
		opacity: [1, 0],
		duration: 1,
		easing: "linear"
	}).add({
		targets: `.${li3}`,
		opacity: [1, 0],
		scale: [
			{ value: [1, 2] },
		],
		easing: "easeOutCubic",
		duration: 1000,
	})

	return animation

}
