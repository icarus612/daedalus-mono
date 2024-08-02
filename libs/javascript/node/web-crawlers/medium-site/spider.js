const request = require('request');
const cheerio = require('cheerio');
const fs = require('fs');

let basicInfo = class {
    constructor(title, about, href){
        this._title = title;
        this._about = about;
        this._href = href;
    }
    get title() { return this._title }
    get about() { return this._about }
    get href() { return this._href }

}
request('http://medium.com/topic/members', (err, res, html) =>{
    var section = [];

    if (err) return err
    if (res.statusCode == 200) {
        const $ = cheerio.load(html);

        console.log($(html).length)



        const sections = $('#root section');
        sections.each((i, el)=>{
            if (i % 2 === 0 ) {
                let title = $(el).find('h3').text();
                let about = $(el).find('p').text();
                let href = $(el).find('a').attr('href');
                newSection = new basicInfo(title, about, href)
                section.push(newSection)
            }
      
        })
    }
    let stream = fs.createWriteStream('medium.json');
    for (let i = 1; i < section.length; i++){
        stream.write(
            `{
                "_id": ${i}, \n 
                "title": "${section[i].title}", \n 
                "about": "${section[i].about}" \n
                "href": "${section[i].href}", \n
            }\n`
        );
    }
    stream.end();
});