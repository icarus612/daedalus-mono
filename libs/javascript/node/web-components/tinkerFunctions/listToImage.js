let fs = require('fs')
let process = require('process')
let request = require('request')

let save = process.argv[3] || "saveFile/"

fs.mkdir(save, (err)=> {
    if (err) console.log("saving to file: " + save);
    else console.log("making new directory: " + save);
});

fs.readFile(process.argv[2], 'utf8', (err, data) => {
    if (err) throw err;
    let x = data.split(/[,\s\n]/)
    console.log(x)
    let re = /\.[psj][pvn].*g/
    
    for (let i = 0; i < x.length; i++){
        let end = x[i].match(re)
        console.log("grabbing file: " + x[i])
        if (x[i]){
            request.get(x[i], (err, res, body)=>{
                if (err) throw err;
            }).pipe(fs.createWriteStream(save + i + end), console.log("saving to: " + i + end))
        }
        
    }
    console.log("All files created and saved.")
});

