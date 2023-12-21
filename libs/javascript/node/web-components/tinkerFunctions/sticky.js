let toChange = document.querySelector(".event-featured");

let findSize = () => {
    let c = document.getElementById("partner-list");
    let cW = c.offsetWidth;
    let cH = c.offsetHeight;
    cW > 768 ? toChange.style.height = `${cH-30}px`: toChange.style.height = `510px`;
}
findSize();
window.onresize = () => {
    findSize();
}