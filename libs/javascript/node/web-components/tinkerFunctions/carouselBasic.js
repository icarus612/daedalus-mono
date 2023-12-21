
			anime({
				targets: ".bg",
				backgroundColor:
				[
					{
						value: ["#042B68", "#063F9A"],
						easing: "linear",
						duration: 2000,
						delay: 250

					},
					{
						value: ["#063F9A", "#03214F"],
						easing: "linear",
						duration: 2000,
						delay: 250

					},
					{
						value: ["#03214F", "#0749B3"],
						easing: "linear",
						duration: 2000,
						delay: 250

					},
					{
						value: ["#0749B3", "#042B68"],
						easing: "linear",
						duration: 2000,
						delay: 250

					},
				],
				loop: true,
			})

			anime({
				targets: ".carousel",
				backgroundColor: ["#C7E4FA", "#81C2F4"],
				loop: true,
				direction: "alternate",
				easing: "easeInCubic",
				duration: 2000,
				delay: 250
			})

			anime({
				targets: ".solutions",
				backgroundColor:
					{
						value: ["#E6F1FD", "#DEEFFC"],
						duration: 2000,
						delay: 120,
						easing: "linear",
					},
				color:
					{
						value: ["#666", "#999"],
						duration: 2000,
						delay: 120,
						easing: "linear",
					},
				direction: "alternate",
				loop: true,

			})


			var widthFunc = () => {
				return document.querySelector("body").offsetWidth > 992 ? 2 : 1
			}

			let hideMe = (e, n) => {
				for (let i = 0; i < e.length; i++){
					e[i].style.display = "block";
					e[i].style.order > n ? e[i].style.display = "none" : e[i].style.display = "block"
				}
			}

			var makeCarousel = (wrapper, card, showNo=0) => {
				let carousel = document.querySelector(wrapper).querySelectorAll(card)
				for (let i = 0; i < carousel.length; i++){
					carousel[i].style.order = [i+1];
					carousel[i].style.display = "block";
				}
				if (showNo) hideMe(carousel, showNo)
				return carousel
			}


			let findMe = (e, s, a=0) => {
				for (let i = 0; i < e.length; i++) {
					e[i].onclick = () => {

						for (let j = 0; j < s.length; j++) {
							let regCheck = new RegExp(`#${s[j].id}`);
							if (regCheck.test(e[i].id)){
								let x = (s.length+1)/2 - s[j].style.order;
								for (let u = 0; u < s.length; u++){
									s[u].style.order = Number(slider[u].style.order) + x;
									if (s[u].style.order > s.length) s[u].style.order = Number(s[u].style.order) -s.length;
									if (s[u].style.order < 1) s[u].style.order = s.length + Number(s[u].style.order);
								}
							}
						}
						if (a) a()
					}
				}
			}

			var prev = (e, s=0, a=0) => {
				for (let i = 0; i < e.length; i++){
					e[i].style.order++;
					if (e[i].style.order > e.length) e[i].style.order = 1;
				}
				if (s) hideMe(e, s);
				if (a) a();
			}
			var next = (e, s=0, a=0) => {
				for (let i = 0; i < e.length; i++){
					e[i].style.order--;
					if (e[i].style.order == 0) e[i].style.order = e.length;
				}
				if (s) hideMe(e, s);
				if (a) a();
			}

			let carousel1 = makeCarousel("carousel1", "story-box", widthFunc());
			let carousel2 = makeCarousel("carousel2", "story-box", widthFunc());
			let carousel3 = makeCarousel("carousel3", "story-box", widthFunc());
			let carouselsMade = [carousel1, carousel2, carousel3];

			window.onresize = () => {
				for (i = 0; i < carouselsMade.length; i++){
					hideMe(carouselsMade[i], widthFunc());
				}
			}
			let carouselLink = document.querySelectorAll(".carousel-link");
			let platformLink = document.querySelectorAll(".platform-link");
			findMe(carouselLink);
			findMe(platformLink);