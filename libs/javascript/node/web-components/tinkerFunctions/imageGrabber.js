let fs = require('fs'),
    request = require('request');

fs.readFile('./shopify-files-list.txt', 'utf8', function(err, data){
    if (err) throw err;
    processFile(data);
});
let download = function(uri, filename, callback){
    request.head(uri, function(err, res, body){
        console.log('content-type:', res.headers['content-type']);
        console.log('content-length:', res.headers['content-length']);
        request(uri).pipe(fs.createWriteStream(filename)).on('close', callback);
    });
  };
const processFile = (e) =>{
    let x = e.split(",");
    for (let i = 0; i < x.length; i++){
        let name = x[i].split("").slice(8, x[i].length).join("");
        download(x[i], `./images/${name}`, function(){
            console.log("done");
        });
    }
}


