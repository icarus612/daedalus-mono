var msgType = function(el, toRotate, period) {
    this.toRotate = toRotate;
    this.el = el;
    this.loopNum = 0;
    this.period = parseInt(period, 10) || 2000;
    this.msg = '';
    this.tick();
    this.deleting = false;
};

msgType.prototype.tick = function() {
    var i = this.loopNum % this.toRotate.length;
    var fullmsg = this.toRotate[i];

    if (this.deleting) {
        this.msg = fullmsg.substring(0, this.msg.length - 1);
    } else {
        this.msg = fullmsg.substring(0, this.msg.length + 1);
    }

    this.el.innerHTML = '<span class="wrap">'+this.msg+'</span>';

    var extra = this;
    var delta = 200 - Math.random() * 100;

    if (this.deleting) { delta /= 2; }

    if (!this.deleting && this.msg === fullmsg) {
        delta = this.period;
        this.deleting = true;
    } else if (this.deleting && this.msg === '') {
        this.deleting = false;
        this.loopNum++;
        delta = 500;
    }

    setTimeout(function() {
        extra.tick();
    }, delta);
};

window.onload = function() {
    var elements = document.getElementsByClassName('typewrite');
    for (var i=0; i<elements.length; i++) {
        var toRotate = elements[i].getAttribute('data-type');
        var period = elements[i].getAttribute('data-period');
        if (toRotate) {
            new msgType(elements[i], JSON.parse(toRotate), period);
        }
    }
    var css = document.createElement("style");
    css.type = "text/css";
    css.innerHTML = ".typewrite > .wrap { border-right: 0.08em solid #fff}";
    document.body.appendChild(css);
};