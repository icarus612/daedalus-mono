let paltformAnimation = (time, target, color1, color2, howMany) => {
    let scrollBG = [];
    let animateBG = (t, x, c1, c2) => {
        scrollBG[scrollBG.length] =
            anime({
                targets: x,
                backgroundColor: [c2, c1],
                easing: "linear",
                autoplay: false,
                duration: t,
                delay: t * scrollBG.length
            })
    }
    let first = (i) => {i % 2 == 0 ? color1 : color2}
    let second = (i) => {i % 2 == 0 ? color2 : color1}
    for (let i = 0; i < howMany; i++){
        scrollBG.length == 0 ? animateBG(time, target, color1, color1) : animateBG(time, target, first(i), second(i));
    }
    console.log(scrollBG)
    return scrollBG
}

let animation = []
animation[0] = paltformAnimation(1000, ".bg-solid-darkblue", "#F1F8FF", "#004589", 4)
animation[1] = paltformAnimation(1000, ".step", "#F1F8FF", "#004589", 4)
let fullHeight = Math.floor(document.getElementById("fullHeight").clientHeight/4);

window.onscroll = () => {
    let solutions = document.getElementById("solutions");
    for (let j = 0; j < animation.length; j++){
        let x = Math.floor(animation[j][animation[j].length-1].currentTime/1000)
        for (i = 0; i < animation[j].length; i++){
            animation[j][i].seek((window.scrollY / (solutions.clientHeight * 6)) * animation[j][i].duration);
        }
        animation[j][x].seek((window.scrollY / (solutions.clientHeight * 6)) * animation[j][ animation[j].length-1 ].duration);
        console.log(animation[j][x].currentTime)
    }
}
