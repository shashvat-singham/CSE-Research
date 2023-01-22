const express = require('express');

const fs = require('fs')


// for calling python files
const {spawn} = require('child_process');
const cors = require('cors');
const bodyParser = require('body-parser');

// instantiates express so we can use the middleware functions
const app = express();
app.use(cors())
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Node's native tool for working with files. 
const path = require('path');

// set a default port in case the host isn't configured with one
const port = process.env.PORT || 5000;

app.use(express.static(path.join(__dirname, 'build')));

//app.get('http://localhost:5000/getjson', (req,res) => {
app.get('/getgrammar', (req,res) => {
    console.log("reached")
    const passcode = req.query['passcode']
    //res.sendFile(path.join(__dirname+'build/index.html'));
        res.setHeader('Content-Type', 'application/json');

        // need to implement logic for selecting grammar from a set of grammar
        let rawdata = fs.readFileSync('./allocation.json');
        let data = JSON.parse(rawdata);
        var groupList  = Object.keys(data)
        var passcodeList = [ "202220222022" ]
        for (let i = 0; i < groupList.length; i++){
            var temp = data[groupList[i]]["passcode"]
            passcodeList.push(temp)
        }
        // console.log("passcode:", passcodeList)
        // if (passcode == 2022){
        if (passcodeList.includes(passcode)){

        //2, 4, 5, 6, 8, 9, 10, 11, 14, 15
        let rawdata = fs.readFileSync('./grammar2Task.json');
        let data = JSON.parse(rawdata);
        var gram = {};
        gram["0"] = "Choose...";
        for(var i = 0; i < data.length; i++) {
            var obj = data[i];
            gram[obj.Id] = obj.Name;
        }
        //const gram = { "0": "", "2": "Grammar 1", "4": "Grammar 2", "5": "Grammar 3", "6": "Grammar 4", "8": "Grammar 5", "9": "Grammar 6", "10": "Grammar 7", "11": "Grammar 8", "14": "Grammar 9", "15": "Grammar 10" }
        res.end(JSON.stringify(gram));
        }
        else{
            res.end(JSON.stringify(""));
        }
});

app.get('/gettask', (req,res) => {
    console.log("reached" + req.query['grammar'])
    const grammarSelected = req.query['grammar']
    //res.sendFile(path.join(__dirname+'build/index.html'));
        res.setHeader('Content-Type', 'application/json');

        var tasks = {};
        
        // need to select  task based on the grammar selected

        let rawdata = fs.readFileSync('./grammar2Task.json');
        let data = JSON.parse(rawdata);
        for(var i = 0; i < data.length; i++) {
            var obj = data[i];
            if (obj.Id == grammarSelected){
                tasks = obj.Task;
                break
            }
        }
        /*
        if((grammarSelected == "2") || (grammarSelected == "10")){
            colors = {"empty": "","1":"1", "2": "2", "3":"3", "4":"4", "5":"5"};
        }
        if((grammarSelected == "4") || (grammarSelected == "6") || (grammarSelected == "8") || (grammarSelected == "11")){
            colors = {"empty": "","1":"1", "2": "2", "3":"3", "4":"4", "5":"5", "6":"6"};
        }
        if((grammarSelected == "5") || (grammarSelected == "14")){
            colors = {"empty": "","1":"1", "2": "2", "3":"3", "4":"4", "5":"5", "6":"6", "7":"7"};
        }
        if(grammarSelected == "9"){
            colors = {"empty": "","1":"1", "2": "2"};
        }
        if(grammarSelected == "15"){
            colors = {"empty": "","1":"1", "2": "2", "3":"3"};
        }
        */
       
        res.end(JSON.stringify(tasks));
});

app.get('/getparsetable', (req,res) => {
        console.log("reached: " + req.query['grammar'] + ", " + req.query['task'])
        const grammarSelected = req.query['grammar']
        const taskSelected = req.query['task'] 
        //res.sendFile(path.join(__dirname+'build/index.html'));
        res.setHeader('Content-Type', 'application/text');
        console.log("inside get parsetable", grammarSelected, taskSelected)
        // need to call my python file to get grammar, parse table and the feedback also
        var process = spawn('python', ['./nodeHandle.py', grammarSelected, taskSelected]);

        

        process.stdout.on('data', function(data){
            s = data.toString();
            j = JSON.parse(s);
            console.log("Received data: "+  s);  
            console.log("Received JSON ParseTable: "+  j["ParseTable"]);
            console.log("Received JSON Feedback: "+  j["Feedback"]);
            console.log("Received JSON Grammar: "+  j["Grammar"]);

        //    res.end(JSON.stringify(data.toString()));
        res.end(JSON.stringify(s));
        })

        // const colors = "success";
        // res.end(JSON.stringify(colors));
});

