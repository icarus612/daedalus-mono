
        let locate = document.querySelectorAll(".throbber-inner"),
            startX = () => (document.querySelector("#dot-outer").offsetWidth - document.querySelector("#dot-start").offsetWidth)/2 +85,
            stage = document.querySelector("#stage"),
            fullHeight = () => stage.offsetHeight,
            fullWidth = () => stage.offsetWidth,
            startY = () => fullHeight()/2-5,
            endY = (e) => steps[e].offsetHeight/2+8,
            endX = (e) => steps[e].offsetWidth+85,
            steps = [];
        for (let i = 0; i < stage.childNodes.length; i++){
            let check = new RegExp("col");
            let x = `${stage.childNodes[i].className}`
            if (check.test(x)) steps.push(stage.childNodes[i])
        }

        let animate = () =>{
            let animation = anime.timeline({
                easing: "easeInOutCubic",
                complete: function(anim) {
                    animate()
                }
            }).add({
                targets: ".catapult-ani",
                translateY: [-5, startY()],
                translateX: [startX(), startX()],
                duration: 1000,
                easing: "easeOutCubic",
            }, 800).add({
              targets: ".pulsar",
              opacity: [1, 0],
              scale: [
                {value: [1, 2]},
              ],
              easing: "easeOutCubic",
              duration: 1000,
            }).add({
                targets: ".catapult-ani",
                translateX: [startX(), (startX() + fullWidth() - endX(0))],
                translateY: [startY(), endY(0)],
                duration: 600,
                easing: "easeOutCubic"
            }).add({
                targets: ".catapult-ani",
                translateY: [
                    {value: [startY(), (startY() * 2 - endY(2))]},
                    {value: [(startY() * 2 - endY(2)), endY(0)]},
                    {value: [endY(0), startY()]}
                ],
                translateX: { value: [startX(), (startX() + fullWidth() - endX(1))], easing: "linear",},
                duration: 1300,
                delay: 100
            }).add({
              targets: ".pulse4",
              opacity: [1, 0],
              scale: [
                {value: [1, 2]},
              ],
              easing: "easeOutCubic",
              duration: 1000,
            }).add({
                targets: ".catapult-ani",
                translateX: [
                    {
                        value: [startX(), (startX() + (fullWidth() - endX(2))/3)],
                        duration: 500,
                        easing: "linear"
                    },
                    {
                        value: [(startX() + (fullWidth() - endX(2))/3), (startX() + fullWidth() - endX(2))],
                        duration: 910,
                        easing: "linear"
                    },
                ],
                translateY: [
                    {
                        value: [startY(), (startY()*2 - endY(2))],
                        duration: 500,
                        easing: "easeInQuad"
                    },
                    {
                        value: [(startY()*2 - endY(2)), startY()],
                        duration: 450,
                        easing: "easeOutCirc"
                    },
                    {
                        value: [startY(), (startY()*2 - endY(2))],
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
                    value: ["#2D80C3", "#fff"],
                    delay: 450,
                    duration: 100
                },
                border: [0, "2px solid #2D80C3"],
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

            })
            return animation
        }
        animate()
