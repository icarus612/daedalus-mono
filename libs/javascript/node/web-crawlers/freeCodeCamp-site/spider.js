const request = require('request');
const cheerio = require('cheerio');
const fs = require('fs');

let basicInfo = class {
    constructor(title, author, authorURL, postURL){
        this._title = title;
        this._author = author;
        this._authorURL = authorURL;
        this._postURL = postURL;
    }
    get title() { return this._title }
    get author() { return this._author }
    get authorURL() { return this._authorURL }
    get postURL() { return this._postURL }

}
request('https://www.freecodecamp.org/news/', (err, res, html) =>{
    var section = [];

    if (err) return err
    if (res.statusCode == 200) {
        const $ = cheerio.load(html);

        console.log($(html).length)



        const sections = $('article');
        sections.each((i, el)=>{
            if (i % 2 === 0 ) {
                let title = $(el).find('h2').text().trim();
                let author = $(el).find('.author-list').text().trim();
                let authorURL = $(el).find('.author-list').find('a').attr('href');
                let postURL = $(el).find('.post-card-image-link').attr('href');
            

                newSection = new basicInfo(title, author, authorURL, postURL)
                section.push(newSection)
            }
      
        })
    }
    let stream = fs.createWriteStream('freeCodeCamp.json');
    for (let i = 1; i < section.length; i++){
        stream.write(
            `{
                "_id": ${i}, \n 
                "Title": "${section[i].title}", \n 
                "Author": "${section[i].author}", \n
                "Author URL": "www.freecodecamp.com${section[i].authorURL}", \n
                "Article URL": "www.freecodecamp.com${section[i].postURL}", \n
            }\n`
        );
    }
    stream.end();
});