app.get('/getentries', (req,res) => {
    console.log("reached getentries")
    const passcode = req.query['passcode']
    console.log("Passcode" + passcode)
    //res.sendFile(path.join(__dirname+'build/index.html'));
    res.setHeader('Content-Type', 'application/json');

    if(passcode === "" || passcode === null){
        // const colors = {'': ''};
        // console.log("if in getentries")
        res.end(JSON.stringify(""));
    }else{
    var files = fs.readdirSync("./submissions/").filter(fn => fn.startsWith(passcode));
    if(files.length === 0){

        res.end(JSON.stringify(""))
    }
    else {
        var contentMap = {}
        for (let i = 0; i < files.length; i++){
            let content = fs.readFileSync("./submissions/" + files[i]).toString()
            contentMap["\"" + files[i] + "\""] = content
        }
        // let dirCont = fs.readdirSync("./submissions/");
        // let files = dirCont.filter(function( elm ) {return elm.match(/.*\.(html?)/ig);});
        // console.log(files)
        // console.log(contentMap)
        res.end(JSON.stringify(contentMap));
    }
    }
});

app.post('/soln', (req,res) => {
    console.log("post reached")
    console.log("reached: " + req.body['grammar'])
    const passcode = req.body['passcode']
    const grammarSelected = req.body['grammar']
    const taskSelected = req.body['task'] 
    const solutionSelected = req.body['solution'] 
    const feedbackSelected = req.body['feedback']

    if(passcode === ""){
         res.setHeader('Content-Type', 'application/json');
    // res.setHeader("Access-Control-Allow-Origin", "*");
    // res.setHeader("Access-Control-Allow-Origin", "cyclops.cse.iitk.ac.in");
    res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE");
    res.setHeader("Access-Control-Max-Age", "3600");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Origin, Cache-Control, X-Requested-With");
    res.setHeader("Access-Control-Allow-Credentials", "true");
 //       res.setHeader('Access-Control-Allow-Origin': '*');
    const colors = {'result': 'Please enter your passcode.'};
        res.end(JSON.stringify(colors));
    }
    else{
    let rawdata = fs.readFileSync('./grammar2Task.json');
    let data = JSON.parse(rawdata);
    var gramarName = ""
    var taskName = ""
    for (let i = 0; i < data.length; i++){
        var obj = data[i];
        if (obj.Id == grammarSelected){
            gramarName = obj.Name;
            taskName = obj.Task[taskSelected];
            break
        }
    }
    const d = new Date();
    let now = d.getTime();
    // let now = Date.now();
    let fileName = passcode + "_" + now + ".json";
    console.log(fileName)
    jsonData = {"Timestamp": new Date(now).toString(), "Passcode": passcode, "Grammar Id": grammarSelected, "Grammar": gramarName, "Task Id": taskSelected, "Task": taskName, "Solution": solutionSelected, "Feedback": feedbackSelected}

    fs.writeFile('./submissions/'+fileName, JSON.stringify(jsonData), function (err,data) {
        if (err) {
            return console.log(err);
        }
        console.log(data);
    }
    );
    //res.sendFile(path.join(__dirname+'build/index.html'));
    //res.send("Hello World");
    res.setHeader('Content-Type', 'application/json');
    // res.setHeader("Access-Control-Allow-Origin", "*");
    // res.setHeader("Access-Control-Allow-Origin", "cyclops.cse.iitk.ac.in");
    res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE");
    res.setHeader("Access-Control-Max-Age", "3600");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Origin, Cache-Control, X-Requested-With");
    res.setHeader("Access-Control-Allow-Credentials", "true");
 //       res.setHeader('Access-Control-Allow-Origin': '*');
    const colors = {'result': 'Your response is successfully submitted.'};
        res.end(JSON.stringify(colors));
}
}

    );

//app.get('*', (req,res) => {
//   res.sendFile(path.join(__dirname+'build/index.html'));
//});

app.listen(port, () => console.log(`Listening on port ${port}`));
