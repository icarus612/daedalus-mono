let isVisible = (e) => {
    let el = document.querySelector(e);
    let where = el.getBoundingClientRect();
    let screen = window.innerHeight;
    return where.top - screen > 0  ? false : where.bottom > 0 ? true : false
}

let checkToPause = (el, animation) => {
    for (let i = 0; i < animation.length; i++) {
        if (!isVisible(el)) {
            animation[i].pause()
        } else {
            animation[i].play()
        }
    }
}