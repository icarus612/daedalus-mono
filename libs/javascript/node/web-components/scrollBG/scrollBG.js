let scrollBG = [];
const time = 1000; // this var effects nothing but dont touch it the time must stay constant for time delay
anime({
    targets: ".throbber-inner-mini",
    scale: .5,
    border: "0px",
    opacity: [0,1],
    easing: "easeInOutCubic",
    direction: "reverse",
    loop: true,
    duration: 1500,
    endDelay: 1500
})
let animateBG = (el, c1, c2) => {
    return(
        anime({
            targets: el,
            backgroundColor: [c1, c2],
            easing: "linear",
            autoplay: false,
            duration: time,
            delay: time * scrollBG.length
        })
    )
}
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#134a89", "#1ea185")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#1ea185", "#9bbb5c")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#9bbb5c", "#e3f226")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#e3f226", "#f29b26")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#f29b26", "#bd392f")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#bd392f", "#f15b6d")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#f15b6d", "#9b26f2")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#9b26f2", "#3fa3db")
scrollBG[scrollBG.length] = animateBG(".color-change-bg", "#3fa3db", "#134a89")


let startColor = document.getElementById("main");
let fullHeight = Math.floor(document.getElementById("main").clientHeight/5);
startColor.style.backgroundColor = "#004589";
window.onscroll = () => {
    let x = Math.floor(scrollBG[scrollBG.length-1].currentTime/time)
    let y = Math.floor(scrollBG[scrollBG.length-1].currentTime)

    for (i = 0; i < scrollBG.length; i++){
        scrollBG[i].seek((window.scrollY / (time * 8)) * scrollBG[i].duration);
    }
    scrollBG[x].seek((window.scrollY / (time * 8)) * scrollBG[scrollBG.length-1].duration);

    y < 20 ? startColor.style.backgroundColor = "#004589" : null

};
